# import basic SIC framework components
from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication

# Import the device(s), service(s), and message(s) we will be using
from sic_framework.devices.franka import Franka
from sic_framework.devices.common_franka.franka_motion_recorder import GoHomeRequest


class FrankaGoHomeDemo(SICApplication):
    """Minimal demo that sends the Franka arm to home once."""

    def __init__(self):
        super(FrankaGoHomeDemo, self).__init__()
        self.set_log_level(sic_logging.INFO)
        self.load_env("../../conf/.env")
        self.franka = Franka()

    def run(self):
        try:
            self.logger.info("Sending GoHomeRequest to Franka arm")
            self.franka.motion_recorder.request(GoHomeRequest())
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = FrankaGoHomeDemo()
    demo.run()
