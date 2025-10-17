# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao
from sic_framework.devices.nao_stub import NaoStub


class NaoButtonDemo(SICApplication):
    """
    NAO button demo application.

    Demonstrates how to use the NAO robot buttons.

    :param nao_ip: The IP address of the NAO robot.
    :type nao_ip: str
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(NaoButtonDemo, self).__init__()
        
        # Demo-specific initialization
        self.nao_ip = "XXX"
        self.nao = None
        
        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/nao/logs")
        
        self.setup()
    
    def on_button_press(self, button_message):
        """
        Callback function for NAO button presses.
        
        Args:
            button_message: The button press message containing button value.
        
        Returns:
            None
        """
        self.logger.info(f"Pressed: {button_message.value}")
    
    def setup(self):
        """Initialize and configure the NAO robot."""
        self.logger.info("Starting NAO Button Demo...")
        
        # Initialize the NAO robot
        self.nao = Nao(ip=self.nao_ip)
        
        # Register callback for button presses
        self.nao.buttons.register_callback(self.on_button_press)
        
        self.logger.info("Demo running. Press buttons on the robot...")
    
    def run(self):
        """Main application loop."""
        try:
            while not self.shutdown_event.is_set():
                pass  # Keep script alive
            
            self.logger.info("Button demo completed successfully")
        except Exception as e:
            self.logger.error("Error in button demo: {}".format(e=e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoButtonDemo()
    demo.run()
