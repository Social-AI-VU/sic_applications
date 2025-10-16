# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.alphamini import Alphamini

# Import the service(s) we will be using
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
)
from sic_framework.services.google_tts.google_tts import (
    GetSpeechRequest,
    Text2Speech,
    Text2SpeechConf,
)

# Import configuration and message types
from sic_framework.devices.common_mini.mini_speaker import MiniSpeakersConf
from sic_framework.core.message_python2 import AudioRequest

# Import libraries necessary for the demo
import json
from os.path import abspath, join
import numpy as np


class AlphaminiDialogflowDemo(SICApplication):
    """
    Alphamini Dialogflow demo application.
    Demonstrates how AlphaMini recognizes user intent and replies using Dialogflow and Text-to-Speech.

    IMPORTANT:
    1. Obtain your own Google Cloud Platform keyfile.json. Make sure to enable the Dialogflow and Text-to-Speech services.
       Place it at: conf/google/google-key.json
       → How to get a key: https://social-ai-vu.github.io/social-interaction-cloud/tutorials/6_google_cloud.html

    2. Ensure Dialogflow and Google Text-to-Speech services are running:
       $ pip install social-interaction-cloud[alphamini,dialogflow,google-tts]
       $ run-dialogflow
       $ run-google-tts (in another terminal)
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(AlphaminiDialogflowDemo, self).__init__()
        

        # Demo-specific initialization
        self.mini_ip = "XXX"
        self.mini_id = "000XXX"
        self.mini_password = "mini"
        self.redis_ip = "XXX"
        self.google_keyfile_path = abspath(join("..", "..", "conf", "google", "google-key.json"))
        self.num_turns = 25
        self.mini = None
        self.tts = None
        self.dialogflow = None
        self.session_id = np.random.randint(10000)

        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/alphamini/logs")
        
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
        """Initialize and configure the Alphamini robot, Google TTS, and Dialogflow."""
        self.logger.info("Setting up Alphamini Dialogflow Demo...")
        
        # Setup the TTS service
        tts_conf = Text2SpeechConf(
            keyfile_json=json.load(open(self.google_keyfile_path))
        )
        self.tts = Text2Speech(conf=tts_conf)
        
        # Get intro message to determine sample rate
        tts_reply = self.tts.request(
            GetSpeechRequest(
                text="Hi, I am an alphamini, what is your name?",
                voice_name="en-US-Standard-C",
                ssml_gender="FEMALE",
            )
        )
        
        # Initialize Alphamini
        self.mini = Alphamini(
            ip=self.mini_ip,
            mini_id=self.mini_id,
            mini_password=self.mini_password,
            redis_ip=self.redis_ip,
            speaker_conf=MiniSpeakersConf(sample_rate=tts_reply.sample_rate),
        )
        
        # Load the key json file
        keyfile_json = json.load(open(self.google_keyfile_path))
        
        # Set up the Dialogflow config
        df_conf = DialogflowConf(
            keyfile_json=keyfile_json, sample_rate_hertz=44100, language="en"
        )
        
        # Initiate Dialogflow object
        self.dialogflow = Dialogflow(ip="localhost", conf=df_conf, input_source=self.mini.mic)
        
        # Register a callback function to act upon arrival of recognition_result
        self.dialogflow.register_callback(self.on_dialog)
        
        # Play intro message
        self.mini.speaker.request(AudioRequest(tts_reply.waveform, tts_reply.sample_rate))
        self.logger.info(" -- Ready -- ")
    
    def run(self):
        """Main application loop."""
        try:
            for i in range(self.num_turns):
                self.logger.info(" ----- Conversation turn {}".format(i))
                # create context_name-lifespan pairs. If lifespan is set to 0, the context expires immediately
                contexts_dict = {"name": 1}
                reply = self.dialogflow.request(GetIntentRequest(self.session_id, contexts_dict))
                
                self.logger.info("The detected intent: {}".format(reply.intent))
                
                if reply.fulfillment_message:
                    text = reply.fulfillment_message
                    self.logger.info("Reply: {}".format(text))
                    
                    # Send the fulfillment text to TTS for speech synthesis
                    tts_reply = self.tts.request(
                        GetSpeechRequest(
                            text=text,
                            voice_name="en-US-Standard-C",
                            ssml_gender="FEMALE",
                        )
                    )
                    self.mini.speaker.request(AudioRequest(tts_reply.waveform, tts_reply.sample_rate))
            
            self.logger.info("Dialogflow demo completed successfully")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = AlphaminiDialogflowDemo()
    demo.run()
