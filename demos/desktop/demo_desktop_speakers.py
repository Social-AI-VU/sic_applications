# import basic SIC framework components
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# import devices, messages, and services we will be using
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.devices.desktop import Desktop

# import demo-specific modules
from os.path import abspath, dirname, join
import wave


class DesktopSpeakersDemo(SICApplication):
    """
    Play a sample WAV file through desktop speakers.
    """

    def __init__(self):
        super(DesktopSpeakersDemo, self).__init__()

        app_root = dirname(dirname(dirname(__file__)))
        self.audio_file = abspath(
            join(app_root, "example_media", "audio", "demo_audio.wav")
        )
        self.desktop = None
        self.wavefile = None
        self.sample_rate = None

        self.set_log_level(sic_logging.INFO)
        
        # self.set_log_file_path("/path/to/log/directory")

        self.load_env("../../conf/.env")
        
        self.setup()

    def setup(self):
        self.logger.info("Loading WAV file: %s", self.audio_file)
        self.wavefile = wave.open(self.audio_file, "rb")
        self.sample_rate = self.wavefile.getframerate()

        self.desktop = Desktop(
            speakers_conf=SpeakersConf(sample_rate=self.sample_rate)
        )

    def run(self):
        try:
            waveform = self.wavefile.readframes(self.wavefile.getnframes())
            self.desktop.speakers.request(
                AudioRequest(waveform=waveform, sample_rate=self.sample_rate)
            )
            self.logger.info("Playback finished")
        except Exception as e:
            self.logger.error("Playback failed: %s", e)
        finally:
            if self.wavefile:
                self.wavefile.close()
            self.shutdown()


if __name__ == "__main__":
    demo = DesktopSpeakersDemo()
    demo.run()