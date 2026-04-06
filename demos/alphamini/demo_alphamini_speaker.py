# Import preliminaries
import wave
from os.path import abspath, dirname, join

# import basic SIC framework libraries
from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication

# import device(s) and services, and message types we will be using
from sic_framework.devices.alphamini import Alphamini
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.devices.common_mini.mini_speaker import MiniSpeakersConf


class AlphaminiSpeakerWavDemo(SICApplication):
    """
    Alphamini speaker demo application.

    Plays a local WAV file (``sic_applications/demos/_media/test_sound.wav``)
    through the Alphamini speakers using the MiniSpeaker component.

    NOTE: the sample rate of the speaker must match the sample rate of the audio from the WAV file.
    """

    def __init__(self):
        super(AlphaminiSpeakerWavDemo, self).__init__()

        # Demo-specific initialization
        self.mini_ip = "XXX"
        self.mini_id = "000XXX"
        self.mini_password = "XXX"
        self.redis_ip = "XXX"
        self.mini = None

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file_path("/path/to/logs")

        self.set_log_level(sic_logging.INFO)

        # Load environment variables
        self.load_env("../../conf/.env")

    def _load_wav(self):
        """
        Load the test WAV file and return (waveform_bytes, sample_rate).

        The file is expected at ``sic_applications/demos/_media/test_sound.wav``
        relative to this script.
        """
        base_dir = dirname(dirname(__file__))
        wav_path = abspath(join(base_dir, "_media", "test_sound.wav"))

        with wave.open(wav_path, "rb") as wf:
            sample_rate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())

        return frames, sample_rate

    def run(self):
        """Main application logic."""
        try:
            waveform, sample_rate = self._load_wav()

            self.logger.info("Initializing Alphamini...")
            self.mini = Alphamini(
                ip=self.mini_ip,
                mini_id=self.mini_id,
                mini_password=self.mini_password,
                redis_ip=self.redis_ip,
                speaker_conf=MiniSpeakersConf(sample_rate=sample_rate),
            )

            self.logger.info("Playing WAV file on Alphamini speakers...")
            self.mini.speaker.request(AudioRequest(waveform, sample_rate))

            self.logger.info("Speaker WAV demo completed successfully")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = AlphaminiSpeakerWavDemo()
    demo.run()
