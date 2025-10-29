#!/usr/bin/env python3
# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Pepper

# Import message types and requests
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoSetAutonomousLifeRequest,
    NaoWakeUpRequest,
    NaoRestRequest,
)
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest
from sic_framework.devices.common_pepper.pepper_motion_streamer import (
    PepperMotionStreamerConf,
    StartStreaming,
    StopStreaming,
)
from sic_framework.devices.common_naoqi.naoqi_motion import (
    NaoqiSmartStiffnessRequest,
    NaoqiBreathingRequest,
)


# ─────────────────────────────────────────────────────────────────────────────
# Puppeteering Application
# ─────────────────────────────────────────────────────────────────────────────
class PepperPuppeteeringDemo(SICApplication):
    """
    Pepper puppeteering demo application (Baseline).

    Demonstrates how to control one Pepper robot by moving another Pepper robot's joints.
    Requires two Pepper robots.

    • PUPPET      : Pepper moved manually by the operator
    • PERFORMER   : Pepper that mirrors the puppet's joint positions

    Controls
    --------
    • Press <Enter> (or Ctrl-C) in the terminal to finish the session

    This is the baseline implementation for comparison with the enhanced version.
    Both robots are always returned to a safe rest pose when the program exits.
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(PepperPuppeteeringDemo, self).__init__()
        
        # Demo-specific configuration
        self.puppet_ip = "10.0.0.184"
        self.performer_ip = "10.0.0.152"
        self.active_joints = ["Head", "RArm", "LArm"]
        self.stream_hz = 30
        
        # Robot instances
        self.puppet = None
        self.performer = None
        self.puppet_motion = None
        self.performer_motion = None
        
        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/pepper/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure both Pepper robots."""
        self.logger.info("Starting Pepper Puppeteering Demo...")
        
        self.logger.info("Initializing puppet (master) robot...")
        puppet_conf = PepperMotionStreamerConf(samples_per_second=self.stream_hz, stiffness=0.0)
        self.puppet = Pepper(self.puppet_ip, pepper_motion_conf=puppet_conf, dev_test=True)
        
        # Disable autonomous behaviour that interferes with manual control
        self.puppet.autonomous.request(NaoSetAutonomousLifeRequest("disabled"))
        
        # Wake up (Pepper cannot change stiffness while in rest)
        self.puppet.autonomous.request(NaoWakeUpRequest())
        
        # Disable smart stiffness and breathing for proper teleoperation
        self.puppet.motion.request(NaoqiSmartStiffnessRequest(False))
        self.puppet.motion.request(NaoqiBreathingRequest("Arms", False))
        
        # Puppet: zero stiffness on streamed chains so the operator can move joints
        self.puppet.stiffness.request(
            Stiffness(0, joints=self.active_joints, enable_joint_list_generation=False)
        )
        
        self.puppet_motion = self.puppet.motion_streaming()
        
        self.logger.info("Initializing performer robot...")
        performer_conf = PepperMotionStreamerConf(samples_per_second=self.stream_hz, stiffness=1.0)
        self.performer = Pepper(self.performer_ip, pepper_motion_conf=performer_conf, dev_test=True)
        
        # Disable autonomous behaviour
        self.performer.autonomous.request(NaoSetAutonomousLifeRequest("disabled"))
        
        # Wake up
        self.performer.autonomous.request(NaoWakeUpRequest())
        
        # Disable smart stiffness and breathing
        self.performer.motion.request(NaoqiSmartStiffnessRequest(False))
        self.performer.motion.request(NaoqiBreathingRequest("Arms", False))
        
        # Connect performer's motion-stream input to the puppet's output
        self.performer_motion = self.performer.motion_streaming(input_source=self.puppet_motion)
        
        self.logger.info("Both robots initialized successfully")
    
    def run(self):
        """Main application logic."""
        try:
            self.logger.info("Starting puppeteering session. Press <Enter> to stop.")
            
            # Start puppeteering
            self.puppet.tts.request(
                NaoqiTextToSpeechRequest("Start puppeteering", language="English")
            )
            self.puppet_motion.request(StartStreaming(self.active_joints))
            
            # Wait for user input
            input()
            
            self.logger.info("Stopping puppeteering session...")
            
        except KeyboardInterrupt:
            self.logger.info("Interrupt received. Stopping session.")
        except Exception as e:
            self.logger.error("Error in puppeteering demo: {}".format(e))
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of the puppeteering session."""
        self.logger.info("Shutting down puppeteering demo...")
        
        # Announce shutdown
        self.puppet.tts.request(
            NaoqiTextToSpeechRequest("We are done puppeteering", language="English")
        )
        
        # Stop streaming
        self.puppet_motion.request(StopStreaming())
        
        # Restore puppet stiffness before rest
        self.puppet.stiffness.request(
            Stiffness(0.7, joints=self.active_joints, enable_joint_list_generation=False)
        )
        
        # Re-enable autonomous life (optional but recommended for Pepper)
        self.puppet.autonomous.request(NaoSetAutonomousLifeRequest("solitary"))
        
        # Put both robots into rest
        self.puppet.autonomous.request(NaoRestRequest())
        self.performer.autonomous.request(NaoRestRequest())
        
        self.logger.info("Session ended; both Peppers are in rest pose.")


# ─────────────────────────────────────────────────────────────────────────────
# Script entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Create and run the demo
    demo = PepperPuppeteeringDemo()
    demo.run()