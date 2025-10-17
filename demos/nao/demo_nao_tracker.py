# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao

# Import message types and requests
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness
from sic_framework.devices.common_naoqi.naoqi_tracker import (
    RemoveTargetRequest,
    StartTrackRequest,
    StopAllTrackRequest,
)

# Import libraries necessary for the demo
import time


class NaoTrackerDemo(SICApplication):
    """
    NAO tracker demo application.
    Demonstrates how to make NAO:
    1. Track a face with its head.
    2. Move its end-effector (both arms in this case) to track a red ball, given a position relative to the ball.
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(NaoTrackerDemo, self).__init__()
        
        # Demo-specific initialization
        self.nao_ip = "XXX"
        self.nao = None
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/nao/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure the NAO robot."""
        self.logger.info("Starting NAO Tracker Demo...")
        
        # Connect to NAO
        self.nao = Nao(ip=self.nao_ip)
    
    def run(self):
        """Main application logic."""
        try:
            # Start tracking a face
            target_name = "Face"
            
            self.logger.info("Enabling head stiffness and starting face tracking...")
            # Enable stiffness so the head joint can be actuated
            self.nao.stiffness.request(Stiffness(stiffness=1.0, joints=["Head"]))
            self.nao.tracker.request(
                StartTrackRequest(target_name=target_name, size=0.2, mode="Head", effector="None")
            )
            
            # Wait for a specific time
            time.sleep(10)
            
            # Unregister target face
            self.logger.info("Stopping face tracking...")
            self.nao.tracker.request(RemoveTargetRequest(target_name))
            
            # Start tracking a red ball using nao's arms
            # Set a robot position relative to target so that the robot stays a 30 centimeters (along x axis) with 10 cm threshold
            self.logger.info("Starting red ball tracking with arms...")
            target_name = "RedBall"
            move_rel_position = [-0.3, 0.0, 0.0, 0.1, 0.1, 0.1]
            self.nao.tracker.request(
                StartTrackRequest(
                    target_name=target_name,
                    size=0.06,
                    mode="Move",
                    effector="Arms",
                    move_rel_position=move_rel_position,
                )
            )
            
            # Wait for a specific time
            time.sleep(10)
            
            # Stop tracking everything
            self.logger.info("Stopping all tracking...")
            self.nao.tracker.request(StopAllTrackRequest())
            
            self.logger.info("Tracker demo completed successfully")
        except Exception as e:
            self.logger.error("Error in tracker demo: {}".format(e=e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoTrackerDemo()
    demo.run()
