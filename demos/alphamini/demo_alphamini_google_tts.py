# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.alphamini import Alphamini

# Import the service(s) we will be using
from sic_framework.services.google_tts.google_tts import (
    Text2Speech,
    Text2SpeechConf,
    GetSpeechRequest,
    SpeechResult
)

# Import configuration and message types
from sic_framework.devices.common_mini.mini_speaker import MiniSpeakersConf
from sic_framework.core.message_python2 import AudioRequest

# Import libraries necessary for the demo
from os.path import abspath, join
import json


class AlphaminiGoogleTTSDemo(SICApplication):
    """
    Alphamini Google Text-to-Speech demo application.
    Demonstrates how to use the Google Text2Speech service to have the Alphamini speak.

    IMPORTANT:
    Google Text2Speech service should be running. You can start it with: run-google-tts

    NOTE: you need to have setup Cloud Text-to-Speech API in your Google Cloud Console and configure the credential keyfile.
    See https://social-ai-vu.github.io/social-interaction-cloud/tutorials/6_google_cloud.html
    Save the file in conf/google/google-key.json
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(AlphaminiGoogleTTSDemo, self).__init__()
        
        # Demo-specific initialization
        self.mini_ip = "XXX"
        self.mini_id = "000XXX"
        self.mini_password = "mini"
        self.redis_ip = "XXX"
        self.google_keyfile_path = abspath(join("..", "..", "conf", "google", "google-key.json"))
        self.mini = None
        self.tts = None
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/alphamini/logs")

        self.set_log_level(sic_logging.INFO)
        
        self.setup()
    
    def setup(self):
        """Initialize and configure the Alphamini robot and Google TTS."""
        self.logger.info("Setting up Google TTS...")
        
        # Initialize Google TTS
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
                    text="Hi, I am an alphamini",
                    voice_name="en-US-Standard-C",
                    ssml_gender="FEMALE"
                )
            )
            
            self.logger.info("Initializing Alphamini...")
            # Initialize Alphamini with matching sample rate
            self.mini = Alphamini(
                ip=self.mini_ip,
                mini_id=self.mini_id,
                mini_password=self.mini_password,
                redis_ip=self.redis_ip,
                speaker_conf=MiniSpeakersConf(sample_rate=reply.sample_rate),
            )
            
            self.logger.info("Alphamini speaking...")
            self.mini.speaker.request(AudioRequest(reply.waveform, reply.sample_rate))
            
            self.logger.info("TTS demo completed successfully")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = AlphaminiGoogleTTSDemo()
    demo.run()
