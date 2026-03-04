import os
import threading
import time
import urllib.request
import webbrowser
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.core.utils import is_sic_instance
from sic_framework.services.webserver.webserver_service import (
    ButtonClicked,
    TranscriptMessage,
    WebInfoMessage,
    Webserver,
    WebserverConf,
)


# LangChain imports for v1.2.x agent API
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

# Tavily web search client
from tavily import TavilyClient  # type: ignore


@tool
def weather_lookup(location: str) -> str:
    """
    Useful for answering questions about the current weather in a given city or location.
    Input should be a plain-text location such as "Amsterdam", "New York", or "Tokyo, Japan".
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return (
            "Weather tool is not configured. "
            "Set OPENWEATHER_API_KEY in sic_applications/conf/.env "
            "and ensure web_agent.py loads it with python-dotenv."
        )

    params = {
        "q": location,
        "appid": api_key,
        "units": "metric",
    }

    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params=params,
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        body = ""
        try:
            body = e.response.text[:300] if e.response is not None else ""
        except Exception:
            body = ""
        return (
            f"DEBUG: OpenWeatherMap HTTP error while fetching weather for '{location}'. "
            f"status={status}, body_snippet={body!r}. "
            "This usually means the API key is invalid, expired, or the request parameters are wrong."
        )
    except Exception as e:
        return (
            f"DEBUG: Unexpected error while fetching weather for '{location}': {e!r}. "
            "Check network connectivity and your OPENWEATHER_API_KEY configuration."
        )

    name = data.get("name", location)
    main = data.get("weather", [{}])[0].get("description", "unknown conditions")
    temp = data.get("main", {}).get("temp")
    feels_like = data.get("main", {}).get("feels_like")

    pieces = [f"Weather for {name}: {main}"]
    if temp is not None:
        pieces.append(f"temperature {temp:.1f}°C")
    if feels_like is not None:
        pieces.append(f"feels like {feels_like:.1f}°C")

    return ", ".join(pieces)


@tool
def web_search(query: str) -> str:
    """
    Useful for searching the web for up-to-date information, news, or facts.
    Input should be a natural language search query.
    """
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        client = TavilyClient(api_key=api_key) if api_key else TavilyClient()
        results = client.search(query=query)
        return str(results)
    except Exception as e:
        return (
            f"DEBUG: Tavily web search failed for query {query!r}: {e!r}. "
            "Verify that TAVILY_API_KEY is set (if required) and that the network is reachable."
        )


class WebAgentApplication(SICApplication):
    """
    LangChain-powered web agent that:

    - handles natural language weather questions,
    - performs web search for arbitrary queries,
    - returns answers via the SIC webserver UI.
    """

    def __init__(self):
        super(WebAgentApplication, self).__init__()

        self.set_log_level(sic_logging.DEBUG)

        self.web_port: int = 8080
        self.webserver: Optional[Webserver] = None
        self.agent = None

        self._agent_lock = threading.Lock()
        # In-memory conversation history shared across turns.
        self._conversation_messages: list[Any] = []

        # Load API keys and other secrets from sic_applications/conf/.env
        # so that ChatOpenAI, TavilyClient, and weather API all see them.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(current_dir, "..", "..", "..", "conf", ".env")
        load_dotenv(env_path)

        self.setup()

    def _build_agent(self):
        """
        Construct the LangChain agent with weather + web search tools
        using the newer `create_agent` API.
        """
        # LLM configuration: relies on OPENAI_API_KEY or compatible env configuration.
        llm = ChatOpenAI(temperature=0)

        tools = [weather_lookup, web_search]

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=(
                "You are a helpful assistant that can answer questions about the weather "
                "and general web queries. Use the provided tools whenever they are helpful "
                "to answer up-to-date or location-specific questions."
            ),
        )
        return agent

    # ------------------------------------------------------------------
    # SIC + Webserver setup
    # ------------------------------------------------------------------
    def setup(self):
        """
        Start the SIC webserver and construct the LangChain agent.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        webfiles_dir = os.path.join(current_dir, "webfiles")

        web_conf = WebserverConf(
            host="0.0.0.0",
            port=self.web_port,
            templates_dir=webfiles_dir,
            static_dir=webfiles_dir,
        )

        self.webserver = Webserver(conf=web_conf)
        self.webserver.register_callback(self.on_web_event)

        with self._agent_lock:
            self.agent = self._build_agent()

        url = f"http://localhost:{self.web_port}"
        threading.Thread(target=lambda: self._open_when_ready(url), daemon=True).start()
        self.logger.info("Web agent UI available at %s", url)

    def _open_when_ready(self, url: str) -> None:
        """
        Open the browser once the webserver's /readyz endpoint reports healthy.
        """
        ready_url = url.rstrip("/") + "/readyz"
        deadline = time.time() + 10.0
        while time.time() < deadline and not self.shutdown_event.is_set():
            try:
                with urllib.request.urlopen(ready_url, timeout=0.5) as resp:
                    if resp.status == 200:
                        webbrowser.open(url, new=2)
                        return
            except Exception:
                pass
            time.sleep(0.1)
        webbrowser.open(url, new=2)

    # ------------------------------------------------------------------
    # Web callbacks
    # ------------------------------------------------------------------
    def on_web_event(self, message: Any) -> None:
        """
        Handle button click events from the web UI.

        Expects a payload of the form:
          {"type": "query", "text": "<user question>"}
        """
        if not is_sic_instance(message, ButtonClicked):
            return

        payload = message.button
        if not isinstance(payload, Dict):
            return

        event_type = str(payload.get("type", "")).strip().lower()
        if event_type != "query":
            return

        user_query = str(payload.get("text", "")).strip()
        if not user_query:
            return

        self.logger.info("Received user query from web UI: %s", user_query)

        # Publish the user's query to the transcript area in the web UI.
        try:
            if self.webserver:
                self.webserver.send_message(TranscriptMessage(transcript=user_query))
        except Exception as e:
            self.logger.warning("Failed to send transcript to web UI: %s", e)

        # Run the agent in a worker thread to avoid blocking the Socket.IO handler.
        threading.Thread(
            target=self._run_agent_and_publish,
            args=(user_query,),
            daemon=True,
        ).start()

    def _run_agent_and_publish(self, user_query: str) -> None:
        """
        Execute the LangChain agent for the given query and publish its answer.
        """
        try:
            with self._agent_lock:
                if self.agent is None:
                    self.agent = self._build_agent()

                # Append the new user message to the in-memory conversation and send the full history 
                # into the agent so that it can answer follow-up questions like "Why not?" with context.
                self._conversation_messages.append(HumanMessage(content=user_query))
                state = self.agent.invoke({"messages": list(self._conversation_messages)})
        except Exception as e:
            self.logger.error("Agent execution failed: %s", e)
            display_text = (
                "DEBUG: LangChain agent execution failed. "
                f"Internal error: {e!r}. Check the server logs for a full traceback."
            )
        else:
            # `state` is an AgentState dict with a `messages` list; take the last AI message.
            try:
                messages = state.get("messages") or []
                # Keep the latest full conversation so that subsequent turns have context.
                self._conversation_messages = list(messages)

                last = messages[-1] if messages else None
                content = getattr(last, "content", None)
                if isinstance(content, list):
                    parts = []
                    for part in content:
                        if isinstance(part, dict) and "text" in part:
                            parts.append(str(part["text"]))
                        else:
                            parts.append(str(part))
                    display_text = "\n".join(parts).strip()
                else:
                    display_text = str(content or "").strip()
                if not display_text:
                    display_text = "(agent returned an empty response)"
            except Exception as e:
                self.logger.error("Failed to parse agent state: %s", e)
                display_text = (
                    "DEBUG: Agent finished but response could not be parsed. "
                    f"Internal error: {e!r}. Inspect the backend logs for details."
                )
        try:
            if self.webserver:
                self.webserver.send_message(WebInfoMessage("agent_response", str(display_text)))
        except Exception as e:
            self.logger.warning("Failed to send agent response to web UI: %s", e)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """
        Keep the application alive while the webserver and agent run.
        """
        self.logger.info("Starting LangChain web agent application.")
        try:
            while not self.shutdown_event.is_set():
                time.sleep(0.25)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()


if __name__ == "__main__":
    app = WebAgentApplication()
    app.run()