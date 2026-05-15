"""
NAO microphone → Google STT → LangGraph agent → NAO MCP tools.

This is a **SICApplication**: it uses ``Nao`` + ``GoogleSpeechToText`` on the robot mic
(see ``demo_desktop_google_stt.py``), then sends each final transcript to a **LangGraph**
agent that calls tools on the **NAO MCP server**.

**By default** the MCP server is **not** started manually: this client **spawns**
``python -m sic_framework.mcp.mcp_nao_server`` as a subprocess and talks **stdio** MCP
(one persistent ``ClientSession`` for the whole voice loop).

**Important:** that subprocess is a **second SIC client** that also instantiates ``Nao``
for MCP tools. This client sets ``SIC_NAO_REUSE_REMOTE_SIC=1`` on the subprocess so it
**does not SSH-pkill** the robot wrapper when remote SIC is already up (same symptom as
before: mic/STT break, duplicate ``NaoComponentManager`` lines, Google ``409``). Prefer
``--mcp-url`` for MCP on another host, or ``--mcp-server-stub`` while iterating on
voice-only behavior.

**Logs:** ``[NaoComponentManager <robot-ip>]`` (and similar remote tags) are emitted by
the **robot's** SIC process and forwarded over Redis; if two local processes are
connected, you may see the **same** remote line **twice** — that is not necessarily two
robots, only two subscribers printing one event.

**``tools/list`` (ListToolsRequest):** ``langchain_mcp_adapters.load_mcp_tools`` already
calls ``session.list_tools()`` (again for each pagination cursor if the server paginates).
An extra explicit ``list_tools()`` before it only added a redundant round-trip.

**Ctrl+C:** Stops the voice loop cleanly (SIC's default handler is disabled for this demo).
Restart the voice client after updating the MCP server so catalog changes load.

Optional: pass ``--mcp-url`` (or set ``NAO_MCP_URL``) to use a **remote** server over
SSE / streamable HTTP instead (e.g. ``run-nao-mcp --transport sse`` in another terminal).

Prerequisites
-------------
1. ``pip install -e '.[nao-mcp-agent]' 'social-interaction-cloud[nao-mcp,google-stt]'``
2. Start Google STT service: ``run-google-stt``
3. ``sic_applications/conf/.env`` — at least ``OPENAI_API_KEY`` (for the default model).
4. Google key JSON: default ``sic_applications/conf/google/google-key.json``
5. Real NAO on the network (microphone runs over SIC to the robot).

Run from ``sic_applications``::

    python demos/mcp/nao_mcp_voice_client.py --robot-ip 10.0.0.50

Remote MCP example::

    export NAO_MCP_URL=http://127.0.0.1:8000/sse
    python demos/mcp/nao_mcp_voice_client.py --robot-ip 10.0.0.50
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import sys
import time
from os.path import abspath, join
from pathlib import Path
from typing import Any, Literal

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.devices import Nao
from sic_framework.services.google_stt.google_stt import (
    GetStatementRequest,
    GoogleSpeechToText,
    GoogleSpeechToTextConf,
)

MCP_SERVER_MODULE = "sic_framework.mcp.mcp_nao_server"
McpHttpTransport = Literal["sse", "streamable_http"]


def _sic_applications_conf_dotenv_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "conf" / ".env"


def _load_sic_applications_conf_dotenv() -> Path:
    path = _sic_applications_conf_dotenv_path()
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        print(
            "Missing python-dotenv. Install: pip install -e '.[nao-mcp-agent]'\n",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    load_dotenv(path, override=False)
    return path


def _default_mcp_url(transport: McpHttpTransport) -> str:
    if transport == "sse":
        return "http://127.0.0.1:8000/sse"
    return "http://127.0.0.1:8000/mcp"


def _mcp_http_connection(
    *,
    transport: McpHttpTransport,
    url: str,
) -> dict[str, dict[str, Any]]:
    if transport == "sse":
        return {"nao": {"transport": "sse", "url": url}}
    return {"nao": {"transport": "streamable_http", "url": url}}


def _mcp_stdio_connection(
    *,
    robot_ip: str | None,
    server_stub: bool,
    extra_server_args: list[str],
) -> dict[str, dict[str, Any]]:
    server_args = ["-m", MCP_SERVER_MODULE]
    if server_stub:
        server_args.append("--stub")
    if robot_ip and robot_ip.strip():
        server_args.extend(["--robot-ip", robot_ip.strip()])
    server_args.extend(extra_server_args)
    return {
        "nao": {
            "transport": "stdio",
            "command": sys.executable,
            "args": server_args,
            "env": {
                **os.environ,
                # Avoid second ``Nao()`` in mcp_nao_server from killing remote SIC / mic.
                "SIC_NAO_REUSE_REMOTE_SIC": "1",
            },
        }
    }


def _format_connect_error(exc: BaseException) -> str:
    if isinstance(exc, BaseExceptionGroup):
        inner = "; ".join(f"{type(e).__name__}: {e}" for e in exc.exceptions)
        return f"{type(exc).__name__} ({inner})"
    return f"{type(exc).__name__}: {exc}"


def _print_mcp_remote_connection_help(
    *,
    url: str,
    transport: McpHttpTransport,
    exc: BaseException,
) -> None:
    print(
        f"Could not connect to the remote NAO MCP server ({transport} {url}).\n"
        f"Reason: {_format_connect_error(exc)}\n",
        file=sys.stderr,
    )
    print(
        "Start ``run-nao-mcp --transport sse`` (or streamable-http) in another terminal, "
        "then retry — or omit --mcp-url to use the default stdio subprocess.\n",
        file=sys.stderr,
    )


def _print_mcp_stdio_spawn_help(exc: BaseException) -> None:
    print(
        "Could not start or talk to the NAO MCP server subprocess (stdio).\n"
        f"Reason: {_format_connect_error(exc)}\n",
        file=sys.stderr,
    )
    print(
        "Check that ``social-interaction-cloud`` is installed and importable, e.g.\n"
        f"  {sys.executable} -m {MCP_SERVER_MODULE} --help\n",
        file=sys.stderr,
    )


def _format_message(m: BaseMessage) -> str:
    if isinstance(m, HumanMessage):
        role = "User"
    elif isinstance(m, AIMessage):
        role = "Assistant"
    elif isinstance(m, ToolMessage):
        role = f"Tool({m.name})"
    else:
        role = type(m).__name__
    content = m.content
    if isinstance(content, list):
        text = str(content)
    else:
        text = str(content) if content else ""
    extra = ""
    if isinstance(m, AIMessage) and m.tool_calls:
        extra = f" tool_calls={m.tool_calls!r}"
    return f"{role}: {text}{extra}"


def _print_delta(messages: list[BaseMessage], start: int) -> None:
    for m in messages[start:]:
        if isinstance(m, HumanMessage):
            continue
        line = _format_message(m)
        if line.strip():
            print(line)


class NaoMcpVoiceDemo(SICApplication):
    """
    SIC app: NAO mic → Google STT → text commands → MCP-backed LangGraph agent.
    """

    MIC_SAMPLE_RATE_HZ = 16000
    # Bounded listen window: avoids blocking the STT request thread indefinitely and
    # keeps Redis mic traffic from piling up when Google never returns a final result.
    LISTEN_STREAM_TIMEOUT_S = 20.0
    LISTEN_REQUEST_TIMEOUT_S = 28.0

    def __init__(
        self,
        *,
        robot_ip: str,
        google_keyfile_path: str,
        model: str,
        mcp_connections: dict[str, dict[str, Any]],
        mcp_remote: bool,
        mcp_remote_url: str | None,
        mcp_remote_transport: McpHttpTransport | None,
        thread_id: str,
        language: str,
    ):
        super(NaoMcpVoiceDemo, self).__init__()
        self.robot_ip = robot_ip
        self.google_keyfile_path = google_keyfile_path
        self.model = model
        self.mcp_connections = mcp_connections
        self.mcp_remote = mcp_remote
        self.mcp_remote_url = mcp_remote_url
        self.mcp_remote_transport = mcp_remote_transport
        self.thread_id = thread_id
        self.language = language

        self.nao: Nao | None = None
        self.stt: GoogleSpeechToText | None = None
        self._voice_run_active = False
        self._sigint_count = 0

        self.set_log_level(sic_logging.INFO)
        self.load_env(join("..", "..", "conf", ".env"))
        self.setup()

    @staticmethod
    def _extract_transcript(result_message: Any) -> str | None:
        if not result_message or not hasattr(result_message, "response"):
            return None
        response = result_message.response
        if isinstance(response, dict):
            return None
        if hasattr(response, "alternatives") and response.alternatives:
            return response.alternatives[0].transcript
        if hasattr(response, "results") and response.results:
            first_result = response.results[0]
            if hasattr(first_result, "alternatives") and first_result.alternatives:
                return first_result.alternatives[0].transcript
        return None

    def setup(self) -> None:
        self.logger.info("Connecting to NAO at %s", self.robot_ip)
        self.nao = Nao(ip=self.robot_ip)

        with open(self.google_keyfile_path, encoding="utf-8") as f:
            key_json = json.load(f)

        stt_conf = GoogleSpeechToTextConf(
            keyfile_json=key_json,
            sample_rate_hertz=self.MIC_SAMPLE_RATE_HZ,
            language=self.language,
            interim_results=False,
            timeout=self.LISTEN_STREAM_TIMEOUT_S,
        )
        self.stt = GoogleSpeechToText(conf=stt_conf, input_source=self.nao.mic)
        self.logger.info("Google STT bound to NAO microphone (%s Hz).", self.MIC_SAMPLE_RATE_HZ)

    def register_exit_handler(self) -> None:
        """Skip SIC's atexit/SIGINT registration; :meth:`run` manages shutdown."""
        self._shutdown_handler_registered = True

    def shutdown(self) -> None:
        if self._voice_run_active:
            self.shutdown_event.set()
            return
        self._stop_sic(exit_process=True)

    def exit_handler(self, signum=None, frame=None) -> None:
        if self._voice_run_active:
            return
        self._stop_sic(exit_process=True)

    def _request_stop(self) -> None:
        self._sigint_count += 1
        self.shutdown_event.set()
        if self._sigint_count >= 2:
            os._exit(130)
        self.logger.info("Stopping… (Ctrl+C again to force quit)")

    def _stop_sic(self, *, exit_process: bool) -> None:
        if getattr(self, "_cleanup_in_progress", False):
            return
        self._cleanup_in_progress = True
        self.shutdown_event.set()
        for device in list(self._active_devices):
            try:
                for connector in device.connectors.values():
                    connector.stop_component()
                device.stop_device()
            except Exception as exc:
                self.logger.error("Error stopping device %s: %s", device.name, exc)
        for connector in [
            c for c in self._active_connectors if not getattr(c, "_stopped", False)
        ]:
            try:
                connector.stop_component()
            except Exception as exc:
                self.logger.warning("Error stopping component: %s", exc)
        sic_logging.SIC_CLIENT_LOG.stop()
        if self._redis is not None:
            self._redis.close()
            self._redis = None
        if exit_process:
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)

    def _listen_once_sync(self) -> str | None:
        assert self.stt is not None
        self.check_health()
        return self._extract_transcript(
            self.stt.request(
                GetStatementRequest(),
                timeout=self.LISTEN_REQUEST_TIMEOUT_S,
            )
        )

    async def _listen_once(self) -> str | None:
        if self.shutdown_event.is_set():
            return None
        try:
            return await asyncio.to_thread(self._listen_once_sync)
        except TimeoutError:
            self.logger.warning(
                "Listen timed out after %.0fs; retrying.",
                self.LISTEN_REQUEST_TIMEOUT_S,
            )
            await asyncio.sleep(0.3)
            return None
        except Exception as exc:
            self.logger.error("Listen failed: %s", exc)
            await asyncio.sleep(0.3)
            return None

    async def _async_voice_mcp_loop(self, agent: Any) -> None:
        thread_config: dict[str, Any] = {"configurable": {"thread_id": self.thread_id}}
        prior_len = 0

        mode = "remote MCP URL" if self.mcp_remote else "stdio MCP subprocess"
        print(
            f"MCP: {mode}. Listening on the NAO mic (Google STT). "
            "Speak a command; Ctrl+C to stop.\n"
        )
        # Start the next listen as soon as the agent finishes (not at the top of the
        # next loop) so Google STT is already streaming when the user replies.
        listen_task: asyncio.Task[str | None] | None = asyncio.create_task(
            self._listen_once()
        )
        while not self.shutdown_event.is_set():
            assert listen_task is not None
            transcript = await listen_task
            listen_task = None
            if self.shutdown_event.is_set():
                break
            if not (transcript and transcript.strip()):
                listen_task = asyncio.create_task(self._listen_once())
                continue
            print(f"\n[heard] {transcript.strip()}")
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=transcript.strip())]},
                thread_config,
            )
            messages = result.get("messages", [])
            _print_delta(messages, prior_len)
            prior_len = len(messages)
            listen_task = asyncio.create_task(self._listen_once())

    async def _async_run_mcp_agent(self) -> None:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        from langchain_mcp_adapters.tools import load_mcp_tools

        mcp = MultiServerMCPClient(self.mcp_connections)
        system_prompt = (
            "You control a SoftBank NAO via MCP tools. "
            "The user's message is speech transcribed from the robot's microphone — "
            "interpret it as a short command and use tools to fulfill it. "
            "Use only the provided tools."
        )

        loop = asyncio.get_running_loop()
        try:
            loop.add_signal_handler(signal.SIGINT, self._request_stop)
            loop.add_signal_handler(signal.SIGTERM, self._request_stop)
        except (NotImplementedError, RuntimeError):
            pass
        try:
            async with mcp.session("nao") as session:
                # ``load_mcp_tools`` already calls ``session.list_tools()`` (paginated).
                tools = await load_mcp_tools(
                    session,
                    callbacks=mcp.callbacks,
                    server_name="nao",
                    tool_interceptors=mcp.tool_interceptors,
                    tool_name_prefix=mcp.tool_name_prefix,
                )
                checkpointer = InMemorySaver()
                agent = create_agent(
                    self.model,
                    tools,
                    system_prompt=system_prompt,
                    checkpointer=checkpointer,
                )
                await self._async_voice_mcp_loop(agent)
        except (KeyboardInterrupt, asyncio.CancelledError):
            return
        except SystemExit:
            raise
        except BaseException as exc:
            if self.shutdown_event.is_set():
                return
            if self.mcp_remote and self.mcp_remote_url and self.mcp_remote_transport:
                _print_mcp_remote_connection_help(
                    url=self.mcp_remote_url,
                    transport=self.mcp_remote_transport,
                    exc=exc,
                )
            else:
                _print_mcp_stdio_spawn_help(exc)
            raise SystemExit(1) from exc

    def run(self) -> None:
        self._voice_run_active = True
        self._sigint_count = 0
        self._cleanup_in_progress = False
        try:
            asyncio.run(self._async_run_mcp_agent())
        finally:
            self._voice_run_active = False
            self._stop_sic(exit_process=False)


