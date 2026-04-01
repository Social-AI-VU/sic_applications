# import SIC framework components
from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication

# import devices, services, and message types
from sic_framework.devices.reachy_mini import ReachyMiniDevice
from sic_framework.devices.common_reachy_mini.reachy_mini_motion import (
    ReachyMiniAntennaRequest,
    ReachyMiniBodyYawRequest,
    ReachyMiniHeadRequest,
)


class ReachyMiniMotionDemo(SICApplication):
    """
    Reachy Mini motion demo.

    Demonstrates head, antenna, and body yaw movements.
    """

    def __init__(self):
        super(ReachyMiniMotionDemo, self).__init__()

        self.mini = None

        self.set_log_level(sic_logging.INFO)
        # set log file path if needed
        # self.set_log_file("/path/to/logs")

        self.setup()

    def setup(self):
        """Initialize the Reachy Mini device."""
        self.logger.info("Initializing Reachy Mini for motion demo...")
        self.mini = ReachyMiniDevice(mode="sim")

    def run(self):
        """Main application logic."""
        try:
            # Antenna wave (goto_target blocks for the duration)
            self.logger.info("Waving antennas")
            self.mini.motion.request(ReachyMiniAntennaRequest(right=0.5, left=-0.5, duration=0.5))
            self.mini.motion.request(ReachyMiniAntennaRequest(right=-0.5, left=0.5, duration=0.5))
            self.mini.motion.request(ReachyMiniAntennaRequest(right=0, left=0, duration=0.5))

            # Head nod
            self.logger.info("Nodding head")
            self.mini.motion.request(ReachyMiniHeadRequest(z=10, duration=0.5, mm=True))
            self.mini.motion.request(ReachyMiniHeadRequest(z=-10, duration=0.5, mm=True))
            self.mini.motion.request(ReachyMiniHeadRequest(z=0, duration=0.5, mm=True))

            # Body rotation
            self.logger.info("Rotating body")
            self.mini.motion.request(ReachyMiniBodyYawRequest(yaw=0.5, duration=1.0))
            self.mini.motion.request(ReachyMiniBodyYawRequest(yaw=-0.5, duration=1.0))
            self.mini.motion.request(ReachyMiniBodyYawRequest(yaw=0, duration=1.0))

            self.logger.info("Motion demo complete")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = ReachyMiniMotionDemo()
    demo.run()
