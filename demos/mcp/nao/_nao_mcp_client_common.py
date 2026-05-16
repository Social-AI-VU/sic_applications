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
from sic_framework.mcp.nao import print_mcp_stdio_spawn_help

# Spoken via MCP say_text once the server session is up (stub mode logs only).
READY_ANNOUNCEMENT = "I'm ready when you are!"

__all__ = [
    "NaoMcpSICApplication",
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
    # Only print new assistant/tool lines since the last turn (skip echoed user text).
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

    def exit_handler(self, signum=None, frame=None) -> None:
        self.shutdown_event.set()

    def _interrupt(self) -> None:
        self._sigint_count += 1
        self.shutdown_event.set()
        if self._sigint_count >= 2:
            os._exit(130)
        self.logger.info("Stopping... (Ctrl+C again to force quit)")

    def _cleanup(self) -> None:
        # Client never owns NAO hardware; the stdio MCP subprocess shuts down in its own finally.
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
        # Route Ctrl+C through shutdown_event instead of SIC's sys.exit-based handlers.
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
                    # Voice demo drives listen_for_speech itself; the agent must not block on mic.
                    tools = [t for t in tools if t.name not in exclude_mcp_tools]
                agent = create_agent(
                    model,
                    tools,
                    system_prompt=system_prompt,
                    checkpointer=InMemorySaver(),
                )
                session_started = True
                await self._announce_ready(session)
                # Subclasses implement chat REPL or voice listen loop against this session.
                await self._async_mcp_loop(
                    agent, thread_id=thread_id, mcp_session=session
                )
        except (KeyboardInterrupt, asyncio.CancelledError):
            self.shutdown_event.set()
            return
        except SystemExit:
            raise
        except BaseException as exc:
            # After a session starts, connection errors are logged in-loop; only pre-connect gets hints.
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
            # Always tear down SIC client state even when asyncio exits via Ctrl+C.
            self._cleanup()

    async def _async_run(self) -> None:
        raise NotImplementedError