def main() -> None:
    env_file = _load_sic_applications_conf_dotenv()

    parser = argparse.ArgumentParser(
        description="NAO mic + Google STT + LangGraph agent calling NAO MCP tools."
    )
    parser.add_argument(
        "--robot-ip",
        type=str,
        default=os.environ.get("ROBOT_IP") or os.environ.get("NAO_IP"),
        help="NAO IP (default: ROBOT_IP or NAO_IP from the environment / .env).",
    )
    parser.add_argument(
        "--google-keyfile",
        type=str,
        default=abspath(join("..", "..", "conf", "google", "google-key.json")),
        help="Path to Google service account JSON for Speech-to-Text.",
    )
    parser.add_argument(
        "--mcp-url",
        type=str,
        default=None,
        help=(
            "If set (or NAO_MCP_URL), connect to a remote MCP server over HTTP instead of "
            "spawning stdio (SSE/streamable-http per --mcp-http-transport)."
        ),
    )
    parser.add_argument(
        "--mcp-http-transport",
        type=str,
        choices=("sse", "streamable_http"),
        default=os.environ.get("NAO_MCP_HTTP_TRANSPORT", "sse"),
        help="When using --mcp-url: HTTP transport (default: sse).",
    )
    parser.add_argument(
        "--mcp-server-stub",
        action="store_true",
        help="When using default stdio MCP: pass --stub to the spawned mcp_nao_server (robot tools stubbed).",
    )
    parser.add_argument(
        "--mcp-server-arg",
        action="append",
        default=[],
        dest="mcp_server_args",
        metavar="ARG",
        help="Extra argv for the spawned MCP server (stdio mode only). Repeatable.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("NAO_MCP_AGENT_MODEL", "openai:gpt-4o-mini"),
    )
    parser.add_argument(
        "--thread-id",
        type=str,
        default="nao-mcp-voice",
        help="LangGraph checkpointer thread id.",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="en-US",
        help="Google STT language code.",
    )
    args = parser.parse_args()

    if not args.robot_ip or not str(args.robot_ip).strip():
        print(
            "Missing NAO IP. Pass --robot-ip or set ROBOT_IP / NAO_IP in the environment "
            f"or in {env_file}.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    robot_ip = args.robot_ip.strip()

    mcp_url = args.mcp_url or os.environ.get("NAO_MCP_URL")
    http_transport: McpHttpTransport = args.mcp_http_transport  # type: ignore[assignment]

    if mcp_url and str(mcp_url).strip():
        mcp_remote = True
        url = str(mcp_url).strip()
        mcp_connections = _mcp_http_connection(transport=http_transport, url=url)
    else:
        mcp_remote = False
        url = None
        mcp_connections = _mcp_stdio_connection(
            robot_ip=robot_ip,
            server_stub=bool(args.mcp_server_stub),
            extra_server_args=list(args.mcp_server_args),
        )

    if args.model.startswith("openai:") and not os.environ.get("OPENAI_API_KEY"):
        print(
            "OPENAI_API_KEY is not set after loading:\n"
            f"  {env_file}\n"
            "Add it for the default OpenAI model, or pass --model for another provider.",
            file=sys.stderr,
        )
        if not env_file.is_file():
            print(f"\nFile does not exist yet: {env_file}\n", file=sys.stderr)
        raise SystemExit(1)

    demo = NaoMcpVoiceDemo(
        robot_ip=robot_ip,
        google_keyfile_path=args.google_keyfile,
        model=args.model,
        mcp_connections=mcp_connections,
        mcp_remote=mcp_remote,
        mcp_remote_url=url,
        mcp_remote_transport=http_transport if mcp_remote else None,
        thread_id=args.thread_id,
        language=args.language,
    )
    demo.run()


if __name__ == "__main__":
    main()
