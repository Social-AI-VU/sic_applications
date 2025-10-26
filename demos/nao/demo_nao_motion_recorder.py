# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoRestRequest, NaoWakeUpRequest

# Import message types and requests
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import (
    NaoqiMotionRecorderConf,
    NaoqiMotionRecording,
    PlayRecording,
    StartRecording,
    StopRecording,
)
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness

# Import libraries necessary for the demo
import time


class NaoMotionRecorderDemo(SICApplication):
    """
    NAO motion recorder demo application.
    Demonstrates how to record and replay a motion on a NAO robot.
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(NaoMotionRecorderDemo, self).__init__()
        
        # Demo-specific initialization
        self.nao_ip = "XXX"
        self.motion_name = "motion_recorder_demo"
        self.record_time = 10
        self.nao = None
        self.chain = ["LArm", "RArm"]

        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/nao/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure the NAO robot."""
        self.logger.info("Starting NAO Motion Recorder Demo...")
        
        # Initialize NAO with motion recorder configuration
        conf = NaoqiMotionRecorderConf(use_sensors=True)
        self.nao = Nao(self.nao_ip, motion_record_conf=conf)
    
    def run(self):
        """Main application logic."""
        try:
            # Make sure the Nao is in active mode for motion recording.

            self.nao.autonomous.request(NaoWakeUpRequest())
            # Disable stiffness such that we can move it by hand
            self.nao.stiffness.request(Stiffness(stiffness=0.0, joints=self.chain))
            
            # Start recording
            self.logger.info("Start moving the robot! (not too fast)")
            self.nao.motion_record.request(StartRecording(self.chain))
            time.sleep(self.record_time)
            
            # Save the recording
            self.logger.info("Saving action")
            recording = self.nao.motion_record.request(StopRecording())
            recording.save(self.motion_name)
            
            # Replay the recording
            self.logger.info("Replaying action")
            self.nao.stiffness.request(
                Stiffness(stiffness=0.7, joints=self.chain)
            )  # Enable stiffness for replay
            recording = NaoqiMotionRecording.load(self.motion_name)
            self.nao.motion_record.request(PlayRecording(recording))

            # always end with a rest, whenever you reach the end of your code
            self.nao.autonomous.request(NaoRestRequest())
            self.logger.info("Motion recorder demo completed successfully")
        except Exception as e:
            self.logger.error("Exception: {}".format(e=e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoMotionRecorderDemo()
    demo.run()
