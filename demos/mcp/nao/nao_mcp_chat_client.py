"""
Keyboard chat -> LangGraph agent -> NAO MCP tools.

Spawns sic_framework.mcp.nao.nao_mcp_server as a stdio subprocess and runs a REPL-style
session: type a line, the agent calls tools on the NAO MCP server.

Pass --robot-ip or set ROBOT_IP / NAO_IP.

Prerequisites
-------------
1. pip install -e '.[mcp]' in sic_applications (LangChain agent deps).
2. sic_applications/conf/.env with OPENAI_API_KEY (for the default model).

Run from sic_applications::

    python demos/mcp/nao_mcp_chat_client.py --robot-ip 10.0.0.50
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from os.path import join
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from sic_framework.core import sic_logging

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
    return Path(__file__).resolve().parent.parent.parent.parent / "conf" / ".env"


def _load_sic_applications_conf_dotenv() -> Path:
    path = _sic_applications_conf_dotenv_path()
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        print(
            "Missing python-dotenv. Install: pip install -e '.[mcp]'\n",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    load_dotenv(path, override=False)
    return path


async def _read_line(prompt: str) -> str:
    # input() blocks the thread pool so the asyncio event loop can still handle Ctrl+C.
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: input(prompt))


class NaoMcpChatDemo(NaoMcpSICApplication):
    """SIC app: keyboard chat -> LangGraph agent -> NAO MCP tools."""

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

        self.set_log_level(sic_logging.INFO)
        self.set_log_file_path(log_dir)
        self.load_env(join("..", "..", "..", "conf", ".env"))

    def _handle_mcp_connect_error(self, exc: BaseException) -> None:
        print_mcp_stdio_spawn_help(exc)

    async def _async_mcp_loop(
        self, agent: Any, *, thread_id: str, mcp_session: Any = None
    ) -> None:
        # InMemorySaver keys conversation turns by thread_id across REPL lines.
        thread_config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
        prior_len = 0

        print(
            "MCP chat (stdio subprocess). Type a command and press Enter.\n"
            "Empty line or Ctrl+C to quit.\n"
        )
        while not self.shutdown_event.is_set():
            try:
                line = await _read_line("You> ")
            except (EOFError, KeyboardInterrupt):
                break
            if self.shutdown_event.is_set():
                break
            if not line.strip():
                break
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=line.strip())]},
                thread_config,
            )
            messages = result.get("messages", [])
            print_delta(messages, prior_len)
            prior_len = len(messages)
            print()

    async def _async_run(self) -> None:
        self.logger.info("Starting MCP agent session...")
        system_prompt = (
            "You control a SoftBank NAO via MCP tools. "
            "The user types commands in a chat session; interpret each message as an "
            "instruction and use tools to fulfill it. Use only the provided tools."
        )
        # No exclude_mcp_tools: chat has no separate listen loop.
        await self._run_mcp_agent_session(
            model=self.model,
            mcp_connections=self.mcp_connections,
            system_prompt=system_prompt,
            thread_id=self.thread_id,
        )


def main() -> None:
    env_file = _load_sic_applications_conf_dotenv()

    parser = argparse.ArgumentParser(
        description=(
            "Keyboard chat with a LangGraph agent that calls NAO MCP tools "
            "(stdio subprocess)."
        )
    )
    parser.add_argument(
        "--robot-ip",
        type=str,
        default=resolve_robot_ip(),
        help="NAO IP (passed to spawned MCP server).",
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
        default="nao-mcp-chat",
        help="LangGraph checkpointer thread id (conversation memory).",
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

    robot_ip = (args.robot_ip or "").strip() or None
    # Spawns sic_framework.mcp.nao.nao_mcp_server; no STT env (keyboard input only).
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

    demo = NaoMcpChatDemo(
        model=args.model,
        mcp_connections=mcp_connections,
        thread_id=args.thread_id,
        log_dir=log_dir,
    )
    demo.run()


if __name__ == "__main__":
    main()
