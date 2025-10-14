# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao
from sic_framework.devices.nao_stub import NaoStub

# Import message types
from sic_framework.core.message_python2 import AudioRequest

# Import libraries necessary for the demo
import wave


class NaoSpeakersDemo(SICApplication):
    """
    NAO speakers demo application.
    Demonstrates how to use the NAO robot speakers to play a wav file.
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(NaoSpeakersDemo, self).__init__()
        
        # Demo-specific initialization
        self.nao_ip = "XXX"
        self.audio_file = "test_sound.wav"
        self.nao = None
        self.wavefile = None
        self.samplerate = None
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/nao/logs")

        self.set_log_level(sic_logging.INFO)
        
        self.setup()
    
    def setup(self):
        """Initialize and configure the NAO robot and load audio file."""
        self.logger.info("Starting NAO Speakers Demo...")
        
        # Read the wav file
        self.wavefile = wave.open(self.audio_file, "rb")
        self.samplerate = self.wavefile.getframerate()
        
        self.logger.info("Audio file specs:")
        self.logger.info("  sample rate: {}".format(self.wavefile.getframerate()))
        self.logger.info("  length: {}".format(self.wavefile.getnframes()))
        self.logger.info("  data size in bytes: {}".format(self.wavefile.getsampwidth()))
        self.logger.info("  number of channels: {}".format(self.wavefile.getnchannels()))
        self.logger.info("")
        
        # Initialize the NAO robot
        self.nao = Nao(ip=self.nao_ip)
    
    def run(self):
        """Main application logic."""
        try:
            self.logger.info("Sending audio!")
            sound = self.wavefile.readframes(self.wavefile.getnframes())
            message = AudioRequest(sample_rate=self.samplerate, waveform=sound)
            self.nao.speaker.request(message)

            self.logger.info("Audio sent, without waiting for it to complete playing.")
            self.logger.info("Speakers demo completed successfully")
        except Exception as e:
            self.logger.error("Error in speakers demo: {}".format(e=e))
        finally:
            if self.wavefile:
                self.wavefile.close()
            self.logger.info("Shutting down application")
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoSpeakersDemo()
    demo.run()
