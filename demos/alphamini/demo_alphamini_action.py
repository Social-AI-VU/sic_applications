# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.alphamini import Alphamini

# Import message types and requests
from sic_framework.devices.common_mini.mini_animation import MiniActionRequest


class AlphaminiActionDemo(SICApplication):
    """
    Alphamini action demo application.
    Demonstrates how to make Alphamini perform predefined actions/animations.
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(AlphaminiActionDemo, self).__init__()
        
        self.mini = None
        self.mini_ip = "XXX"
        self.mini_id = "000XXX"
        self.mini_password = "mini"
        self.redis_ip = "XXX"

        self.set_log_level(sic_logging.DEBUG)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/alphamini/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure the Alphamini robot."""
        self.logger.info("Initializing Alphamini...")
        
        # Initialize Alphamini
        self.mini = Alphamini(
            ip=self.mini_ip,
            mini_id=self.mini_id,
            mini_password=self.mini_password,
            redis_ip=self.redis_ip
        )
    
    def run(self):
        """Main application logic."""
        try:
            self.logger.info("Performing action...")
            self.mini.animation.request(MiniActionRequest("018"))
            
            self.logger.info("Action demo completed successfully")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # Replace with your Alphamini's details
    demo = AlphaminiActionDemo()
    demo.run()

