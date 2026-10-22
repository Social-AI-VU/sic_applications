# import basic SIC framework components
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# import device(s), service(s), and message(s) we will be using
from sic_framework.devices.reachy_mini import ReachyMiniDevice
from sic_framework.devices.common_reachy_mini.reachy_mini_motion import (
    ReachyMiniAnimationRequest,
    ReachyMiniGetAnimationsRequest,
    ReachyMiniHeadRequest,
)

# import demo-specific modules
import time


class ReachyMiniAnimationsDemo(SICApplication):
    """
    Reachy Mini emotions and dances demo.

    Plays recorded animations by name:

    - a short name (e.g. "cheerful1") is searched in all libraries
    - a full name (e.g. "dances/simple_nod") is taken from that library

    The animations come from Pollen's emotions and dances libraries on
    Hugging Face; they are downloaded the first time and cached afterwards.
    """

    def __init__(self):
        super(ReachyMiniAnimationsDemo, self).__init__()

        self.mini = None
        self.mini_ip = "XXX"

        self.set_log_level(sic_logging.INFO)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file_path("/path/to/log/directory")

        # Load environment variables
        self.load_env("../../conf/.env")

        self.setup()

    def setup(self):
        """Initialize the Reachy Mini device."""
        self.logger.info("Initializing Reachy Mini for animations demo...")
        self.mini = ReachyMiniDevice(mode="wireless", robot_ip=self.mini_ip)

    def animate(self, name, sound=True):
        """Play an animation; blocks until it has finished."""
        self.logger.info("Playing '{}'{}".format(name, "" if sound else " (no sound)"))
        self.mini.motion.request(ReachyMiniAnimationRequest(name, sound=sound))

    def list_animations(self):
        """Log all available animations per library."""
        # The first call can take a while: the libraries are downloaded once
        reply = self.mini.motion.request(ReachyMiniGetAnimationsRequest(), timeout=300)
        for library, names in reply.animations.items():
            self.logger.info("{} ({}): {}".format(library, len(names), ", ".join(names)))
        return reply.animations

    def tour(self):
        """Guided tour of the animation features."""
        self.logger.info("--- Emotions by short name (with their sound)")
        for name in ["cheerful1", "curious1", "sad1", "surprised1"]:
            self.animate(name)
            time.sleep(1)

        self.logger.info("--- Dances by full name")
        for name in ["dances/simple_nod", "dances/side_to_side_sway"]:
            self.animate(name)
            time.sleep(1)

        self.logger.info("--- An emotion without its sound")
        self.animate("emotions/yes1", sound=False)
        time.sleep(1)

        self.logger.info("--- Animations return to where the head was: look left, then laugh")
        self.mini.motion.request(ReachyMiniHeadRequest(yaw=25, duration=1.0))
        time.sleep(1)
        self.animate("laughing1")
        self.logger.info("The head should be looking left again")
        time.sleep(3)

        self.logger.info("--- Any motion request interrupts an animation smoothly")
        self.mini.motion.request(ReachyMiniAnimationRequest("dances/groovy_sway_and_roll"), block=False)
        time.sleep(2.5)
        self.mini.motion.request(ReachyMiniHeadRequest(duration=1.0))
        self.logger.info("Dance interrupted, head back at neutral")
        time.sleep(3)

    def play_all(self, sound=True, pause=1.0):
        """Play every available animation, library by library."""
        reply = self.mini.motion.request(ReachyMiniGetAnimationsRequest(), timeout=300)

        total = sum(len(names) for names in reply.animations.values())
        count = 0
        for library, names in reply.animations.items():
            self.logger.info("--- {} ({} animations)".format(library, len(names)))
            for name in names:
                count += 1
                self.logger.info("[{}/{}] {}/{}".format(count, total, library, name))
                self.mini.motion.request(ReachyMiniAnimationRequest("{}/{}".format(library, name), sound=sound))
                time.sleep(pause)

    def run(self):
        """Main application logic."""
        try:
            self.list_animations()
            self.tour()
            # self.play_all()
            self.logger.info("Animations demo complete")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = ReachyMiniAnimationsDemo()
    demo.run()
