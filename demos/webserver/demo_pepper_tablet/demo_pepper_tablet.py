import os
import threading
import time
import urllib.request
import webbrowser

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.devices import Pepper
from sic_framework.devices.common_pepper.pepper_tablet import (
    ClearDisplayMessage,
    UrlMessage,
    WifiConnectRequest,
)
from sic_framework.services.webserver.webserver_service import Webserver, WebserverConf


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------
ROBOT_IP = "10.0.0.168"  # Replace with your Pepper's IP address

# Optional tablet Wi-Fi connection. Leave WIFI_SSID empty to skip this step.
WIFI_SSID = ""
WIFI_PASSWORD = ""
WIFI_SECURITY = "wpa2"  # one of: "open", "wep", "wpa", "wpa2"

# Local webserver settings.
WEB_PORT = 8080
AUTO_OPEN_LOCAL_BROWSER = True


class PepperTabletWebserverDemo(SICApplication):
    """
    Unified Pepper tablet demo using the SIC webserver.

    - Serves `webfiles/index.html` and any static assets in `webfiles/`
    - Shows that page on Pepper's tablet
    - Supports mixed media (images, audio, video) via normal HTML tags
    """

    def __init__(self):
        super(PepperTabletWebserverDemo, self).__init__()

        self.set_log_level(sic_logging.DEBUG)
        self.pepper = None
        self.webserver = None

        self.setup()

    def setup(self):
        self.logger.info("Connecting to Pepper at %s ...", ROBOT_IP)
        self.pepper = Pepper(ip=ROBOT_IP)
        self.logger.info("Connected to Pepper.")

        self._maybe_connect_tablet_wifi()
        self._start_webserver()

        # Use the host IP so Pepper can reach the page (not localhost).
        tablet_url = "http://{}:{}/".format(self.client_ip, WEB_PORT)
        self.logger.info("Displaying web page on Pepper tablet: %s", tablet_url)
        self.pepper.tablet.send_message(UrlMessage(tablet_url))

        if AUTO_OPEN_LOCAL_BROWSER:
            local_url = "http://localhost:{}/".format(WEB_PORT)
            threading.Thread(target=lambda: self._open_when_ready(local_url), daemon=True).start()
            self.logger.info("Local preview URL: %s", local_url)

    def _start_webserver(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        webfiles_dir = os.path.join(current_dir, "webfiles")

        conf = WebserverConf(
            host="0.0.0.0",
            port=WEB_PORT,
            templates_dir=webfiles_dir,
            static_dir=webfiles_dir,
            ephemeral=True,
        )
        self.webserver = Webserver(conf=conf)
        self.logger.info("Webserver started on port %d", WEB_PORT)

    def _maybe_connect_tablet_wifi(self):
        if not WIFI_SSID:
            self.logger.info("Skipping tablet Wi-Fi setup (WIFI_SSID is empty).")
            return

        self.logger.info("Connecting tablet to Wi-Fi SSID '%s'...", WIFI_SSID)
        try:
            response = self.pepper.tablet.request(
                WifiConnectRequest(
                    network_name=WIFI_SSID,
                    network_password=WIFI_PASSWORD,
                    network_type=WIFI_SECURITY,
                )
            )
            if response:
                self.logger.info("Tablet Wi-Fi connection request succeeded.")
            else:
                self.logger.warning("Tablet Wi-Fi connection request returned no response.")
        except Exception as e:
            self.logger.error("Failed to connect tablet Wi-Fi: %s", e)

    def _open_when_ready(self, url: str) -> None:
        ready_url = url.rstrip("/") + "/readyz"
        deadline = time.time() + 10.0
        while time.time() < deadline and not self.shutdown_event.is_set():
            try:
                with urllib.request.urlopen(ready_url, timeout=0.5) as resp:
                    if resp.status == 200:
                        webbrowser.open(url, new=2)
                        return
            except Exception:
                pass
            time.sleep(0.1)
        webbrowser.open(url, new=2)

    def run(self):
        try:
            self.logger.info("Pepper tablet webserver demo is running.")
            while not self.shutdown_event.is_set():
                time.sleep(0.25)
        except KeyboardInterrupt:
            pass
        finally:
            try:
                self.logger.info("Clearing Pepper tablet display.")
                self.pepper.tablet.send_message(ClearDisplayMessage())
                time.sleep(0.5)  # give tablet time to process before teardown
            except Exception as e:
                self.logger.debug("Could not clear tablet on exit: %s", e)
            self.shutdown()


if __name__ == "__main__":
    demo = PepperTabletWebserverDemo()
    demo.run()
