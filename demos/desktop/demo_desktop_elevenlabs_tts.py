import os

from sic_framework.core import sic_logging
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.core.sic_application import SICApplication

from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.devices.desktop import Desktop

from sic_framework.services.elevenlabs_tts.elevenlabs_tts import (
    ElevenLabsTTS,
    ElevenLabsTTSConf,
    GetElevenLabsSpeechRequest,
    ElevenLabsSpeechResult,
)


class ElevenLabsTTSDemo(SICApplication):
    """
    ElevenLabs Text-to-Speech demo application.

    Requirements:
    1. ElevenLabs TTS service must be installed and running
    2. ELEVENLABS_API_KEY must be set in the environment,
       or passed directly in ElevenLabsTTSConf
    """

    def __init__(self, api_key=None, mode="batch"):
        super(ElevenLabsTTSDemo, self).__init__()

        self.desktop = None
        self.tts = None
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.mode = mode

        self.set_log_level(sic_logging.INFO)
        self.setup()

    def setup(self):
        self.logger.info("Setting up ElevenLabs Text-to-Speech...")

        if not self.api_key:
            raise ValueError("No ElevenLabs API key found. Set ELEVENLABS_API_KEY.")

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
        self.logger.info("Starting ElevenLabs TTS Demo")

        try:
            reply = self.tts.request(
                GetElevenLabsSpeechRequest(
                    text="Hello, I am testing the ElevenLabs text to speech service in Social Interaction Cloud. This is a slightly longer example so we can check whether the full audio plays correctly from beginning to end. If everything is working well, there should be no truncation, no missing words, and the voice should sound natural.",
                    mode=self.mode,
                )
            )

            self.desktop = Desktop(
                speakers_conf=SpeakersConf(sample_rate=reply.sample_rate)
            )

            self.desktop.speakers.request(
                AudioRequest(reply.waveform, reply.sample_rate)
            )

            self.logger.info("Speech playback completed")

        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = ElevenLabsTTSDemo(mode="ws")
    demo.run()