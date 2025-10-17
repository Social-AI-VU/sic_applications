# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop

# Import the service(s) we will be using
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
    QueryResult,
    RecognitionResult,
)

# Import libraries necessary for the demo
import json
from os.path import abspath, join
import numpy as np


class DialogflowDemo(SICApplication):
    """
    Dialogflow demo application using Desktop microphone for intent detection.

    IMPORTANT:
    First, you need to obtain your own keyfile.json from Dialogflow and place it in a location that the code can load.
    How to get a key? See https://social-ai-vu.github.io/social-interaction-cloud/external_apis/google_cloud.html#google-cloud-platform-guide for more information.
    Save the key in conf/google/google-key.json

    Second, the Dialogflow service needs to be running:
    1. pip install --upgrade social-interaction-cloud[dialogflow]
        Note: on macOS you might need use quotes pip install --upgrade "social-interaction-cloud[...]"
    2. run-dialogflow
    """
    
    def __init__(self, google_keyfile_path):
        # Call parent constructor (handles singleton initialization)
        super(DialogflowDemo, self).__init__()
        
        # Demo-specific initialization
        self.desktop = None
        self.desktop_mic = None
        self.dialogflow = None
        self.google_keyfile_path = google_keyfile_path

        self.set_log_level(sic_logging.INFO)

        # Random session ID is necceessary for Dialogflow
        self.session_id = np.random.randint(10000)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")
        
        self.setup()
    
    def on_dialog(self, message):
        """
        Callback function for Dialogflow recognition results.
        
        Args:
            message: The Dialogflow recognition result message.
        
        Returns:
            None
        """
        if message.response:
            if message.response.recognition_result.is_final:
                self.logger.info("Transcript: {transcript}".format(transcript=message.response.recognition_result.transcript))
    
    def setup(self):
        """Initialize and configure the desktop microphone and Dialogflow service."""
        self.logger.info("Initializing Desktop microphone")
        
        # local desktop setup
        self.desktop = Desktop()
        self.desktop_mic = self.desktop.mic
        
        self.logger.info("Initializing Dialogflow")
        # load the key json file, you need to get your own keyfile.json
        with open(self.google_keyfile_path) as f:
            keyfile_json = json.load(f)
        
        dialogflow_conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=44100, language="en")
        
        self.dialogflow = Dialogflow(conf=dialogflow_conf, input_source=self.desktop_mic)
        
        self.logger.info("Initialized dialogflow... registering callback function")
        # register a callback function to act upon arrival of recognition_result
        self.dialogflow.register_callback(callback=self.on_dialog)
    
    def run(self):
        """Main application loop."""
        self.logger.info(" -- Starting Demo -- ")
        
        try:
            while not self.shutdown_event.is_set():
                self.logger.info(" ----- Conversation turn")
                # create context_name-lifespan pairs. If lifespan is set to 0, the context expires immediately
                contexts_dict = {"name": 1}
                reply = self.dialogflow.request(GetIntentRequest(self.session_id, contexts_dict))
                
                self.logger.info("The detected intent: {intent}".format(intent=reply.intent))
                
                if reply.fulfillment_message:
                    text = reply.fulfillment_message
                    self.logger.info("Reply: {text}".format(text=text))
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = DialogflowDemo(google_keyfile_path=abspath(join("..", "..", "conf", "google", "google-key.json")))
    demo.run()
