# Import basic preliminaries
import time

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication

# Import the device we will be using
from sic_framework.devices.alphamini import Alphamini
from mini import MouthLampColor, MouthLampMode
from pathlib import Path
from dotenv import load_dotenv


class AlphaminiMouthLampDemo(SICApplication):
    """
    Alphamini mouth lamp demo application.

    Demonstrates normal and breath mouth lamp modes.
    """

    def __init__(self):
        super(AlphaminiMouthLampDemo, self).__init__()

        self.mini = None
        self.mini_ip = "XXX"
        self.mini_id = "000XXX"
        self.mini_password = "XXX"
        self.redis_ip = "XXX"

        self.set_log_level(sic_logging.INFO)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/path/to/logs")


        # Load environment variables
        env_path = Path(__file__).parent.parent.parent / "conf" / ".env"
        load_dotenv(env_path)
        
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

        Useful references:
        - Colors: mini.MouthLampColor (RED, GREEN, WHITE)
        - Modes: mini.MouthLampMode (NORMAL, BREATH)
        - The control call used is Alphamini.set_mouth_lamp(...)
        """
        try:
            self.logger.info("Mouth lamp: GREEN NORMAL for 3 seconds")
            self.mini.set_mouth_lamp(
                color=MouthLampColor.GREEN,
                mode=MouthLampMode.NORMAL,
                duration=3000,
            )
            time.sleep(3)

            self.logger.info("Mouth lamp: WHITE BREATH for 5 seconds")
            self.mini.set_mouth_lamp(
                color=MouthLampColor.WHITE,
                mode=MouthLampMode.BREATH,
                breath_duration=1000,
            )
            time.sleep(5)

            self.logger.info("Mouth lamp demo completed successfully")
        except Exception as e:
            self.logger.error("Exception: %s", e)
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = AlphaminiMouthLampDemo()
    demo.run()
