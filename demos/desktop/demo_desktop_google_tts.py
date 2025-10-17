# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop

# Import configuration(s) for the components
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf

# Import the service(s) we will be using
from sic_framework.services.google_tts.google_tts import (
    GetSpeechRequest,
    Text2Speech,
    Text2SpeechConf,
)

# Import the message type(s) we're using
from sic_framework.core.message_python2 import AudioRequest

# Import libraries necessary for the demo
import json
from os.path import abspath, join


class GoogleTTSDemo(SICApplication):
    """
    Google Text-to-Speech demo application.

    IMPORTANT:
    Google text-to-speech dependency needs to be installed and the service needs to be running:
    1. pip install --upgrade social-interaction-cloud[google-tts]
        Note: on macOS you might need use quotes pip install --upgrade "social-interaction-cloud[...]"
    2. run-google-tts (in a separate terminal)

    NOTE: you need to have setup Cloud Text-to-Speech API in your Google Cloud Console and configure the credential keyfile.
    See https://social-ai-vu.github.io/social-interaction-cloud/external_apis/google_cloud.html#google-cloud-platform-guide
    """
    
    def __init__(self, google_keyfile_path):
        # Call parent constructor (handles singleton initialization)
        super(GoogleTTSDemo, self).__init__()
        
        # Demo-specific initialization
        self.desktop = None
        self.tts = None
        self.google_keyfile_path = google_keyfile_path
        
        # Configure logging
        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure the text-to-speech service and desktop speakers."""
        self.logger.info("Setting up Google Text-to-Speech...")
        
        # initialize the text2speech service
        tts_conf = Text2SpeechConf(
            keyfile_json=json.load(open(self.google_keyfile_path))
        )
        self.tts = Text2Speech(conf=tts_conf)
    
    def run(self):
        """Main application logic."""
        self.logger.info("Starting Google TTS Demo")
        
        try:
            # Request speech synthesis from Google TTS
            reply = self.tts.request(
                GetSpeechRequest(text="Hi, I am your computer", voice_name="en-US-Standard-C")
            )
            
            # Make sure that the sample rate of the speakers is the same as the sample rate of the audio from Google
            self.desktop = Desktop(speakers_conf=SpeakersConf(sample_rate=reply.sample_rate))
            
            # Play the audio through the speakers
            response = self.desktop.speakers.request(AudioRequest(reply.waveform, reply.sample_rate))
            
            self.logger.info("Speech playback completed")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = GoogleTTSDemo(google_keyfile_path=abspath(join("..", "..", "conf", "google", "google-key.json")))
    demo.run()
