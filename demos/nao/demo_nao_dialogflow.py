# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao
from sic_framework.devices.nao_stub import NaoStub
from sic_framework.devices.nao import NaoqiTextToSpeechRequest

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


class NaoDialogflowDemo(SICApplication):
    """
    NAO Dialogflow demo application.
    Demonstrates NAO picking up your intent and replying according to your trained agent using Dialogflow.

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
        super(NaoDialogflowDemo, self).__init__()
        
        # Demo-specific initialization
        self.nao_ip = "XXX"
        self.google_keyfile_path = google_keyfile_path
        self.nao = None
        self.dialogflow = None
        self.session_id = np.random.randint(10000)

        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/nao/logs")
        
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
                self.logger.info("Transcript: {}".format(message.response.recognition_result.transcript))
    
    def setup(self):
        """Initialize and configure NAO robot and Dialogflow."""
        self.logger.info("Initializing NAO...")
        
        # # Initialize NAO
        self.nao = Nao(ip=self.nao_ip)
        
        nao_mic = self.nao.mic
        
        # Load the key json file
        keyfile_json = json.load(open(self.google_keyfile_path))
        
        # Set up the config
        conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=16000)
        
        self.logger.info("Initializing Dialogflow...")
        # Initiate Dialogflow object
        self.dialogflow = Dialogflow(ip="localhost", conf=conf, input_source=nao_mic)
        
        # Register a callback function to act upon arrival of recognition_result
        self.dialogflow.register_callback(self.on_dialog)
    
    def run(self):
        """Main application loop."""
        try:
            # Demo starts
            self.nao.tts.request(NaoqiTextToSpeechRequest("Hello, who are you?"))
            self.logger.info(" -- Ready -- ")
            
            while not self.shutdown_event.is_set():
                self.logger.info(" ----- Your turn to talk!")
                reply = self.dialogflow.request(GetIntentRequest(self.session_id))
                
                self.logger.info(reply.intent)
                
                if reply.fulfillment_message:
                    text = reply.fulfillment_message
                    self.logger.info("Reply: {}".format(text))
                    self.nao.tts.request(NaoqiTextToSpeechRequest(text))
        except Exception as e:
            self.logger.error("Exception: {}".format(e=e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoDialogflowDemo(google_keyfile_path=abspath(join("..", "..", "conf", "google", "google-key.json")))
    demo.run()
