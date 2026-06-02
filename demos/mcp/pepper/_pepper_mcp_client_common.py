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
from sic_framework.mcp.mcp_server import call_tool_text
from sic_framework.mcp.pepper import print_mcp_stdio_spawn_help

READY_ANNOUNCEMENT = "I'm ready when you are!"

__all__ = [
    "PepperMcpSICApplication",
    "READY_ANNOUNCEMENT",
    "format_message",
    "print_delta",
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


class PepperMcpSICApplication(SICApplication):
    def register_exit_handler(self) -> None:
        self._shutdown_handler_registered = True

    def exit_handler(self, signum=None, frame=None) -> None:
        self.shutdown_event.set()

    def _interrupt(self) -> None:
        self._sigint_count += 1
        self.shutdown_event.set()
        if self._sigint_count >= 2:
            os._exit(130)
        self.logger.info("Stopping... (Ctrl+C again to force quit)")

    def _cleanup(self) -> None:
        self.cleanup_resources(log_shutdown=False)

    async def _announce_ready(self, mcp_session: Any) -> None:
        try:
            result = await mcp_session.call_tool(
                "say_text",
                arguments={"text": READY_ANNOUNCEMENT, "animated": False},
            )
            text = call_tool_text(result)
            if text.startswith("ERROR:"):
                self.logger.warning("Ready announcement failed: %s", text)
        except Exception as exc:
            self.logger.warning("Ready announcement failed: %r", exc)

    async def _run_mcp_agent_session(
        self,
        *,
        model: str,
        mcp_connections: dict[str, dict[str, Any]],
        system_prompt: str,
        thread_id: str,
        exclude_mcp_tools: frozenset[str] = frozenset(),
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
                if exclude_mcp_tools:
                    tools = [t for t in tools if t.name not in exclude_mcp_tools]
                agent = create_agent(
                    model,
                    tools,
                    system_prompt=system_prompt,
                    checkpointer=InMemorySaver(),
                )
                session_started = True
                await self._announce_ready(session)
                await self._async_mcp_loop(
                    agent, thread_id=thread_id, mcp_session=session
                )
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

    async def _async_mcp_loop(
        self, agent: Any, *, thread_id: str, mcp_session: Any = None
    ) -> None:
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
