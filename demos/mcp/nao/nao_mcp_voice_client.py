"""
NAO microphone -> Google STT -> LangGraph agent -> NAO MCP tools.

The client builds a Google STT config dict and passes it to the MCP subprocess
(``SIC_NAO_STT_CONF``). The server owns ``Nao()``, the mic, and STT; this process
calls ``listen_for_speech`` each turn.

Prerequisites: run-google-stt, OPENAI_API_KEY, robot on the network.

Run from sic_applications::

    python demos/mcp/nao_mcp_voice_client.py --robot-ip 10.0.0.50
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import timedelta
from os.path import abspath, join
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from sic_framework.core import sic_logging
from sic_framework.mcp.mcp_server import call_tool_text
from sic_framework.mcp.nao import (
    build_google_stt_conf,
    mcp_stdio_connection,
    nao_mcp_session_log_dir,
    resolve_robot_ip,
)

from _nao_mcp_client_common import (
    NaoMcpSICApplication,
    print_delta,
    print_mcp_stdio_spawn_help,
)

LISTEN_TOOL_NAME = "listen_for_speech"
# Must exceed the server's STT/listen timeout so MCP does not cut off a slow utterance.
LISTEN_MCP_TIMEOUT_S = 30.0

def _sic_applications_conf_dotenv_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent / "conf" / ".env"


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
    """SIC app: MCP listen_for_speech -> LangGraph agent -> NAO MCP action tools."""

    def __init__(
        self,
        *,
        model: str,
        mcp_connections: dict[str, dict[str, Any]],
        thread_id: str,
        log_dir: str,
    ):
        super().__init__()
        self.model = model
        self.mcp_connections = mcp_connections
        self.thread_id = thread_id

        self.set_log_level(sic_logging.DEBUG)
        self.set_log_file_path(log_dir)
        self.load_env(join("..", "..", "..", "conf", ".env"))

    def _handle_mcp_connect_error(self, exc: BaseException) -> None:
        print_mcp_stdio_spawn_help(
            exc,
            extra_lines=(
                "  - run-google-stt must be running.\n"
                "  - Pass --google-keyfile or use the default conf/google/google-key.json.\n"
                "  - Robot reachable via --robot-ip.\n"
            ),
        )

    async def _listen_via_mcp(self, mcp_session: Any) -> str | None:
        # Blocking listen runs in the MCP server process where NAO mic + Google STT live.
        result = await mcp_session.call_tool(
            LISTEN_TOOL_NAME,
            arguments={},
            read_timeout_seconds=timedelta(seconds=LISTEN_MCP_TIMEOUT_S),
        )
        text = call_tool_text(result).strip()
        if text.startswith("ERROR:"):
            self.logger.error("%s", text)
            await asyncio.sleep(0.3)
            return None
        return text or None

    async def _async_mcp_loop(
        self, agent: Any, *, thread_id: str, mcp_session: Any = None
    ) -> None:
        if mcp_session is None:
            raise RuntimeError("voice demo requires an active MCP session")

        thread_config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
        prior_len = 0
        self.logger.info(
            "Listening on the NAO mic (via MCP). Speak a command; Ctrl+C to stop.\n"
        )
        while not self.shutdown_event.is_set():
            transcript = await self._listen_via_mcp(mcp_session)
            if self.shutdown_event.is_set():
                break
            if not (transcript and transcript.strip()):
                # Timeout or silence: poll again without waking the agent.
                continue
            self.logger.info("\n[heard] %s", transcript.strip())
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=transcript.strip())]},
                thread_config,
            )
            messages = result.get("messages", [])
            print_delta(messages, prior_len)
            prior_len = len(messages)

    async def _async_run(self) -> None:
        system_prompt = (
            "You control a SoftBank NAO via MCP tools. "
            "The user's message is speech transcribed from the robot's microphone; "
            "interpret it as a short command and use tools to fulfill it. "
            "Use only the provided tools."
        )
        # Agent gets TTS/LED/motion tools only; this loop owns the microphone.
        await self._run_mcp_agent_session(
            model=self.model,
            mcp_connections=self.mcp_connections,
            system_prompt=system_prompt,
            thread_id=self.thread_id,
            exclude_mcp_tools=frozenset({LISTEN_TOOL_NAME}),
        )


def main() -> None:
    env_file = _load_sic_applications_conf_dotenv()

    parser = argparse.ArgumentParser(
        description="NAO mic + Google STT (MCP server) + LangGraph agent."
    )
    parser.add_argument("--robot-ip", type=str, default=resolve_robot_ip())
    parser.add_argument(
        "--google-keyfile",
        type=str,
        default=abspath(join("..", "..", "..", "conf", "google", "google-key.json")),
    )
    parser.add_argument("--mcp-server-stub", action="store_true")
    parser.add_argument(
        "--mcp-server-arg",
        action="append",
        default=[],
        dest="mcp_server_args",
        metavar="ARG",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("NAO_MCP_AGENT_MODEL", "openai:gpt-4o-mini"),
    )
    parser.add_argument("--thread-id", type=str, default="nao-mcp-voice")
    parser.add_argument("--language", type=str, default="en-US")
    parser.add_argument("--log-dir", type=str, default=None)
    args = parser.parse_args()

    log_dir = (args.log_dir or "").strip() or nao_mcp_session_log_dir(caller_file=__file__)

    if not args.robot_ip or not str(args.robot_ip).strip():
        print("Missing NAO IP (--robot-ip or ROBOT_IP / NAO_IP).", file=sys.stderr)
        raise SystemExit(1)

    robot_ip = args.robot_ip.strip()
    google_keyfile = abspath(args.google_keyfile)
    stt_conf = None
    if not args.mcp_server_stub:
        # STT credentials are serialized into SIC_NAO_STT_CONF for the spawned MCP server.
        if not os.path.isfile(google_keyfile):
            print(f"Google key file not found: {google_keyfile}", file=sys.stderr)
            raise SystemExit(1)
        stt_conf = build_google_stt_conf(
            google_keyfile=google_keyfile,
            language=args.language,
        )

    mcp_connections = mcp_stdio_connection(
        robot_ip=robot_ip,
        server_stub=bool(args.mcp_server_stub),
        extra_server_args=list(args.mcp_server_args),
        log_dir=log_dir,
        stt_conf=stt_conf,
    )

    if args.model.startswith("openai:") and not os.environ.get("OPENAI_API_KEY"):
        print(f"OPENAI_API_KEY not set after loading {env_file}", file=sys.stderr)
        raise SystemExit(1)

    NaoMcpVoiceDemo(
        model=args.model,
        mcp_connections=mcp_connections,
        thread_id=args.thread_id,
        log_dir=log_dir,
    ).run()


if __name__ == "__main__":
    main()
