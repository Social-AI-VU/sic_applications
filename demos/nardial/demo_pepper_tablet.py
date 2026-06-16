r"""
Nardial Pepper Tablet Screen Demo

Demonstrates the NarDialPy screen provider on a Pepper robot's built-in tablet.
Uses keyboard input (WrittenKeywordNLUProvider) — no TTS cloud service required.

The conversation flow is defined in:
    dialog_configs/demo_screen_dialogs.json

Before running this demo, make sure you have completed the required setup steps.
-------------------------
1. Install dependencies
-------------------------
    pip install "nardial[webserver]"
-------------------------
2. Configure the demo
-------------------------
Set your Pepper's IP and your computer's LAN IP in this file:
    pepper = Pepper("XXX.XXX.XXX.XXX")   # Pepper's IP
    host_ip = "XXX.XXX.XXX.XXX"          # Your computer's LAN IP (not localhost)

Find your LAN IP with:
    (MacOs/Linux) ifconfig
    (Windows)     ipconfig
-------------------------
3. Start required services
-------------------------
You MUST run these in separate terminals BEFORE starting the demo:

    (MacOs/Linux)
    redis-server conf/redis/redis.conf
    OR
    (Windows)
    .\conf\redis\redis-server.exe .\conf\redis\redis.conf
    run-webserver
-------------------------
4. Open the browser on Pepper's tablet
-------------------------
After starting the demo, the tablet should open automatically.
You can also open it manually at: http://<host_ip>:<port>
=========================
"""

import sys
from pathlib import Path

import nardial.providers.screen as _screen_pkg
from nardial.conversation_agent import ConversationAgent
from nardial.providers.device.pepper import PepperAdapter
from nardial.providers.nlu.written_keyword import WrittenKeywordNLUProvider
from nardial.providers.screen.pepper_tablet import PepperTabletScreenAdapter
from nardial.providers.tts.null import NullTTSProvider
from nardial.session_manager import SessionManager
from sic_framework.devices.pepper import Pepper
from sic_framework.services.webserver.webserver_service import Webserver, WebserverConf

BASE_DIR = Path(__file__).resolve().parent

_WEB_DIR = Path(_screen_pkg.__file__).parent / "web"

if __name__ == "__main__":
    # =========================
    # 1. SELECT DEVICE
    # =========================
    pepper = Pepper("10.0.0.148")  # Replace with your Pepper's IP address
    device = PepperAdapter(pepper)

    # =========================
    # 2. SCREEN PROVIDER
    # =========================
    # host_ip must be your computer's LAN address that Pepper can route to (not localhost).
    host_ip = "10.0.0.184"  # Replace with your computer's LAN IP
    port = 5001

    allowed_origin = f"http://{host_ip}:{port}"
    webserver = Webserver(
        conf=WebserverConf(
            templates_dir=str(_WEB_DIR / "templates"),
            static_dir=str(_WEB_DIR / "static"),
            port=port,
            cors_allowed_origins=[allowed_origin],
        )
    )

    screen = PepperTabletScreenAdapter(
        webserver=webserver,
        host_ip=host_ip,
        tablet=pepper.tablet,
        port=port,
    )

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
