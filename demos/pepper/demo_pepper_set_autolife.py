# Import basic preliminaries
import argparse

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication

# Import the device(s) we will be using
from sic_framework.devices import Pepper

# Import message types and requests
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoSetAutonomousLifeRequest,
)


class PepperAutonomousLifeDemo(SICApplication):
    """
    Simple SIC demo that toggles Pepper's Autonomous Life module.
    """

    def __init__(
        self,
        robot_ip,
        life_mode,
    ):
        super(PepperAutonomousLifeDemo, self).__init__()

        self.pepper = None
        self.robot_ip = robot_ip
        self.life_mode = life_mode

        self.set_log_level(sic_logging.INFO)
        self.setup()

    def setup(self):
        """Initialize the Pepper device."""
        self.logger.info("Connecting to Pepper")
        self.pepper = Pepper(ip=self.robot_ip, dev_test=True)
        self.logger.info("Pepper connected successfully.")

    def run(self):
        """Send the Autonomous Life request."""
        try:
            self.logger.info("Setting Autonomous Life to %s.", self.life_mode)
            self.pepper.autonomous.request(
                NaoSetAutonomousLifeRequest(state=self.life_mode)
            )
            self.logger.info("Autonomous Life set to %s successfully.", self.life_mode)
        except Exception as exc:
            self.logger.error(
                "Failed to set Autonomous Life to %s: %s", self.life_mode, exc
            )
            raise
        finally:
            self.shutdown()

    def shutdown(self):
        """Stop SIC on Pepper unless instructed to keep running."""
        try:
            self.logger.info("Stopping SIC on Pepper...")
            self.pepper.stop_device()
            self.logger.info("Pepper stopped successfully.")
        except Exception as exc:
            self.logger.warning("Failed to stop Pepper cleanly: %s", exc)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Pepper Autonomous Life Demo")
    parser.add_argument("--robot-ip", type=str, required=True, help="Pepper IP address")
    parser.add_argument(
        "--life-mode",
        type=str,
        default="disabled",
        choices=["solitary", "interactive", "safeguard", "disabled"],
        help="Mode to run the demo",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    demo = PepperAutonomousLifeDemo(robot_ip=args.robot_ip, life_mode=args.life_mode)
    demo.run()
