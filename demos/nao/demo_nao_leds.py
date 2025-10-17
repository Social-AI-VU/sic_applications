# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao
from sic_framework.devices.nao_stub import NaoStub

# Import message types and requests
from sic_framework.devices.common_naoqi.naoqi_leds import (
    NaoFadeRGBRequest,
    NaoLEDRequest,
)

# Import libraries necessary for the demo
import time

class NaoLEDsDemo(SICApplication):
    """
    NAO LEDs demo application.
    Demonstrates how to control the NAO robot's LEDs.
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(NaoLEDsDemo, self).__init__()
        
        # Demo-specific initialization
        self.nao_ip = "XXX"
        self.nao = None

        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/nao/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure the NAO robot."""
        self.logger.info("Starting NAO LEDs Demo...")
        
        # Initialize the NAO robot
        self.nao = Nao(ip=self.nao_ip)
    
    def run(self):
        """Main application logic."""
        try:
            self.logger.info("Requesting Eye LEDs to turn on")
            reply = self.nao.leds.request(NaoLEDRequest("FaceLeds", True))
            time.sleep(1)

            self.logger.info("Setting right Eye LEDs to red")
            reply = self.nao.leds.request(NaoFadeRGBRequest("RightFaceLeds", 1, 0, 0, 0))
            time.sleep(1)

            self.logger.info("Setting left Eye LEDs to blue")
            reply = self.nao.leds.request(NaoFadeRGBRequest("LeftFaceLeds", 0, 0, 1, 0))

            self.logger.info("LEDs demo completed successfully")
        except Exception as e:
            self.logger.error("Error in LEDs demo: {}".format(e=e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoLEDsDemo()
    demo.run()
