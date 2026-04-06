# import libraries for the demo
import json
from os.path import abspath, join, dirname

# import SIC framework components
from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication

# import devices, services, and message types
from sic_framework.devices.reachy_mini import ReachyMiniDevice
from sic_framework.devices.common_reachy_mini.reachy_mini_speakers import ReachyMiniSpeakersConf
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.services.google_tts.google_tts import (
    GetSpeechRequest,
    Text2Speech,
    Text2SpeechConf,
)

class ReachyMiniGoogleTTSDemo(SICApplication):
    """
    Reachy Mini Google Text-to-Speech demo.

    Demonstrates how to use the Google Text2Speech service to have the
    Reachy Mini speak through its built-in speaker.

    IMPORTANT:
    Google text-to-speech dependency needs to be installed and the service needs to be running:
    1. pip install --upgrade social-interaction-cloud[google-tts]
    2. run-google-tts (in a separate terminal)

    NOTE: you need to have setup Cloud Text-to-Speech API in your Google Cloud Console
    and configure the credential keyfile.
    See https://social-ai-vu.github.io/social-interaction-cloud/external_apis/google_cloud.html
    Save the file in conf/google/google-key.json
    """

    def __init__(self, google_keyfile_path):
        super(ReachyMiniGoogleTTSDemo, self).__init__()

        self.google_keyfile_path = google_keyfile_path
        self.mini = None
        self.tts = None

        self.set_log_level(sic_logging.INFO)
        # set log file path if needed
        # self.set_log_file_path("/path/to/logs")


        # Load environment variables
        self.load_env("../../conf/.env")
        
        self.setup()

    def setup(self):
        """Initialize the Google TTS service."""
        self.logger.info("Setting up Google Text-to-Speech...")

        tts_conf = Text2SpeechConf(
            keyfile_json=json.load(open(self.google_keyfile_path))
        )
        self.tts = Text2Speech(conf=tts_conf)

    def run(self):
        """Main application logic."""
        try:
            # Get speech from Google TTS
            reply = self.tts.request(
                GetSpeechRequest(
                    text="Hi, I am Reachy Mini",
                    voice_name="en-US-Standard-C",
                )
            )

            # Initialize device with matching sample rate
            self.mini = ReachyMiniDevice(
                mode="sim",
                speakers_conf=ReachyMiniSpeakersConf(sample_rate=reply.sample_rate)
            )

            self.logger.info("Playing speech through Reachy Mini speaker...")
            self.mini.speakers.request(AudioRequest(reply.waveform, reply.sample_rate))

            self.logger.info("TTS demo completed")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = ReachyMiniGoogleTTSDemo(
        google_keyfile_path=abspath(
            join(dirname(__file__), "..", "..", "conf", "google", "google-key.json")
        )
    )
    demo.run()
