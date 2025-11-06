"""
Simple Pepper Tablet Website Display Demo

This demo connects to Pepper and displays a website on the tablet.

Usage:
    python demo_pepper_tablet_website.py

Requirements:
    - Pepper robot connected to network
    - Update ROBOT_IP with your Pepper's IP address
    - Update WEBSITE_URL with the URL you want to display
"""

# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Pepper

# Import message types
from sic_framework.devices.common_pepper.pepper_tablet import UrlMessage


# ────────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────────
ROBOT_IP = "10.0.0.152"  # Replace with your Pepper's IP address
WEBSITE_URL = "XXX"  # Website to display


# ─────────────────────────────────────────────────────────────────────────────
# Pepper Tablet Demo Application
# ─────────────────────────────────────────────────────────────────────────────
class PepperTabletDemo(SICApplication):
    """
    Simple Pepper tablet demo that displays a website.
    """
    
    def __init__(self):
        super(PepperTabletDemo, self).__init__()
        self.set_log_level(sic_logging.INFO)
        
        # Initialize Pepper
        self.logger.info("Connecting to Pepper at {}...".format(ROBOT_IP))
        self.pepper = Pepper(ip=ROBOT_IP)
        # self.pepper = Pepper(ip=ROBOT_IP, dev_test=True)
        self.logger.info("Connected successfully!")
    
    def run(self):
        """Display website on Pepper's tablet."""
        try:
            # Display website on the tablet
            self.logger.info("Displaying website on Pepper's tablet...")
            self.logger.info("URL: {}".format(WEBSITE_URL))
            self.pepper.tablet_display_url.send_message(UrlMessage(WEBSITE_URL))
            self.logger.info("Website is now displayed on the tablet!")
            
        except Exception as e:
            self.logger.error("Error during demo: {}".format(e))
            import traceback
            traceback.print_exc()


# ─────────────────────────────────────────────────────────────────────────────
# Script entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo = PepperTabletDemo()
    demo.run()
