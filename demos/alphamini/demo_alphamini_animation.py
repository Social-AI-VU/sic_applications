# Import basic preliminaries
import time

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication

# Import the device we will be using
from sic_framework.devices.alphamini import Alphamini, SDKAnimationType


class AlphaminiAnimationDemo(SICApplication):
    """
    Alphamini animation demo application.

    This demo uses the unified animate(...) API for both body actions and
    eye expressions.

    Built-in action/emoticon reference:
    https://docs.ubtrobot.com/alphamini/python-sdk-en/additional.html#
    """

    def __init__(self):
        super(AlphaminiAnimationDemo, self).__init__()

        self.mini = None
        self.mini_ip = "XXX"
        self.mini_id = "000XXX"
        self.mini_password = "XXX"
        self.redis_ip = "XXX"

        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file_path("/path/to/logs")
        

        # Load environment variables
        self.load_env("../../conf/.env")
        
        self.setup()


    def setup(self):
        """Initialize and configure the Alphamini robot."""
        self.logger.info("Initializing Alphamini...")
        self.mini = Alphamini(
            ip=self.mini_ip,
            mini_id=self.mini_id,
            mini_password=self.mini_password,
            redis_ip=self.redis_ip,
        )

    def run(self):
        """
        Main application logic.

        Available built-in actions/emoticons are documented here:
        https://docs.ubtrobot.com/alphamini/python-sdk-en/additional.html#
        """
        try:
            self.logger.info("Playing blinking expression...")
            self.mini.animate(SDKAnimationType.EXPRESSION, "codemao20")
            time.sleep(5)

            self.logger.info("Playing raise right leg action...")
            self.mini.animate(SDKAnimationType.ACTION, "018")
            time.sleep(5)

            self.logger.info("Playing dance...")
            self.mini.animate(SDKAnimationType.ACTION, "dance_0007en")
            time.sleep(5)

            self.logger.info("Animation demo completed successfully")
        except Exception as e:
            self.logger.error("Exception: %s", e)
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = AlphaminiAnimationDemo()
    demo.run()
