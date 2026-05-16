"""
Shared MCP demo base (asyncio SICApplication) and LangChain message printing.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from sic_framework.core.sic_application import SICApplication
from sic_framework.mcp.nao import (
    print_mcp_sse_connection_help,
    print_mcp_stdio_spawn_help,
)

__all__ = [
    "NaoMcpSICApplication",
    "format_message",
    "print_delta",
    "print_mcp_sse_connection_help",
    "print_mcp_stdio_spawn_help",
]


def format_message(m: BaseMessage) -> str:
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


def print_delta(messages: list[BaseMessage], start: int) -> None:
    for m in messages[start:]:
        if isinstance(m, HumanMessage):
            continue
        line = format_message(m)
        if line.strip():
            print(line)


class NaoMcpSICApplication(SICApplication):
    """
    SICApplication base for asyncio MCP clients.

    Skips SIC's SIGINT/atexit handlers (they call sys.exit and break stdio MCP).
    Ctrl+C sets shutdown_event via asyncio; run() always cleans up in finally.
    """

    def register_exit_handler(self) -> None:
        """Do not register handlers that sys.exit during asyncio.run."""
        self._shutdown_handler_registered = True

    def _interrupt(self) -> None:
        self._sigint_count += 1
        self.shutdown_event.set()
        if self._sigint_count >= 2:
            os._exit(130)
        self.logger.info("Stopping... (Ctrl+C again to force quit)")

    def _cleanup(self) -> None:
        self.cleanup_resources(log_shutdown=False)

    async def _run_mcp_agent_session(
        self,
        *,
        model: str,
        mcp_connections: dict[str, dict[str, Any]],
        system_prompt: str,
        thread_id: str,
    ) -> Any:
        from langchain.agents import create_agent
        from langchain_mcp_adapters.client import MultiServerMCPClient
        from langchain_mcp_adapters.tools import load_mcp_tools
        from langgraph.checkpoint.memory import InMemorySaver

        mcp = MultiServerMCPClient(mcp_connections)
        if len(mcp_connections) != 1:
            raise ValueError("expected exactly one MCP server in mcp_connections")
        server_name = next(iter(mcp_connections))
        loop = asyncio.get_running_loop()
        try:
            loop.add_signal_handler(signal.SIGINT, self._interrupt)
            loop.add_signal_handler(signal.SIGTERM, self._interrupt)
        except (NotImplementedError, RuntimeError):
            pass

        session_started = False
        try:
            async with mcp.session(server_name) as session:
                tools = await load_mcp_tools(
                    session,
                    callbacks=mcp.callbacks,
                    server_name=server_name,
                    tool_interceptors=mcp.tool_interceptors,
                    tool_name_prefix=mcp.tool_name_prefix,
                )
                agent = create_agent(
                    model,
                    tools,
                    system_prompt=system_prompt,
                    checkpointer=InMemorySaver(),
                )
                session_started = True
                await self._async_mcp_loop(agent, thread_id=thread_id)
        except (KeyboardInterrupt, asyncio.CancelledError):
            self.shutdown_event.set()
            return
        except SystemExit:
            raise
        except BaseException as exc:
            if self.shutdown_event.is_set() or session_started:
                return
            self._handle_mcp_connect_error(exc)
            raise SystemExit(1) from exc

    def _handle_mcp_connect_error(self, exc: BaseException) -> None:
        raise NotImplementedError

    async def _async_mcp_loop(self, agent: Any, *, thread_id: str) -> None:
        raise NotImplementedError

    def run(self) -> None:
        self._sigint_count = 0
        self._cleanup_in_progress = False
        try:
            asyncio.run(self._async_run())
        finally:
            self._cleanup()

    async def _async_run(self) -> None:
        raise NotImplementedError
