# Import preliminaries
import json
import time
from os.path import abspath, join
from pathlib import Path
from dotenv import load_dotenv

# import basic SIC framework libraries
from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication

# import device and services we will be using
from sic_framework.devices.alphamini import Alphamini
from sic_framework.services.google_stt.google_stt import (
    GetStatementRequest,
    GoogleSpeechToText,
    GoogleSpeechToTextConf,
)


class AlphaminiGoogleSTTDemo(SICApplication):
    """
    Alphamini microphone -> Google Speech-to-Text demo.

    This demo continuously listens to the Alphamini microphone stream and prints
    transcriptions in a loop.

    Prerequisites:
    1. Install dependency: pip install social-interaction-cloud[alphamini,google-stt]
    2. Start service: run-google-stt
    3. Put Google key at: conf/google/google-key.json
    """

    def __init__(self):
        super(AlphaminiGoogleSTTDemo, self).__init__()

        # Update these values for your setup.
        self.mini_ip = "XXX"
        self.mini_id = "000XXX"
        self.mini_password = "XXX"
        self.redis_ip = "XXX"
        self.google_keyfile_path = abspath(
            join("..", "..", "conf", "google", "google-key.json")
        )

        self.mini = None
        self.stt = None

        self.set_log_level(sic_logging.INFO)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/path/to/logs")
        

        # Load environment variables
        env_path = Path(__file__).parent.parent.parent / "conf" / ".env"
        load_dotenv(env_path)
        
        self.setup()

    def on_stt(self, result):
        """
        Callback for interim Google STT results.
        """
        if hasattr(result.response, "alternatives") and result.response.alternatives:
            transcript = result.response.alternatives[0].transcript
            self.logger.info("Interim: {}".format(transcript))

    def setup(self):
        self.logger.info("Setting up Alphamini Google STT demo...")

        self.mini = Alphamini(
            ip=self.mini_ip,
            mini_id=self.mini_id,
            mini_password=self.mini_password,
            redis_ip=self.redis_ip,
        )

        stt_conf = GoogleSpeechToTextConf(
            keyfile_json=json.load(open(self.google_keyfile_path)),
            sample_rate_hertz=44100,
            language="en-US",
            interim_results=False,
        )
        self.stt = GoogleSpeechToText(conf=stt_conf, input_source=self.mini.mic)
        self.stt.register_callback(callback=self.on_stt)

        self.logger.info(" -- Ready: listening for speech -- ")

    def run(self):
        try:
            while not self.shutdown_event.is_set():
                result = self.stt.request(GetStatementRequest())
                if (
                    not result
                    or not hasattr(result.response, "alternatives")
                    or not result.response.alternatives
                ):
                    self.logger.info("No transcript received")
                    continue

                transcript = result.response.alternatives[0].transcript
                self.logger.info("Transcript: {}".format(transcript))
                time.sleep(0.1)
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = AlphaminiGoogleSTTDemo()
    demo.run()
