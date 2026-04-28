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
    pip install social-interaction-cloud
    pip install --upgrade social-interaction-cloud[dialogflow,google-tts,openai-gpt]
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

    redis-server conf/redis/redis.conf
    run-dialogflow
    run-google-tts
    run-gpt
=========================
"""

# Import Nardial basics
from nardial.conversation_agent import ConversationAgent
from nardial.interaction_orchestrator import InteractionConfig
from nardial.session_manager import SessionManager

# Import SIC device(s), message(s), and service(s) we will be using
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.devices.desktop import Desktop

# Import other necessary libraries
from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parent
SIC_APPLICATIONS_DIR = BASE_DIR.parents[1]

DIALOG_CONFIG_PATH = BASE_DIR / "dialog_configs" / "simple_llm_dialogs.json"
GOOGLE_KEYFILE_PATH = SIC_APPLICATIONS_DIR / "conf" / "google" / "google-key.json"
ENV_FILE_PATH = SIC_APPLICATIONS_DIR / "conf" / ".env"


if __name__ == "__main__":
    # =========================
    # 1. SELECT DEVICE
    # =========================
    device = Desktop(
        speakers_conf=SpeakersConf(
            sample_rate=22050
        )
    )

    # =========================
    # 2. CONFIGURE INTERACTION
    # =========================
    # Keep RAG disabled for a simple LLM-only flow.
    interaction_config = InteractionConfig(
        google_keyfile_path=str(GOOGLE_KEYFILE_PATH),
        env_file_path=str(ENV_FILE_PATH),
        keyboard_input=True,
        rag=False,
    )

    # =========================
    # 3. CREATE AGENT
    # =========================
    agent = ConversationAgent(
        device_manager=device,
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
