# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# import the device(s) we will be using
from sic_framework.devices import Pepper

# import the message types we will be using
from sic_framework.devices.common_pepper.pepper_tablet import (
    UrlMessage,
    WifiConnectRequest,
    ClearDisplayMessage,
)

import time

# ────────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────────
ROBOT_IP = "XXX"  # Replace with your Pepper's IP address

# Wi-Fi settings (optional). Leave WIFI_SSID empty to skip.
WIFI_SSID = "XXX"
WIFI_PASSWORD = "XXX"
WIFI_SECURITY = "XXX"  # one of: "open", "wep", "wpa", "wpa2"

WEBSITE_URL = "http://google.com"

# Display timing
DISPLAY_DURATION_URL = 8.0

class PepperTabletCapabilityDemo(SICApplication):
    """
    Demonstrates tablet messaging capabilities on Pepper.
    """

    def __init__(self):
        super(PepperTabletCapabilityDemo, self).__init__()
       
        self.set_log_level(sic_logging.DEBUG)

        self.Pepper = None
        
        # Optional: set log file path if needed
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/pepper/tablet_demos/logs")
        self.setup()


    def setup(self):
        """
        Setup the Pepper tablet capability demo.
        """
        # Connect to Pepper
        self.logger.info("Connecting to Pepper at %s ...", ROBOT_IP)
        self.pepper = Pepper(ip=ROBOT_IP)
        self.logger.info("Connected successfully!")
        self.logger.info("Setting up Pepper tablet capability demo.")
        
        # Connect Pepper's tablet to Wi-Fi (optional)
        if WIFI_SSID:
            self.logger.info(
                "Requesting tablet Wi-Fi connection to SSID '%s'...", WIFI_SSID
            )
            response = self.pepper.tablet.request(
                WifiConnectRequest(
                    network_name=WIFI_SSID,
                    network_password=WIFI_PASSWORD,
                    network_type=WIFI_SECURITY
                )
            )
            if not response:
                self.logger.error("Failed to connect Pepper's tablet to Wi-Fi network")
            else:
                self.logger.info("Wi-Fi connection established successfully!")
        else:
            self.logger.info("Skipping Wi-Fi connection step (no SSID provided).")

    def run(self):
        """
        Execute the capability walkthrough.
        """
        try:
            self.logger.info("Starting Pepper tablet capability demo.")

            # 1. Display a website
            if WEBSITE_URL:
                self.logger.info("Displaying website: %s", WEBSITE_URL)
                self.pepper.tablet.send_message(UrlMessage(WEBSITE_URL))
                time.sleep(DISPLAY_DURATION_URL)

            # 2. Clear tablet display
            self.logger.info("Clearing the tablet display.")
            self.pepper.tablet.send_message(ClearDisplayMessage())

            self.logger.info("Pepper tablet capability demo complete!")

        except Exception as exc:
            self.logger.error("Error during tablet demo: %s", exc)
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    demo = PepperTabletCapabilityDemo()
    demo.run()