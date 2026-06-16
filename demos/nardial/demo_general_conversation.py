r"""
Nardial General Conversation Demo

A minimal conversational demo using Google TTS and keyboard input (no Dialogflow required).
Type your replies directly in the terminal when prompted.

The conversation flow is defined in:
    dialog_configs/general_conversation_dialogs.json

Before running this demo, make sure you have completed the required setup steps.
-------------------------
1. Install dependencies
-------------------------
    pip install "nardial[google-tts]"
-------------------------
2. Configure credentials
-------------------------
You MUST create the following file:

- Google credentials: conf/google/google-key.json

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
    run-google-tts
=========================
"""

import sys
from pathlib import Path

from nardial.conversation_agent import ConversationAgent
from nardial.interaction_orchestrator import InteractionConfig
from nardial.providers.device.desktop import DesktopAdapter
from nardial.providers.nlu.written_keyword import WrittenKeywordNLUProvider
from nardial.providers.tts.google import GoogleTTSConf, GoogleTTSProvider
from nardial.session_manager import SessionManager
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.devices.desktop import Desktop

BASE_DIR = Path(__file__).resolve().parent
SIC_APPLICATIONS_DIR = BASE_DIR.parents[1]

DIALOG_CONFIG_PATH = BASE_DIR / "dialog_configs" / "general_conversation_dialogs.json"
GOOGLE_KEYFILE_PATH = SIC_APPLICATIONS_DIR / "conf" / "google" / "google-key.json"

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
    session_manager = SessionManager(
        session_agenda=["greeting", "hero_can_dream_1", "dream12", "goodbye"],
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
