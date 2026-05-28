"""
Nardial RAG + LLM Conversation Demo

This demo shows how to run a Nardial conversation that uses retrieval-augmented
generation (RAG) for selected llm_based dialog blocks.

The conversation flow is defined in:
    dialog_configs/rag_llm_dialogs.json

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

WARNING: Never commit credential files to version control.
-------------------------
3. Start required services
-------------------------
Install Docker Desktop (services start automatically via docker-compose.yml).

Manual alternative (without Docker auto-start):
    run-redis --data-dir <path to where you want to save vector database>
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

# import other libraries
from pathlib import Path
import sys


# Path inside the datastore container (see docker-compose.yml volume mount).
DOCKER_RAG_DOCS_PATH = "/ingest/rag_docs"

BASE_DIR = Path(__file__).resolve().parent
SIC_APPLICATIONS_DIR = BASE_DIR.parents[2]

DOCS_DIR = BASE_DIR / "RAG_example_docs"
DIALOG_CONFIG_PATH = BASE_DIR / "dialog_configs" / "rag_llm_dialogs.json"
GOOGLE_KEYFILE_PATH = SIC_APPLICATIONS_DIR / "conf" / "google" / "google-key.json"
ENV_FILE_PATH = SIC_APPLICATIONS_DIR / "conf" / ".env"

INDEX_NAME = "nardial_pip_lantern_docs"
INGEST_DOCS = True


if __name__ == "__main__":
    app = SICApplication(services_compose="docker-compose.yml")

    ingest_path = (
        DOCKER_RAG_DOCS_PATH
        if app._services_compose_started
        else str(DOCS_DIR)
    )

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
        env_file_path=str(ENV_FILE_PATH),
        keyboard_input=True,
        rag=True,
        ingest_docs=INGEST_DOCS,
        input_path=ingest_path,
        index_name=INDEX_NAME,
        embedding_model="text-embedding-3-large",
        chunk_chars=900,
        chunk_overlap=120,
        override_existing=True,
        force_recreate_index=False,
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
            "rag_llm_welcome",
            "non_rag_warmup",
            "rag_character_backstory",
            "rag_practical_help",
            "non_rag_reflection",
            "rag_llm_goodbye",
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
    app.cleanup_resources(log_shutdown=True)
    sys.exit()
