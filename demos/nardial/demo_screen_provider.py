"""
Nardial Screen Provider Demo

Demonstrates the NarDialPy screen provider: transcript display, HTML content, iframes,
and interactive buttons — all driven from a dialog JSON file.

No cloud services required: spoken text is printed to the terminal (NullTTSProvider)
and NLU input is read from the keyboard (WrittenKeywordNLUProvider).

The conversation flow is defined in:
    dialog_configs/demo_screen_dialogs.json

Before running this demo, make sure you have completed the required setup steps.
-------------------------
1. Install dependencies
-------------------------
    pip install "nardial[webserver]"
-------------------------
2. Start required services
-------------------------
You MUST run these in separate terminals BEFORE starting the demo:

    (MacOs/Linux)
    redis-server conf/redis/redis.conf
    OR
    (Windows)
    .\conf\redis\redis-server.exe .\conf\redis\redis.conf
    run-webserver
-------------------------
3. Open the browser
-------------------------
After starting the demo, open: http://localhost:5000
=========================
"""

import sys
from pathlib import Path

import nardial.providers.screen as _screen_pkg
from nardial.conversation_agent import ConversationAgent
from nardial.providers.device.desktop import DesktopAdapter
from nardial.providers.nlu.written_keyword import WrittenKeywordNLUProvider
from nardial.providers.screen.sic_adapter import SICScreenAdapter
from nardial.providers.tts.null import NullTTSProvider
from nardial.session_manager import SessionManager
from sic_framework.devices.desktop import Desktop
from sic_framework.services.webserver.webserver_service import Webserver, WebserverConf

BASE_DIR = Path(__file__).resolve().parent

_WEB_DIR = Path(_screen_pkg.__file__).parent / "web"

if __name__ == "__main__":
    # =========================
    # 1. SELECT DEVICE
    # =========================
    desktop = Desktop()
    device = DesktopAdapter(desktop)

    # =========================
    # 2. SCREEN PROVIDER
    # =========================
    # The SIC Webserver must be running (run-webserver) before this line.
    webserver = Webserver(
        conf=WebserverConf(
            templates_dir=str(_WEB_DIR / "templates"),
            static_dir=str(_WEB_DIR / "static"),
            port=5000,
        )
    )
    screen = SICScreenAdapter(webserver=webserver)

    # =========================
    # 3. CREATE AGENT
    # =========================
    agent = ConversationAgent(
        device=device,
        tts_provider=NullTTSProvider(),
        nlu_provider=WrittenKeywordNLUProvider(),
        screen_provider=screen,
    )

    # =========================
    # 4. SESSION MANAGER
    # =========================
    manager = SessionManager(
        session_agenda=["screen_demo"],
        agent=agent,
        dialog_json_path=str(BASE_DIR / "dialog_configs" / "demo_screen_dialogs.json"),
        participant_id="screen_demo_user",
    )

    # =========================
    # 5. RUN SESSION
    # =========================
    manager.run()

    # =========================
    # 6. CLEAN EXIT
    # =========================
    sys.exit()
