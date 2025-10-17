# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop

# Import the service(s) we will be using
from sic_framework.services.google_stt.google_stt import (
    GoogleSpeechToText,
    GoogleSpeechToTextConf,
    GetStatementRequest,
)

# Import libraries necessary for the demo
import json
from os.path import abspath, join
import time


class GoogleSTTDemo(SICApplication):
    """
    Google Speech-to-Text demo application.

    IMPORTANT:
    Google speech-to-text dependency needs to be installed and the service needs to be running:
    1. pip install --upgrade social-interaction-cloud[google-stt]
        Note: on macOS you might need use quotes pip install --upgrade "social-interaction-cloud[...]"
    2. run-google-stt

    NOTE: you need to have setup Cloud Speech-to-Text API in your Google Cloud Console and configure the credential keyfile.
    See https://social-ai-vu.github.io/social-interaction-cloud/external_apis/google_cloud.html#google-cloud-platform-guide
    """
    
    def __init__(self, google_keyfile_path):
        # Call parent constructor (handles singleton initialization)
        super(GoogleSTTDemo, self).__init__()
        
        # Demo-specific initialization
        self.desktop = None
        self.desktop_mic = None
        self.google_keyfile_path = google_keyfile_path
        self.stt = None
        
        # Configure logging
        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")
        
        self.setup()
    
    def on_stt(self, result):
        """
        Callback function for interim speech-to-text results.
        
        Args:
            result: The recognition result containing transcript alternatives.
        
        Returns:
            None
        """
        if hasattr(result.response, 'alternatives') and result.response.alternatives:
            transcript = result.response.alternatives[0].transcript
            print("Interim result:\n", transcript)
    
    def setup(self):
        """Initialize and configure the desktop microphone and speech-to-text service."""
        self.logger.info("Setting up Google Speech-to-Text...")
        
        # initialize the desktop device to get the microphone
        self.desktop = Desktop()
        self.desktop_mic = self.desktop.mic
        
        # initialize the speech-to-text service
        stt_conf = GoogleSpeechToTextConf(
            keyfile_json=json.load(open(self.google_keyfile_path)),
            sample_rate_hertz=44100,
            language="en-US",
            interim_results=False,
        )
        
        self.stt = GoogleSpeechToText(conf=stt_conf, input_source=self.desktop_mic)
        
        # register a callback function to act upon arrival of recognition_result
        self.stt.register_callback(callback=self.on_stt)
    
    def run(self):
        """Main application loop."""
        self.logger.info("Starting Google STT Demo")
        print(" -- Starting Demo -- ")
        
        try:
            while not self.shutdown_event.is_set():
                # For more info on what is returned, see Google's documentation on the response object:
                # https://cloud.google.com/php/docs/reference/cloud-speech/latest/V2.StreamingRecognizeResponse
                result = self.stt.request(GetStatementRequest())
                if not result or not hasattr(result.response, 'alternatives') or not result.response.alternatives:
                    print("No transcript received")
                    continue
                # alternative is a list of possible transcripts, we take the first one which is the most likely
                transcript = result.response.alternatives[0].transcript
                print("User said:\n", transcript)
                # Small delay between requests to allow proper cleanup
                time.sleep(0.1)
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = GoogleSTTDemo(google_keyfile_path=abspath(join("..", "..", "conf", "google", "google-key.json")))
    demo.run()
