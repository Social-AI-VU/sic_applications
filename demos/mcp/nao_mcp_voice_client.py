"""
NAO microphone -> Google STT -> LangGraph agent -> NAO MCP tools.

Uses Nao + GoogleSpeechToText on the robot mic, then sends each final transcript to a
LangGraph agent that calls tools on the NAO MCP server (stdio subprocess).

The MCP subprocess is a second SIC client that also instantiates Nao for robot tools.
SIC skips restarting remote SIC when the robot is already pingable and reserved for this
host. Use --mcp-server-stub to test voice without robot tools.

Prerequisites
-------------
1. pip install -e '.[nao-mcp-agent]' 'social-interaction-cloud[nao-mcp,google-stt]'
2. Start Google STT service: run-google-stt
3. sic_applications/conf/.env - at least OPENAI_API_KEY (for the default model).
4. Google key JSON: default sic_applications/conf/google/google-key.json
5. Real NAO on the network (microphone runs over SIC to the robot).

Run from sic_applications::

    python demos/mcp/nao_mcp_voice_client.py --robot-ip 10.0.0.50
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from os.path import abspath, join
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from sic_framework.core import sic_logging
from sic_framework.devices import Nao
from sic_framework.services.google_stt.google_stt import (
    GetStatementRequest,
    GoogleSpeechToText,
    GoogleSpeechToTextConf,
)

from sic_framework.mcp.nao import (
    mcp_stdio_connection,
    nao_mcp_session_log_dir,
    resolve_robot_ip,
)

from _nao_mcp_client_common import (
    NaoMcpSICApplication,
    print_delta,
    print_mcp_stdio_spawn_help,
)


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


class NaoMcpVoiceDemo(NaoMcpSICApplication):
    """SIC app: NAO mic -> Google STT -> text commands -> MCP-backed LangGraph agent."""

    MIC_SAMPLE_RATE_HZ = 16000
    LISTEN_STREAM_TIMEOUT_S = 20.0
    LISTEN_REQUEST_TIMEOUT_S = 28.0

    def __init__(
        self,
        *,
        robot_ip: str,
        google_keyfile_path: str,
        model: str,
        mcp_connections: dict[str, dict[str, Any]],
        thread_id: str,
        language: str,
        log_dir: str,
    ):
        super().__init__()
        self.robot_ip = robot_ip
        self.google_keyfile_path = google_keyfile_path
        self.model = model
        self.mcp_connections = mcp_connections
        self.thread_id = thread_id
        self.language = language

        self.nao: Nao | None = None
        self.stt: GoogleSpeechToText | None = None

        self.set_log_level(sic_logging.DEBUG)
        self.set_log_file_path(log_dir)
        self.load_env(join("..", "..", "conf", ".env"))

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

    def _handle_mcp_connect_error(self, exc: BaseException) -> None:
        print_mcp_stdio_spawn_help(
            exc,
            extra_lines=(
                "  - run-google-stt running for microphone transcription.\n"
                "  - Robot reachable via --robot-ip or --mcp-server-stub on MCP only.\n"
            ),
        )

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

    async def _async_mcp_loop(self, agent: Any, *, thread_id: str) -> None:
        thread_config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
        prior_len = 0

        self.logger.info(
            "MCP stdio subprocess. Listening on the NAO mic (Google STT).\n"
            "Speak a command (silence up to {:.0f}s ends a listen turn). Ctrl+C to stop.\n".format(
                self.LISTEN_STREAM_TIMEOUT_S
            )
        )
        listen_task = asyncio.create_task(self._listen_once())
        while not self.shutdown_event.is_set():
            assert listen_task is not None
            transcript = await listen_task
            listen_task = None
            if self.shutdown_event.is_set():
                break
            if not (transcript and transcript.strip()):
                listen_task = asyncio.create_task(self._listen_once())
                continue
            self.logger.info(f"\n[heard] {transcript.strip()}")
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=transcript.strip())]},
                thread_config,
            )
            messages = result.get("messages", [])
            print_delta(messages, prior_len)
            prior_len = len(messages)
            listen_task = asyncio.create_task(self._listen_once())

    async def _async_run(self) -> None:
        self.logger.info("Connecting to NAO and Google STT...")
        self.setup()
        self.logger.info("Starting MCP agent session...")
        system_prompt = (
            "You control a SoftBank NAO via MCP tools. "
            "The user's message is speech transcribed from the robot's microphone; "
            "interpret it as a short command and use tools to fulfill it. "
            "Use only the provided tools."
        )
        await self._run_mcp_agent_session(
            model=self.model,
            mcp_connections=self.mcp_connections,
            system_prompt=system_prompt,
            thread_id=self.thread_id,
        )


def main() -> None:
    env_file = _load_sic_applications_conf_dotenv()

    parser = argparse.ArgumentParser(
        description="NAO mic + Google STT + LangGraph agent calling NAO MCP tools (stdio)."
    )
    parser.add_argument(
        "--robot-ip",
        type=str,
        default=resolve_robot_ip(),
        help="NAO IP (default: ROBOT_IP or NAO_IP from the environment / .env).",
    )
    parser.add_argument(
        "--google-keyfile",
        type=str,
        default=abspath(join("..", "..", "conf", "google", "google-key.json")),
        help="Path to Google service account JSON for Speech-to-Text.",
    )
    parser.add_argument(
        "--mcp-server-stub",
        action="store_true",
        help="Pass --stub to the spawned mcp_nao_server.",
    )
    parser.add_argument(
        "--mcp-server-arg",
        action="append",
        default=[],
        dest="mcp_server_args",
        metavar="ARG",
        help="Extra argv for the spawned MCP server. Repeatable.",
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
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help=(
            "Directory for SIC file logs (client and stdio MCP server). "
            "Default: sic_applications/logs/mcp."
        ),
    )
    args = parser.parse_args()

    log_dir = (args.log_dir or "").strip() or nao_mcp_session_log_dir(caller_file=__file__)

    if not args.robot_ip or not str(args.robot_ip).strip():
        print(
            "Missing NAO IP. Pass --robot-ip or set ROBOT_IP / NAO_IP in the environment "
            f"or in {env_file}.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    robot_ip = args.robot_ip.strip()

    mcp_connections = mcp_stdio_connection(
        robot_ip=robot_ip,
        server_stub=bool(args.mcp_server_stub),
        extra_server_args=list(args.mcp_server_args),
        log_dir=log_dir,
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
        thread_id=args.thread_id,
        language=args.language,
        log_dir=log_dir,
    )
    demo.run()


if __name__ == "__main__":
    main()
