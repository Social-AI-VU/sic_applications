# Import basic SIC framework modules
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s), service(s), and message(s) we will be using
from sic_framework.devices.alphamini import Alphamini
from sic_framework.devices.common_mini.mini_speaker import MiniSpeakersConf
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.services.elevenlabs_tts.elevenlabs_tts import (
    ElevenLabsTTS, 
    ElevenLabsTTSConf, 
    GetElevenLabsSpeechRequest
    )

# import demo-specific modules
from os.path import abspath, dirname, join
from dotenv import load_dotenv
import os


class AlphaminiElevenLabsTTSDemo(SICApplication):
    """
    Alphamini ElevenLabs Text-to-Speech demo application.
    Demonstrates how to use the ElevenLabs TTS service to have the Alphamini
    speak.

    Requirements:
    1. ElevenLabs TTS service must be installed and running
    2. ELEVENLABS_API_KEY must be set in the environment,
       or passed directly via the api_key constructor argument
    """

    def __init__(self, api_key=None, mode="batch"):
        super(AlphaminiElevenLabsTTSDemo, self).__init__()

        # Update these values for your setup.
        self.mini_ip = "XXX"
        self.mini_id = "000XXX"
        self.mini_password = "XXX"
        self.redis_ip = "XXX"

        self.mini = None
        self.tts = None
        self._provided_api_key = api_key
        self.mode = mode

        self.set_log_level(sic_logging.INFO)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file_path("/path/to/log/directory")

        # Load environment variables
        self.load_env("../../conf/.env")
        
        self.setup()

    def setup(self):
        self.logger.info("Setting up ElevenLabs Text-to-Speech...")

        load_dotenv(
            abspath(join(dirname(__file__), "..", "..", "conf", ".env"))
        )
        self.api_key = (
            self._provided_api_key or os.getenv("ELEVENLABS_API_KEY")
        )

        if not self.api_key:
            raise ValueError(
                "No ElevenLabs API key found. Set ELEVENLABS_API_KEY."
            )

        tts_conf = ElevenLabsTTSConf(
            api_key=self.api_key,
            default_mode=self.mode,
            # optional overrides:
            # voice_id="yO6w2xlECAQRFP6pX7Hw",
            # model_id="eleven_flash_v2_5",
            # sample_rate=22050,
        )
        self.tts = ElevenLabsTTS(conf=tts_conf)

    def run(self):
        self.logger.info("Starting Alphamini ElevenLabs TTS Demo")

        try:
            reply = self.tts.request(
                GetElevenLabsSpeechRequest(
                    text=(
                        "Hello, I am an Alphamini robot testing the"
                        " ElevenLabs text to speech service in Social"
                        " Interaction Cloud. This is a slightly longer"
                        " example so we can check whether the full audio"
                        " plays correctly from beginning to end. If"
                        " everything is working well, there should be no"
                        " truncation, no missing words, and the voice"
                        " should sound natural."
                    ),
                    mode="batch",
                )
            )

            self.logger.info("Initializing Alphamini...")
            self.mini = Alphamini(
                ip=self.mini_ip,
                mini_id=self.mini_id,
                mini_password=self.mini_password,
                redis_ip=self.redis_ip,
                speaker_conf=MiniSpeakersConf(sample_rate=reply.sample_rate),
            )

            self.logger.info("Alphamini speaking...")
            self.mini.speaker.request(
                AudioRequest(reply.waveform, reply.sample_rate)
            )

            self.logger.info("Speech playback completed")

        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = AlphaminiElevenLabsTTSDemo(mode="ws")
    demo.run()
