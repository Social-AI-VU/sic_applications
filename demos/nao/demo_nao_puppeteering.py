# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao

# Import message types and requests
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoBackgroundMovingRequest,
    NaoBasicAwarenessRequest,
    NaoRestRequest,
)
from sic_framework.devices.common_naoqi.nao_motion_streamer import (
    NaoMotionStreamerConf,
    StartStreaming,
    StopStreaming,
)
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import (
    NaoqiTextToSpeechRequest,
)

# Import libraries necessary for the demo
import time


class NaoPupeteeringDemo(SICApplication):
    """
    NAO puppeteering demo application.
    Demonstrates how to control one NAO robot by moving another NAO robot's joints.
    Requires two NAO robots.
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(NaoPupeteeringDemo, self).__init__()
        
        # Demo-specific initialization
        self.puppet_master_ip = "XXX"
        self.puppet_ip = "XXX"
        self.puppeteering_duration = 30
        self.puppet_master = None
        self.puppet = None
        self.puppet_master_motion = None
        self.puppet_motion = None
        self.JOINTS = ["Head", "RArm", "LArm"]
        self.FIXED_JOINTS = ["RLeg", "LLeg"]

        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/nao/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure both NAO robots."""
        self.logger.info("Starting NAO Puppeteering Demo...")
        
        self.logger.info("Initializing puppet master...")
        conf = NaoMotionStreamerConf(samples_per_second=30)
        self.puppet_master = Nao(self.puppet_master_ip, motion_stream_conf=conf)
        self.puppet_master.autonomous.request(NaoBasicAwarenessRequest(False))
        self.puppet_master.autonomous.request(NaoBackgroundMovingRequest(False))
        self.puppet_master.stiffness.request(Stiffness(stiffness=0.0, joints=self.JOINTS))
        self.puppet_master_motion = self.puppet_master.motion_streaming()
        
        self.logger.info("Initializing puppet...")
        self.puppet = Nao(self.puppet_ip)
        self.puppet.autonomous.request(NaoBasicAwarenessRequest(False))
        self.puppet.autonomous.request(NaoBackgroundMovingRequest(False))
        self.puppet.stiffness.request(Stiffness(0.5, joints=self.JOINTS))
        self.puppet_motion = self.puppet.motion_streaming(input_source=self.puppet_master_motion)
        
        self.logger.info("Setting fixed joints to high stiffness...")
        # Set fixed joints to high stiffness such that the robots don't fall
        self.puppet_master.stiffness.request(Stiffness(0.7, joints=self.FIXED_JOINTS))
        self.puppet.stiffness.request(Stiffness(0.7, joints=self.FIXED_JOINTS))
    
    def run(self):
        """Main application logic."""
        try:
            self.logger.info("Starting both robots in rest pose...")
            # Start both robots in rest pose
            self.puppet.autonomous.request(NaoRestRequest())
            self.puppet_master.autonomous.request(NaoRestRequest())
            
            self.logger.info("Starting puppeteering...")
            # Start the puppeteering and let Nao say that you can start
            self.puppet_master_motion.request(StartStreaming(self.JOINTS))
            self.puppet_master.tts.request(
                NaoqiTextToSpeechRequest("Start puppeteering", language="English", animated=True)
            )
            
            # Wait for puppeteering duration
            time.sleep(self.puppeteering_duration)
            
            self.logger.info("Done puppeteering...")
            # Done puppeteering, let Nao say it's finished, and reset stiffness
            self.puppet_master.tts.request(
                NaoqiTextToSpeechRequest(
                    "We are done puppeteering", language="English", animated=True
                )
            )
            self.puppet_master.stiffness.request(Stiffness(0.7, joints=self.JOINTS))
            self.puppet_master_motion.request(StopStreaming())
            
            # Set both robots in rest pose again
            self.puppet.autonomous.request(NaoRestRequest())
            self.puppet_master.autonomous.request(NaoRestRequest())
            
            self.logger.info("Puppeteering demo completed successfully")
        except Exception as e:
            self.logger.error("Error in puppeteering demo: {}".format(e=e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoPupeteeringDemo()
    demo.run()
