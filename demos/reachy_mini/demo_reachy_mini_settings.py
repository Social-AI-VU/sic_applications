import requests

# import basic SIC framework components
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# import device(s), service(s), and message(s) we will be using
from sic_framework.devices.reachy_mini import ReachyMiniDevice

class ReachyMiniSettings(SICApplication):
    """
    Reachy Mini settings.

    Setting the volume:
    Call demo.set_volume(volume)

    Putting the Reachy Mini back in rest position:
    Call demo.rest()
    """

    def __init__(self):
        super(ReachyMiniSettings, self).__init__()

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
        self.logger.info("Initializing Reachy Mini for motion demo...")
        self.mini = ReachyMiniDevice(mode="wireless", robot_ip=self.mini_ip)

    def set_volume(self, volume):
        """Set the output volume (0-100) of the Reachy Mini."""
        response = requests.post(
            "http://{}:8000/api/volume/set".format(self.mini_ip),
            json={"volume": volume},
            timeout=10,
        )
        response.raise_for_status()
        self.logger.info("Volume set to {}".format(response.json()["volume"]))

    def rest(self):
        self.mini.rest()


if __name__ == "__main__":
    demo = ReachyMiniSettings()
    demo.set_volume(100)
    demo.rest()
