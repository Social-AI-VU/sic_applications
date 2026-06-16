r"""
Nardial Dialog with Characters Demo (ElevenLabs TTS)

This demo shows how to assign per-character voice settings in a dialog using ElevenLabs TTS.
Uses keyboard input (WrittenKeywordNLUProvider) — no Dialogflow required.

The conversation flow is defined in:
    dialog_configs/dialog_with_characters_elevenlabs.json

Before running this demo, make sure you have completed the required setup steps.
-------------------------
1. Install dependencies
-------------------------
    pip install "nardial[elevenlabs]"
-------------------------
2. Configure credentials
-------------------------
You MUST create the following file:

- ElevenLabs API key: conf/.env
Example `.env` entry:
    ELEVENLABS_API_KEY="your key"

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
    run-elevenlabs-tts
=========================
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from nardial.conversation_agent import ConversationAgent
from nardial.interaction_orchestrator import InteractionConfig
from nardial.providers.device.desktop import DesktopAdapter
from nardial.providers.nlu.written_keyword import WrittenKeywordNLUProvider
from nardial.providers.tts.elevenlabs import ElevenLabsTTSConf, ElevenLabsTTSProvider
from nardial.session_manager import SessionManager
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.devices.desktop import Desktop

BASE_DIR = Path(__file__).resolve().parent
SIC_APPLICATIONS_DIR = BASE_DIR.parents[1]

DIALOG_CONFIG_PATH = (
    BASE_DIR / "dialog_configs" / "dialog_with_characters_elevenlabs.json"
)
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
    # The default voice (voice_id below) is used for lines without an explicit "character" field.
    # Per-character voices are defined in the dialog JSON under "characters".
    tts_conf = ElevenLabsTTSConf(
        api_key=os.getenv("ELEVENLABS_API_KEY", ""),
        voice_id="9BWtsMINqrJLrRacOk9x",
        model_id="eleven_flash_v2_5",
    )
    tts = ElevenLabsTTSProvider(conf=tts_conf, device=device)

    # --- NLU ---
    # Type your replies in the terminal when prompted.
    nlu = WrittenKeywordNLUProvider()

    # --- Behavioral config ---
    interaction_config = InteractionConfig(
        post_speech_delay=0, signal_listening_behavior=False
    )

    # =========================
    # 3. CREATE AGENT
    # =========================
    agent = ConversationAgent(
        device=device,
        tts_provider=tts,
        nlu_provider=nlu,
        int_config=interaction_config,
    )

    # =========================
    # 4. SESSION MANAGER
    # =========================
    # session_agenda=[] lets the SessionManager run all eligible dialogs from the JSON.
    session_manager = SessionManager(
        session_agenda=[],
        agent=agent,
        dialog_json_path=str(DIALOG_CONFIG_PATH),
    )

    # =========================
    # 5. RUN SESSION
    # =========================
    session_manager.run()

    # =========================
    # 6. CLEAN EXIT
    # =========================
    sys.exit()
