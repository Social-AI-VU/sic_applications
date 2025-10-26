# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoRestRequest
from sic_framework.devices.common_naoqi.naoqi_leds import NaoLEDRequest
from sic_framework.devices.nao_stub import NaoStub

# Import message types and requests
from sic_framework.devices.common_naoqi.naoqi_motion import (
    NaoPostureRequest,
    NaoqiAnimationRequest,
)

# Import libraries necessary for the demo
import time


class NaoMotionDemo(SICApplication):
    """
    NAO motion demo application.
    Demonstrates how to make NAO perform predefined postures and animations.
    
    For a list of postures, see NaoPostureRequest class or
    http://doc.aldebaran.com/2-4/family/robots/postures_robot.html#robot-postures
    
    A list of all NAO animations can be found here:
    http://doc.aldebaran.com/2-4/naoqi/motion/alanimationplayer-advanced.html#animationplayer-list-behaviors-nao
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(NaoMotionDemo, self).__init__()
        
        # Demo-specific initialization
        self.nao_ip = "XXX"
        self.nao = None

        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/nao/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure the NAO robot."""
        self.logger.info("Starting NAO Motion Demo...")
        
        # Initialize the NAO robot
        self.nao = Nao(ip=self.nao_ip)
    
    def run(self):
        """Main application logic."""
        try:
            self.logger.info("Requesting Stand posture")
            self.nao.motion.request(NaoPostureRequest("Stand", 0.5))
            time.sleep(1)

            self.logger.info("Playing Hey gesture animation")
            self.nao.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Hey_1"))
            time.sleep(1)

            # Reset the eyes when necessary
            self.nao.leds.request(NaoLEDRequest("FaceLeds", True))
            # always end with a rest, whenever you reach the end of your code
            self.nao.autonomous.request(NaoRestRequest())

            self.logger.info("Motion demo completed successfully")
        except Exception as e:
            self.logger.error("Error in motion demo: {}".format(e=e))
        finally:
            self.logger.info("Shutting down application")
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoMotionDemo()
    demo.run()
