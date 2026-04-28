# import basic SIC framework modules
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# import device(s), service(s), and message(s) we will be using
from sic_framework.devices.reachy_mini import ReachyMiniDevice
from sic_framework.services.openai_whisper_stt.whisper_stt import (
    GetTranscript,
    SICWhisper,
    Transcript,
    WhisperConf,
)

# import demo-specific modules
from os.path import abspath, join
from os import environ
import time


class ReachyMiniWhisperDemo(SICApplication):
    """
    Reachy Mini microphone with Whisper speech-to-text.

    IMPORTANT:
    1. Whisper service needs to be running:
    pip install --upgrade social-interaction-cloud[whisper-speech-to-text]
    run-whisper
    2. An OpenAI API key must be set in conf/.env as OPENAI_API_KEY="your key".
    """

    def __init__(self):
        super(ReachyMiniWhisperDemo, self).__init__()

        self.mini = None
        self.whisper = None
        
        self.set_log_level(sic_logging.INFO)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file_path("/path/to/log/directory")
        
        # Load environment variables
        self.load_env("../../conf/.env")

        self.setup()

    def on_transcript(self, message: Transcript):
        print(message.transcript)

    def setup(self):
        """Initialize the Reachy Mini device and Whisper service."""
        self.logger.info("Setting up Whisper speech-to-text...")

        self.mini = ReachyMiniDevice(mode="sim")

        whisper_conf = WhisperConf(openai_key=environ["OPENAI_API_KEY"])
        self.whisper = SICWhisper(input_source=self.mini.mic, conf=whisper_conf)

        time.sleep(1)

        self.whisper.register_callback(self.on_transcript)

    def run(self):
        """Main application loop."""
        self.logger.info("Starting Whisper demo")

        try:
            while not self.shutdown_event.is_set():
                self.logger.info("Talk now!")
                transcript = self.whisper.request(
                    GetTranscript(timeout=10, phrase_time_limit=30)
                )
                self.logger.info(
                    "transcript: {transcript}".format(transcript=transcript.transcript)
                )
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = ReachyMiniWhisperDemo()
    demo.run()
