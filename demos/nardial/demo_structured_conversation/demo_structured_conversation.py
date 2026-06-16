r"""
Nardial Structured Conversation Demo

This demo shows how to use Nardial to conduct a structured conversation with a user.

The conversation is conducted through a series of dialogs, which are defined in the
dialog_configs/structured_conversation_dialogs.json file.

Before running this demo, make sure you have completed the required setup steps.
This demo depends on external services for speech, language understanding, and LLM responses.
-------------------------
1. Install dependencies
-------------------------
    pip install "nardial[google-tts,dialogflow,openai]"
-------------------------
2. Configure credentials
-------------------------
You MUST create the following files:

- Dialogflow / Google credentials: conf/google/google-key.json
- OpenAI API key: conf/.env
Example `.env` file:
    OPENAI_API_KEY="your key"

WARNING: Never commit these files to version control.
-------------------------
3. Start required services
-------------------------
You MUST run these in separate terminals BEFORE starting the demo:

    (MacOs/Linux)
    redis-server conf/redis/redis.conf
    OR
    (Windows)
    .\conf\redis\redis-server.exe .\conf\redis\redis.conf
    run-dialogflow
    run-google-tts
    run-gpt
=========================
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from nardial.conversation_agent import ConversationAgent
from nardial.interaction_orchestrator import InteractionConfig
from nardial.providers.device.desktop import DesktopAdapter
from nardial.providers.llm.openai_gpt import OpenAIGPTProvider
from nardial.providers.nlu.dialogflow import DialogflowNLUProvider
from nardial.providers.tts.google import GoogleTTSConf, GoogleTTSProvider
from nardial.session_manager import SessionManager
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.devices.desktop import Desktop
from sic_framework.services.dialogflow.dialogflow import DialogflowConf

BASE_DIR = Path(__file__).resolve().parent
SIC_APPLICATIONS_DIR = BASE_DIR.parents[2]

GOOGLE_KEYFILE_PATH = SIC_APPLICATIONS_DIR / "conf" / "google" / "google-key.json"
ENV_FILE_PATH = SIC_APPLICATIONS_DIR / "conf" / ".env"

load_dotenv(ENV_FILE_PATH)

if __name__ == "__main__":
    # =========================
    # 1. SELECT DEVICE
    # =========================
    # Choose where the conversation runs:
    # - Desktop: uses your computer's mic + speakers
    # - Pepper: connects to a Pepper robot (requires IP)
    # or any other device of your liking

    desktop = Desktop(
        speakers_conf=SpeakersConf(
            sample_rate=22050  # You can change audio quality (higher = better, but heavier)
        )
    )
    device = DesktopAdapter(desktop)

    # Uncomment to use Pepper instead:
    # from nardial.providers.device.pepper import PepperAdapter
    # from sic_framework.devices import Pepper
    # device = PepperAdapter(Pepper(ip="XXX"))  # Replace with your robot's IP

    # =========================
    # 2. CONFIGURE PROVIDERS
    # =========================
    # Each provider is configured and instantiated separately.
    # This makes it easy to swap out individual components (e.g. switch TTS engine or NLU backend).

    # --- TTS ---
    tts_conf = GoogleTTSConf(
        # speaking_rate=1.0,                        # speech speed (0.25–4.0)
        # google_tts_voice_name="en-US-Neural2-C",  # voice selection
    )
    tts = GoogleTTSProvider(
        conf=tts_conf, device=device, keyfile_path=str(GOOGLE_KEYFILE_PATH)
    )

    # --- NLU ---
    # device.get_mic() returns the SIC microphone component used by Dialogflow for live audio input.
    dialogflow_conf = DialogflowConf(keyfile_json=json.load(open(GOOGLE_KEYFILE_PATH)))
    nlu = DialogflowNLUProvider(conf=dialogflow_conf, mic=device.get_mic())

    # --- LLM (optional) ---
    # Reads OPENAI_API_KEY from the environment (loaded via dotenv above).
    # Pass api_key="..." explicitly if you prefer not to use dotenv.
    llm = OpenAIGPTProvider()

    # --- Behavioral config ---
    interaction_config = InteractionConfig(
        # Change language (affects Dialogflow language context)
        # language="nl",
        # Add a pause after the agent speaks (seconds)
        # post_speech_delay=0.5,
        # Visual/behavior cue while listening (useful for robots)
        # signal_listening_behavior=True,
    )

    # ADVANCED (InteractionConfig fields you can set directly):
    # - animated = True         -> enable speaking gestures (for embodied agents)
    # - always_regenerate = True -> disable TTS audio caching
    # - chunk_audio = True      -> stream audio in chunks (lower latency)
    # - animation_style         -> AnimationStyle.EXPLANATORY or .EXPRESSIVE

    # =========================
    # 3. CREATE AGENT
    # =========================
    # The agent combines device + all providers into a single high-level interface.
    agent = ConversationAgent(
        device=device,
        tts_provider=tts,
        nlu_provider=nlu,
        llm_provider=llm,
        int_config=interaction_config,
    )

    # To enable RAG, pass a vector store:
    # from nardial.providers.vector_store.redis_store import RedisVectorStoreProvider
    # vector_store = RedisVectorStoreProvider(
    #     embedding_model="text-embedding-ada-002",
    #     index_name="my_docs",
    #     ingest_docs=True,       # set True on first run to index your documents
    #     input_path="path/to/docs/",
    # )
    # agent = ConversationAgent(..., vector_store=vector_store)

    # =========================
    # 4. DEFINE SESSION STRUCTURE
    # =========================
    # This determines the flow of the conversation.
    # Each string must match a dialog_id in your JSON file.

    session_agenda = [
        "welcome_and_name",  # greeting + collect user name
        "plan_activity",  # collaborative planning
        "adapt_to_user_energy",  # dynamic behavior based on user state
        "structured_goodbye",  # closing the interaction
    ]

    # You can:
    # - Reorder steps to change flow
    # - Remove items for shorter sessions
    # - Add new dialog_ids from your dialog JSON

    # =========================
    # 5. SESSION MANAGER
    # =========================
    # Handles dialog execution, state tracking, and logging

    session_manager = SessionManager(
        session_agenda=session_agenda,
        agent=agent,
        # Path to your dialog definitions
        dialog_json_path=str(
            BASE_DIR / "dialog_configs" / "structured_conversation_dialogs.json"
        ),
        # Optional: identify the user (used for personalization/memory)
        participant_id="2",
    )

    # Internally, SessionManager:
    # - Loads dialogs from JSON
    # - Filters them based on eligibility (DialogLogic)
    # - Tracks conversation state (topics, completed dialogs)
    # - Logs session history
    # - Extracts topics of interest using the LLM

    # =========================
    # 6. RUN SESSION
    # =========================
    # Starts the full interaction loop

    session_manager.run()

    # =========================
    # 7. CLEAN EXIT
    # =========================
    sys.exit()
