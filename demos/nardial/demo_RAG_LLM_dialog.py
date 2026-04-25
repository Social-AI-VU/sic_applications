import sys
from pathlib import Path
from typing import Any, cast

from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.devices.desktop import Desktop

from nardial.conversation_agent import ConversationAgent
from nardial.interaction_orchestrator import InteractionConfig
from nardial.session_manager import SessionManager


BASE_DIR = Path(__file__).resolve().parent
SIC_APPLICATIONS_DIR = BASE_DIR.parents[1]

DOCS_DIR = BASE_DIR / "RAG_example_docs"
DIALOG_CONFIG_PATH = BASE_DIR / "dialog_configs" / "rag_llm_dialogs.json"
GOOGLE_KEYFILE_PATH = SIC_APPLICATIONS_DIR / "conf" / "google" / "google-key.json"
ENV_FILE_PATH = SIC_APPLICATIONS_DIR / "conf" / ".env"

INDEX_NAME = "nardial_pip_lantern_docs"
INGEST_DOCS = True


if __name__ == "__main__":
    device = Desktop(
        speakers_conf=SpeakersConf(
            sample_rate=22050
        )
    )
    device_manager = cast(Any, device)

    interaction_config = InteractionConfig(
        google_keyfile_path=str(GOOGLE_KEYFILE_PATH),
        env_file_path=str(ENV_FILE_PATH),
        keyboard_input=True,
        rag=True,
        ingest_docs=INGEST_DOCS,
        input_path=str(DOCS_DIR),
        index_name=INDEX_NAME,
        embedding_model="text-embedding-3-large",
        chunk_chars=900,
        chunk_overlap=120,
        override_existing=True,
        force_recreate_index=False,
    )

    agent = ConversationAgent(
        device_manager=device_manager,
        int_config=interaction_config,
    )

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
    )

    session_manager.run()
    sys.exit()
