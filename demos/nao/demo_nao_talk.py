# Import basic preliminaries
# Import libraries necessary for the demo
from time import sleep

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication

# Import the device(s) we will be using
from sic_framework.devices import Nao

# Import message types and requests
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoRestRequest,
    NaoWakeUpRequest,
)
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import (
    NaoqiTextToSpeechRequest,
)


class NaoTalkDemo(SICApplication):
    """
    NAO text-to-speech demo application.
    Demonstrates how to use the NAO TTS to say something with different options.
    """

    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(NaoTalkDemo, self).__init__()

        # Demo-specific initialization
        self.nao_ip = "XXX"
        self.nao = None

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file_path("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/nao/logs")

        self.set_log_level(sic_logging.INFO)


        # Load environment variables
        self.load_env("../../conf/.env")
        
        self.setup()

    def setup(self):
        """Initialize and configure the NAO robot."""
        self.logger.info("Initializing NAO...")

        # Initialize the NAO robot
        self.nao = Nao(ip=self.nao_ip)

    def say(self):
        """Make NAO say something using TTS."""
        self.nao.tts.request(NaoqiTextToSpeechRequest("Say."))
        self.nao.tts.request(NaoqiTextToSpeechRequest("Hello, I am a Nao robot!"))

    def say_animated(self):
        """Make NAO say something with animated gestures."""
        self.nao.tts.request(NaoqiTextToSpeechRequest("Animated Say."))
        self.nao.tts.request(
            NaoqiTextToSpeechRequest(
                "Hello, I am a Nao robot! And I like to chat.", animated=True
            )
        )

    def say_with_gesture(self):
        """Make NAO say something while performing a gesture."""
        self.nao.tts.request(NaoqiTextToSpeechRequest("Say and gesture."))
        self.nao.tts.request(
            NaoqiTextToSpeechRequest("Hello, I am a Nao robot! And I like to chat."),
            block=False,
        )
        self.nao.motion.request(
            NaoqiAnimationRequest("animations/Stand/Gestures/Hey_1")
        )

    def wakeup(self):
        """Wake up the NAO robot."""
        self.nao.autonomous.request(NaoWakeUpRequest())

    def rest(self):
        """Put the NAO robot to rest."""
        self.nao.autonomous.request(NaoRestRequest())

    def run(self):
        """Main application logic."""
        self.logger.info("Starting NAO Talk Demo...")
        try:
            self.wakeup()
            # self.nao.tts.request(NaoqiTextToSpeechRequest("Hello, I am a Nao robot!"))
            self.say()
            sleep(2)
            self.say_animated()
            sleep(2)
            self.say_with_gesture()
            sleep(2)
            self.rest()
            self.logger.info("Demo completed successfully")
        except Exception as e:
            self.logger.error("Error in demo: {}".format(e=e))
        finally:
            self.logger.info("Shutting down application")
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoTalkDemo()
    demo.run()
