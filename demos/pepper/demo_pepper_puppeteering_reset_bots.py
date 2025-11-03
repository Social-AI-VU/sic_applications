# External imports
import os

# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Pepper

# Import message types and requests
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoSetAutonomousLifeRequest,
    NaoWakeUpRequest,
    NaoRestRequest,
)
from sic_framework.devices.common_naoqi.naoqi_motion import (
    NaoqiMoveTowardRequest,
    NaoqiBreathingRequest,
    NaoqiSmartStiffnessRequest,
)

# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Set Redis password environment variable
os.environ['REDIS_PASSWORD'] = 'changemeplease'

# Robot IPs
PUPPET_IP = "XXX"
PERFORMER_IP = "XXX"

# ─────────────────────────────────────────────────────────────────────────────
# Manual Drive Application
# ─────────────────────────────────────────────────────────────────────────────
class RobotManualDriveApp(SICApplication):
    """
    Robot manual drive application for Pepper robot relocation.
    
    Puts both Pepper robots in manual drive mode, allowing operators to manually
    move them to new positions without resistance. Use this to relocate robots
    between tasks.

    Usage:
        python demo_pepper_puppeteering_reset_bots.py

    Features:
    - Wakes up both robots
    - Disables autonomous behaviors, smart stiffness, and breathing
    - Stops all movement
    - Allows manual repositioning without resistance
    - Safely puts robots to rest when finished
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(RobotManualDriveApp, self).__init__()
        
        # Demo-specific configuration
        self.puppet_ip = PUPPET_IP
        self.performer_ip = PERFORMER_IP
        
        # Robot instances
        self.puppet = None
        self.performer = None
        
        self.set_log_level(sic_logging.INFO)
        
        self.setup()
    
    def setup(self):
        """Initialize and configure both Pepper robots for manual drive."""
        self.logger.info("Robot Manual Drive Script")
        self.logger.info("=========================")
        self.logger.info("Connecting to robots...")
        
        self.logger.info("Using standard connection...")
        self.puppet = Pepper(self.puppet_ip)
        self.performer = Pepper(self.performer_ip)
        
        self.logger.info("Setting up robots for manual drive...")
        
        # Wake up robots (required for control)
        self.puppet.autonomous.request(NaoWakeUpRequest())
        self.performer.autonomous.request(NaoWakeUpRequest())
        
        # Disable all autonomous behaviors
        self.puppet.autonomous.request(NaoSetAutonomousLifeRequest("disabled"))
        self.performer.autonomous.request(NaoSetAutonomousLifeRequest("disabled"))
        
        # Disable smart stiffness and breathing
        self.puppet.motion.request(NaoqiSmartStiffnessRequest(False))
        self.performer.motion.request(NaoqiSmartStiffnessRequest(False))
        self.puppet.motion.request(NaoqiBreathingRequest("Arms", False))
        self.performer.motion.request(NaoqiBreathingRequest("Arms", False))
        
        # Set velocity to zero to stop any movement
        self.puppet.motion.request(NaoqiMoveTowardRequest(0.0, 0.0, 0.0))
        self.performer.motion.request(NaoqiMoveTowardRequest(0.0, 0.0, 0.0))
        
        self.logger.info("✓ Robots are ready for manual drive!")
        self.logger.info("  - Both robots are awake but autonomous behaviors disabled")
        self.logger.info("  - Smart stiffness and breathing disabled")
        self.logger.info("  - Movement stopped")
        self.logger.info("  - You can now manually drive them around")
    
    def run(self):
        """Main application logic."""
        try:
            self.logger.info("\nWhen you're done relocating the robots, press Enter to put them to rest...")
            
            # Wait for user to finish moving robots
            input()
            
            self.logger.info("Putting robots to rest...")
            
        except KeyboardInterrupt:
            self.logger.info("\nInterrupt received. Putting robots to rest...")
        except Exception as e:
            self.logger.error("Error in manual drive: {}".format(e))
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown - put robots to rest."""
        self.logger.info("Shutting down manual drive...")
        
        try:
            # Put robots to rest
            self.puppet.autonomous.request(NaoRestRequest())
            self.performer.autonomous.request(NaoRestRequest())
            
            self.logger.info("✓ Both robots are now in rest mode")
        except Exception as e:
            self.logger.error("✗ Error putting robots to rest: {}".format(e))
            self.logger.warning("Please manually check robot states")
        
        self.logger.info("\nManual drive complete. You can now start your next task.")


# ─────────────────────────────────────────────────────────────────────────────
# Script entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Create and run the app
    app = RobotManualDriveApp()
    app.run() 