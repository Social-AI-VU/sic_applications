"""
Keyboard chat -> LangGraph agent -> NAO MCP tools.

SICApplication with a continuous REPL-style session: type a line, the agent calls
tools on the NAO MCP server.

Default (--transport stdio): spawns python -m sic_framework.mcp.nao.nao_mcp_server as a
subprocess (stdio JSON-RPC). Pass --robot-ip or set ROBOT_IP / NAO_IP.

--transport sse: connects to an MCP server already running over HTTP (SSE). Tries
http://127.0.0.1:8000/sse on localhost unless --mcp-url (or NAO_MCP_URL) is set.
If connection fails, the error suggests starting the server or passing --mcp-url.

This demo does not connect to the robot directly in SSE mode; the server owns Nao.

Prerequisites
-------------
1. pip install -e '.[mcp]' in sic_applications (LangChain agent deps).
2. sic_applications/conf/.env with OPENAI_API_KEY (for the default model).

Run from sic_applications::

    python demos/mcp/nao_mcp_chat_client.py --robot-ip 10.0.0.50

    # Server in another terminal:
    run-nao-mcp --transport sse --robot-ip 10.0.0.50
    python demos/mcp/nao_mcp_chat_client.py --transport sse

    python demos/mcp/nao_mcp_chat_client.py --transport sse --mcp-url http://192.168.1.10:8000/sse
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
    DEFAULT_SSE_MCP_URL,
    McpClientTransport,
    mcp_sse_connection,
    mcp_stdio_connection,
    nao_mcp_session_log_dir,
    resolve_robot_ip,
)

from _nao_mcp_client_common import (
    NaoMcpSICApplication,
    print_delta,
    print_mcp_sse_connection_help,
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
            "Missing python-dotenv. Install: pip install -e '.[mcp]'\n",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    load_dotenv(path, override=False)
    return path


async def _read_line(prompt: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: input(prompt))


class NaoMcpChatDemo(NaoMcpSICApplication):
    """SIC app: keyboard chat -> LangGraph agent -> NAO MCP tools."""

    def __init__(
        self,
        *,
        model: str,
        mcp_connections: dict[str, dict[str, Any]],
        mcp_transport: McpClientTransport,
        mcp_url: str | None,
        user_supplied_mcp_url: bool,
        thread_id: str,
        log_dir: str,
    ):
        super().__init__()
        self.model = model
        self.mcp_connections = mcp_connections
        self.mcp_transport = mcp_transport
        self.mcp_url = mcp_url
        self.user_supplied_mcp_url = user_supplied_mcp_url
        self.thread_id = thread_id

        self.set_log_level(sic_logging.INFO)
        self.set_log_file_path(log_dir)
        self.load_env(join("..", "..", "conf", ".env"))

    def _handle_mcp_connect_error(self, exc: BaseException) -> None:
        if self.mcp_transport == "sse":
            print_mcp_sse_connection_help(
                url=self.mcp_url or DEFAULT_SSE_MCP_URL,
                exc=exc,
                user_supplied_url=self.user_supplied_mcp_url,
            )
        else:
            print_mcp_stdio_spawn_help(exc)

    async def _async_mcp_loop(self, agent: Any, *, thread_id: str) -> None:
        thread_config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
        prior_len = 0

        mode = (
            "stdio MCP subprocess"
            if self.mcp_transport == "stdio"
            else "SSE (remote MCP server)"
        )
        print(
            f"MCP chat ({mode}). Type a command and press Enter.\n"
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
            "(stdio subprocess by default, or SSE to an existing server)."
        )
    )
    parser.add_argument(
        "--transport",
        type=str,
        choices=("stdio", "sse"),
        default="stdio",
        help=(
            "MCP transport: stdio spawns mcp_nao_server (default); "
            "sse connects to a server already running over HTTP."
        ),
    )
    parser.add_argument(
        "--robot-ip",
        type=str,
        default=resolve_robot_ip(),
        help="NAO IP for stdio mode (passed to spawned MCP server).",
    )
    parser.add_argument(
        "--mcp-url",
        type=str,
        default=None,
        help=(
            "SSE only: MCP server URL. If omitted, uses NAO_MCP_URL or "
            f"{DEFAULT_SSE_MCP_URL!r} on localhost."
        ),
    )
    parser.add_argument(
        "--mcp-server-stub",
        action="store_true",
        help="Stdio only: pass --stub to the spawned mcp_nao_server.",
    )
    parser.add_argument(
        "--mcp-server-arg",
        action="append",
        default=[],
        dest="mcp_server_args",
        metavar="ARG",
        help="Stdio only: extra argv for the spawned MCP server. Repeatable.",
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

    transport: McpClientTransport = args.transport  # type: ignore[assignment]
    env_mcp_url = (os.environ.get("NAO_MCP_URL") or "").strip()
    user_supplied_mcp_url = bool((args.mcp_url or "").strip()) or bool(env_mcp_url)

    if transport == "stdio":
        robot_ip = (args.robot_ip or "").strip() or None
        mcp_connections = mcp_stdio_connection(
            robot_ip=robot_ip,
            server_stub=bool(args.mcp_server_stub),
            extra_server_args=list(args.mcp_server_args),
            log_dir=log_dir,
        )
        mcp_url = None
        if user_supplied_mcp_url or env_mcp_url:
            print(
                "Note: --mcp-url / NAO_MCP_URL are ignored in stdio mode.\n",
                file=sys.stderr,
            )
    else:
        if user_supplied_mcp_url:
            mcp_url = str(args.mcp_url).strip()
        elif env_mcp_url:
            mcp_url = env_mcp_url
        else:
            mcp_url = DEFAULT_SSE_MCP_URL
        mcp_connections = mcp_sse_connection(url=mcp_url)

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
        mcp_transport=transport,
        mcp_url=mcp_url,
        user_supplied_mcp_url=user_supplied_mcp_url,
        thread_id=args.thread_id,
        log_dir=log_dir,
    )
    demo.run()


if __name__ == "__main__":
    main()
