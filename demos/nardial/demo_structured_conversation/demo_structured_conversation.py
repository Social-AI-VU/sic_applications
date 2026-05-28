"""
Nardial Structured Conversation Demo

This demo shows how to use Nardial to conduct a structured conversation with a user.

The conversation is conducted through a series of dialogs, which are defined in the
dialog_configs/structured_conversation_dialogs.json file.

Before running this demo, make sure you have completed the required setup steps.
This demo depends on external services for speech, language understanding, and LLM responses.
-------------------------
1. Install dependencies
-------------------------
    pip install nardial
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

WARNING: Never commit these files to version control.
-------------------------
3. Start required services
-------------------------
Install Docker Desktop (services start automatically via docker-compose.yml).

Manual alternative (without Docker auto-start):
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
from sic_framework.core.sic_application import SICApplication
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.devices.desktop import Desktop

# Import other necessary libraries
from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parent
SIC_APPLICATIONS_DIR = BASE_DIR.parents[2]

DIALOG_CONFIG_PATH = BASE_DIR / "dialog_configs" / "structured_conversation_dialogs.json"
GOOGLE_KEYFILE_PATH = SIC_APPLICATIONS_DIR / "conf" / "google" / "google-key.json"
ENV_FILE_PATH = SIC_APPLICATIONS_DIR / "conf" / ".env"

if __name__ == '__main__':
    app = SICApplication(services_compose="docker-compose.yml")

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
    interaction_config = InteractionConfig(
        google_keyfile_path=str(GOOGLE_KEYFILE_PATH),
        keyboard_input=True,
        env_file_path=str(ENV_FILE_PATH),
    )

    # =========================
    # 3. CREATE AGENT
    # =========================
    agent = ConversationAgent(
        device_manager=device,
        int_config=interaction_config
    )

    # =========================
    # 4. DEFINE SESSION STRUCTURE
    # =========================
    session_agenda = [
        "welcome_and_name",
        "plan_activity",
        "adapt_to_user_energy",
        "structured_goodbye",
    ]

    # =========================
    # 5. SESSION MANAGER
    # =========================
    session_manager = SessionManager(
        session_agenda=session_agenda,
        agent=agent,
        dialog_json_path=str(DIALOG_CONFIG_PATH),
        participant_id="2",
    )

    # =========================
    # 6. RUN SESSION
    # =========================
    session_manager.run()

    # =========================
    # 7. CLEAN EXIT
    # =========================
    app.cleanup_resources(log_shutdown=True)
    sys.exit()
