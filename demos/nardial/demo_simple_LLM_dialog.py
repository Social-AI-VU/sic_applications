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

DIALOG_CONFIG_PATH = BASE_DIR / "dialog_configs" / "simple_llm_dialogs.json"
GOOGLE_KEYFILE_PATH = SIC_APPLICATIONS_DIR / "conf" / "google" / "google-key.json"
ENV_FILE_PATH = SIC_APPLICATIONS_DIR / "conf" / ".env"


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
        rag=False,
    )

    agent = ConversationAgent(
        device_manager=device_manager,
        int_config=interaction_config,
    )

    session_manager = SessionManager(
        session_agenda=[
            "simple_llm_welcome",
            "simple_llm_chat",
            "simple_llm_goodbye",
        ],
        agent=agent,
        dialog_json_path=str(DIALOG_CONFIG_PATH),
    )

    session_manager.run()
    sys.exit()
