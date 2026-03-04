import json
import time
from os.path import abspath, join
from typing import Any, Optional

from dotenv import load_dotenv

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_motion import (
    NaoPostureRequest,
    NaoqiAnimationRequest,
)
from sic_framework.devices.nao import NaoqiTextToSpeechRequest
from sic_framework.services.google_stt.google_stt import (
    GetStatementRequest,
    GoogleSpeechToText,
    GoogleSpeechToTextConf,
)

# LangChain imports (v1.2.x agent API)
from langchain_openai import ChatOpenAI  # type: ignore
from langchain.tools import tool  # type: ignore
from langchain.agents import create_agent  # type: ignore
from langchain_core.messages import HumanMessage  # type: ignore


class NaoVoiceCommandAgent(SICApplication):
    """
    NAO voice command demo powered by LangChain tools.

    - Listens continuously to the user's voice via Google Speech-to-Text.
    - Sends each transcript to a LangChain agent.
    - The agent decides which gesture/tool best matches the user's command.
    - If no tool matches, NAO says:
        "I'm sorry, but I lack the proper tools to perform that action".

    IMPORTANT:
    - Set `self.nao_ip` in `__init__` to your NAO's IP address.
    - Google STT service must be running:
        - pip install --upgrade "social-interaction-cloud[google-stt]"
        - run-google-stt
    - Google credentials must be available at `conf/google/google-key.json`.
    - OpenAI API key must be set (e.g. in `sic_applications/conf/.env`).
    """

    def __init__(self):
        super(NaoVoiceCommandAgent, self).__init__()

        # Replace with your NAO's IP address.
        self.nao_ip: str = "192.168.101.9"

        self.nao: Optional[Nao] = None
        self.stt: Optional[GoogleSpeechToText] = None

        # LangChain agent + conversation state.
        self.agent = None
        self._conversation_messages: list[Any] = []

        self.set_log_level(sic_logging.INFO)

        # Load environment variables (OPENAI_API_KEY, etc.).
        load_dotenv(abspath(join("..", "..", "conf", ".env")))

        self.setup()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def setup(self) -> None:
        """Initialize NAO and Google STT, then build the LangChain agent."""
        self.logger.info("Initializing NAO robot at %s ...", self.nao_ip)
        self.nao = Nao(ip=self.nao_ip, dev_test=True)

        self.logger.info("Setting up Google Speech-to-Text service.")
        google_keyfile_path = abspath(join("..", "..", "conf", "google", "google-key.json"))
        with open(google_keyfile_path) as f:
            keyfile_json = json.load(f)

        stt_conf = GoogleSpeechToTextConf(
            keyfile_json=keyfile_json,
            sample_rate_hertz=16000,  # NAO microphone sample rate
            language="en-US",
            interim_results=False,
        )
        self.stt = GoogleSpeechToText(conf=stt_conf, input_source=self.nao.mic)

        self.agent = self._build_agent()
        self._conversation_messages = []

        # Initial spoken introduction.
        try:
            self.nao.tts.request(
                NaoqiTextToSpeechRequest(
                    "Hello, I'm an agent that can control the Nao robot. "
                    "Say commands and I will complete them for you."
                )
            )
        except Exception as e:
            self.logger.error("Failed to speak introduction: %r", e)

        self.logger.info("NaoVoiceCommandAgent setup complete. Listening for voice commands...")

    # ------------------------------------------------------------------
    # LangChain tools and agent
    # ------------------------------------------------------------------
    def _build_agent(self):
        """
        Construct a LangChain agent with tools that control NAO gestures.

        The agent:
        - Receives natural language commands (transcripts).
        - Picks the gesture tool that best matches the command.
        - If no gesture is appropriate, replies with a fixed fallback phrase.
        """

        @tool
        def wave() -> str:
            """
            Make NAO wave hello with its arm.

            Use this for commands like:
            - "wave"
            - "say hi"
            - "greet me"
            """
            if not self.nao:
                return "DEBUG: wave tool called but NAO is not initialized."
            try:
                self.nao.motion.request(NaoPostureRequest("Stand", 0.5), block=False)
                self.nao.motion.request(
                    NaoqiAnimationRequest("animations/Stand/Gestures/Hey_1"),
                    block=False,
                )
                return "Waving hello."
            except Exception as e:
                self.logger.error("Wave tool failed: %r", e)
                return f"DEBUG: wave tool failed with error: {e!r}"

        @tool
        def nod() -> str:
            """
            Make NAO nod its head up and down.

            Use this for commands like:
            - "nod"
            - "say yes"
            - "agree with me"
            """
            if not self.nao:
                return "DEBUG: nod tool called but NAO is not initialized."
            try:
                self.nao.motion.request(NaoPostureRequest("Stand", 0.5), block=False)
                self.nao.motion.request(
                    NaoqiAnimationRequest("animations/Stand/Gestures/Yes_1"),
                    block=False,
                )
                return "Nodding yes."
            except Exception as e:
                self.logger.error("Nod tool failed: %r", e)
                return f"DEBUG: nod tool failed with error: {e!r}"

        @tool
        def shake_head() -> str:
            """
            Make NAO shake its head left and right (no).

            Use this for commands like:
            - "shake your head"
            - "say no"
            - "disagree"
            """
            if not self.nao:
                return "DEBUG: shake_head tool called but NAO is not initialized."
            try:
                self.nao.motion.request(NaoPostureRequest("Stand", 0.5), block=False)
                self.nao.motion.request(
                    NaoqiAnimationRequest("animations/Stand/Gestures/No_1"),
                    block=False,
                )
                return "Shaking head no."
            except Exception as e:
                self.logger.error("shake_head tool failed: %r", e)
                return f"DEBUG: shake_head tool failed with error: {e!r}"

        @tool
        def sit_down() -> str:
            """
            Make NAO sit down safely.

            Use this for commands like:
            - "sit"
            - "sit down"
            """
            if not self.nao:
                return "DEBUG: sit_down tool called but NAO is not initialized."
            try:
                self.nao.motion.request(NaoPostureRequest("Sit", 0.5), block=False)
                return "Sitting down."
            except Exception as e:
                self.logger.error("sit_down tool failed: %r", e)
                return f"DEBUG: sit_down tool failed with error: {e!r}"

        @tool
        def stand_up() -> str:
            """
            Make NAO stand up.

            Use this for commands like:
            - "stand"
            - "stand up"
            - "get up"
            """
            if not self.nao:
                return "DEBUG: stand_up tool called but NAO is not initialized."
            try:
                self.nao.motion.request(NaoPostureRequest("Stand", 0.5), block=False)
                return "Standing up."
            except Exception as e:
                self.logger.error("stand_up tool failed: %r", e)
                return f"DEBUG: stand_up tool failed with error: {e!r}"

        @tool
        def say_phrase(text: str) -> str:
            """
            Make NAO say a short phrase out loud.

            Use this for commands like:
            - "say hello"
            - "repeat after me: ..."
            - "tell me 'good morning'"
            """
            if not self.nao:
                return "DEBUG: say_phrase tool called but NAO is not initialized."
            cleaned = (text or "").strip()
            if not cleaned:
                return "DEBUG: say_phrase tool received empty text."
            try:
                self.nao.tts.request(NaoqiTextToSpeechRequest(cleaned))
                return f"Spoke the phrase: {cleaned}"
            except Exception as e:
                self.logger.error("say_phrase tool failed: %r", e)
                return f"DEBUG: say_phrase tool failed with error: {e!r}"

        llm = ChatOpenAI(temperature=0)
        tools = [wave, nod, shake_head, sit_down, stand_up, say_phrase]

        # The system prompt explains how to map voice commands to tools and when
        # to fall back with the fixed phrase.
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=(
                "You control a NAO robot and receive user commands as text "
                "transcribed from their speech.\n"
                "- Decide whether the user's command clearly matches one of the "
                "available tools: wave, nod, shake_head, sit_down, stand_up, "
                "or say_phrase.\n"
                "- Only call a tool when it is clearly appropriate for the command.\n"
                "- If no tool is appropriate, call the say_phrase tool and "
                "make NAO say exactly this sentence and nothing else:\n"
                "  \"I'm sorry, but I lack the proper tools to perform that action\".\n"
                "- Keep any other responses short and suitable for spoken dialogue."
            ),
        )
        return agent

    # ------------------------------------------------------------------
    # STT + agent interaction
    # ------------------------------------------------------------------
    def _capture_statement(self) -> str:
        """Capture a single spoken statement using Google STT."""
        if not self.stt:
            self.logger.error("STT service is not initialized.")
            return ""

        self.logger.info("Listening for a spoken command via Google STT...")
        try:
            result = self.stt.request(GetStatementRequest())
        except Exception as e:
            self.logger.error("Google STT request failed: %r", e)
            return ""

        if (
            not result
            or not hasattr(result.response, "alternatives")
            or not result.response.alternatives
        ):
            self.logger.info("No transcript received from Google STT.")
            return ""

        transcript = result.response.alternatives[0].transcript
        return transcript.strip()

    def _run_agent_turn(self, user_text: str) -> str:
        """
        Append a new human message, invoke the LangChain agent, update conversation
        state, and return the latest assistant text.

        The returned text is suitable for speaking via NAO TTS.
        """
        if not self.agent:
            self.logger.error("Agent is not initialized.")
            return ""

        self._conversation_messages.append(HumanMessage(content=user_text))
        try:
            state = self.agent.invoke({"messages": list(self._conversation_messages)})
        except Exception as e:
            self.logger.error("Agent invocation failed: %r", e)
            return (
                "DEBUG: LangChain agent failed to respond. "
                f"Internal error: {e!r}. Check backend logs for details."
            )

        try:
            messages = state.get("messages") or []
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
                text = "\n".join(parts).strip()
            else:
                text = str(content or "").strip()
            if not text:
                text = "(agent returned an empty response)"
            return text
        except Exception as e:
            self.logger.error("Failed to parse agent state: %r", e)
            return (
                "DEBUG: Agent finished but response could not be parsed. "
                f"Internal error: {e!r}."
            )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Main application loop: listen for commands and let the agent act."""
        self.logger.info("Starting NaoVoiceCommandAgent main loop.")
        try:
            while not self.shutdown_event.is_set():
                transcript = self._capture_statement()
                if not transcript:
                    # No speech detected; loop again.
                    time.sleep(0.1)
                    continue

                self.logger.info("User command: %s", transcript)
                reply_text = self._run_agent_turn(transcript)


                if reply_text:
                    self.logger.info("Agent reply: %s", reply_text)

                # Small pause between turns.
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user.")
        finally:
            self.shutdown()


if __name__ == "__main__":
    app = NaoVoiceCommandAgent()
    app.run()
