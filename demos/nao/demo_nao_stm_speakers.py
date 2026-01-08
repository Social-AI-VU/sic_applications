# Import basic preliminaries
# Import libraries necessary for the demo
import wave

import numpy as np

from sic_framework.core import sic_logging
# Import message types
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.core.sic_application import SICApplication
# Import the device(s) we will be using
from sic_framework.devices import Nao


class NaoSpeakersDemo(SICApplication):
    """
    NAO speakers demo application.
    Demonstrates how to use the NAO robot speakers to play a wav file.
    """
    
    def __init__(self):
        super(NaoSpeakersDemo, self).__init__()
        
        self.nao_ip = "10.15.3.234"
        self.audio_file = "sample.wav"
        self.nao = None
        self.wavefile = None
        self.samplerate = None
        self.channels = None  # mono / stereo
        
        self.set_log_level(sic_logging.DEBUG)
        self.setup()

    @staticmethod
    def mono_to_stereo(pcm_mono: bytes) -> bytes:
        """Convert 16-bit mono PCM bytes to 16-bit stereo (L=R) PCM bytes."""
        samples = np.frombuffer(pcm_mono, dtype=np.int16)    # shape (N,)
        stereo = np.repeat(samples[:, None], 2, axis=1)      # shape (N, 2)
        return stereo.astype(np.int16).tobytes()             # interleaved L,R,...

    def setup(self):
        """Initialize and configure the NAO robot and load audio file."""
        self.logger.info("Starting NAO Speakers Demo...")
        
        # Read the wav file
        self.wavefile = wave.open(self.audio_file, "rb")
        self.samplerate = self.wavefile.getframerate()
        self.channels = self.wavefile.getnchannels()

        # Basic sanity check: NAO expects 16-bit PCM
        if self.wavefile.getsampwidth() != 2:
            raise ValueError("Only 16-bit PCM WAV files are supported")

        self.logger.info("Audio file specs:")
        self.logger.info("  sample rate: {}".format(self.wavefile.getframerate()))
        self.logger.info("  length (frames): {}".format(self.wavefile.getnframes()))
        self.logger.info("  sample width (bytes): {}".format(self.wavefile.getsampwidth()))
        self.logger.info("  number of channels: {}".format(self.channels))
        self.logger.info("")
        
        # Initialize the NAO robot
        self.nao = Nao(ip=self.nao_ip, dev_test=True, test_repo="/home/sandergs/Documents/sic_dev/social-interaction-cloud")
    
    def run(self):
        """Main application logic: stream WAV in chunks."""
        try:
            self.logger.info("Sending audio in chunks!")
            
            MAX_FRAMES_PER_CHUNK = int(16384 / 4)  # max frames per chunk
            self.wavefile.rewind()

            while True:
                # Read up to MAX_FRAMES_PER_CHUNK frames from the WAV
                chunk = self.wavefile.readframes(MAX_FRAMES_PER_CHUNK)
                if not chunk:
                    break  # end of file

                self.logger.info("chunk length: %d, type: %s", len(chunk), type(chunk))

                # If file is mono, convert this chunk to stereo
                if self.channels == 1:
                    chunk = self.mono_to_stereo(chunk)

                self.logger.info("chunk length: %d, type: %s", len(chunk), type(chunk))

                # Create and send AudioRequest for this chunk
                message = AudioRequest(
                    sample_rate=self.samplerate,
                    waveform=chunk,  # 16-bit stereo PCM bytes
                    is_stream=True
                )
                self.nao.speaker.request(message)

            self.logger.info("All audio chunks sent (not waiting for playback to finish).")
            self.logger.info("Speakers demo completed successfully")

        except Exception as e:
            self.logger.error("Error in speakers demo: {}".format(e))
        finally:
            if self.wavefile:
                self.wavefile.close()
            self.logger.info("Shutting down application")
            self.shutdown()


if __name__ == "__main__":
    demo = NaoSpeakersDemo()
    demo.run()
