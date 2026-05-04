"""
Nardial Simple LLM Conversation Demo

This demo shows a minimal llm_based conversation flow without RAG.

The conversation flow is defined in:
    dialog_configs/simple_llm_dialogs.json

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
Example `.env` entry:
    OPENAI_API_KEY="your key"

WARNING: Never commit credential files to version control.
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
SIC_APPLICATIONS_DIR = BASE_DIR.parents[1]

DIALOG_CONFIG_PATH = BASE_DIR / "dialog_configs" / "simple_llm_dialogs.json"
GOOGLE_KEYFILE_PATH = SIC_APPLICATIONS_DIR / "conf" / "google" / "google-key.json"
ENV_FILE_PATH = SIC_APPLICATIONS_DIR / "conf" / ".env"

load_dotenv(ENV_FILE_PATH)


if __name__ == "__main__":
    # =========================
    # 1. SELECT DEVICE
    # =========================
    desktop = Desktop(speakers_conf=SpeakersConf(sample_rate=22050))
    device = DesktopAdapter(desktop)

    # Uncomment to use Pepper instead:
    # from nardial.providers.device.pepper import PepperAdapter
    # from sic_framework.devices import Pepper
    # device = PepperAdapter(Pepper(ip="XXX"))  # Replace with your robot's IP

    # =========================
    # 2. CONFIGURE PROVIDERS
    # =========================

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

    # --- LLM ---
    # Reads OPENAI_API_KEY from the environment (loaded via dotenv above).
    llm = OpenAIGPTProvider()

    # --- Behavioral config ---
    interaction_config = InteractionConfig(
        # language="nl",
        # post_speech_delay=0.5,
    )

    # =========================
    # 3. CREATE AGENT
    # =========================
    agent = ConversationAgent(
        device=device,
        tts_provider=tts,
        nlu_provider=nlu,
        llm_provider=llm,
        int_config=interaction_config,
    )

    # =========================
    # 4. SESSION MANAGER
    # =========================
    session_manager = SessionManager(
        session_agenda=[
            "simple_llm_welcome",
            "simple_llm_chat",
            "simple_llm_goodbye",
        ],
        agent=agent,
        dialog_json_path=str(DIALOG_CONFIG_PATH),
        participant_id="1",
    )

    # =========================
    # 5. RUN SESSION
    # =========================
    session_manager.run()

    # =========================
    # 6. CLEAN EXIT
    # =========================
    sys.exit()
