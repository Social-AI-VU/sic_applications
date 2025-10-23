# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop

# Import the service(s) we will be using
from sic_framework.services.dialogflow_cx.dialogflow_cx import (
    DialogflowCX,
    DialogflowCXConf,
    DetectIntentRequest,
    QueryResult,
    RecognitionResult,
)

# Import libraries necessary for the demo
import json
from os.path import abspath, join
import numpy as np


class DialogflowCXDemo(SICApplication):
    """
    Dialogflow CX (Conversational Agents) demo application using Desktop microphone for intent detection.

    IMPORTANT:
    1. You need to obtain your own keyfile.json from Google Cloud and place it in a location that the code can load.
       How to get a key? See https://social-ai-vu.github.io/social-interaction-cloud/external_apis/google_cloud.html
       Save the key in conf/google/google-key.json

    2. You need to create a Dialogflow CX agent and note:
       - Your agent ID (found in agent settings)
       - Your agent location (e.g., "global" or "us-central1")

    3. The Conversational Agents service needs to be running:
       - pip install social-interaction-cloud[dialogflow-cx]
       - run-dialogflow-cx

    Note: This uses the newer Dialogflow CX API (v3), which is different from the older Dialogflow ES (v2).
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(DialogflowCXDemo, self).__init__()
        
        # Demo-specific initialization
        self.desktop = None
        self.desktop_mic = None
        self.conversational_agent = None

        self.set_log_level(sic_logging.INFO)

        # Random session ID is necessary for Dialogflow CX
        self.session_id = np.random.randint(10000)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")
        
        self.setup()
    
    def on_recognition(self, message):
        """
        Callback function for Dialogflow CX recognition results.
        
        Args:
            message: The Dialogflow CX recognition result message.
        
        Returns:
            None
        """
        if message.response:
            if hasattr(message.response, 'recognition_result') and message.response.recognition_result:
                rr = message.response.recognition_result
                if hasattr(rr, 'is_final') and rr.is_final:
                    if hasattr(rr, 'transcript'):
                        self.logger.info("Transcript: {transcript}".format(transcript=rr.transcript))
    
    def setup(self):
        """Initialize and configure the desktop microphone and Conversational Agents service."""
        self.logger.info("Initializing Desktop microphone")
        
        # Local desktop setup
        self.desktop = Desktop()
        self.desktop_mic = self.desktop.mic
        
        self.logger.info("Initializing Conversational Agents (Dialogflow CX)")
        
        # Load the key json file - you need to get your own keyfile.json
        with open(abspath(join("..", "..", "conf", "google", "google-key.json"))) as f:
            keyfile_json = json.load(f)
        
        # TODO: Replace with your actual agent ID and location
        # You can find your agent ID in the Dialogflow CX console:
        # 1. Go to https://dialogflow.cloud.google.com/cx/
        # 2. Select your project
        # 3. Click on your agent
        # 4. The agent ID is in the URL: ...agents/YOUR-AGENT-ID/...
        # or in Agent Settings under "Agent ID"
        
        agent_id = "XXX"  # Replace with your agent ID
        location = "XXX"  # Replace with your agent location if different
        
        # Create configuration for Conversational Agents
        ca_conf = DialogflowCXConf(
            keyfile_json=keyfile_json,
            agent_id=agent_id,
            location=location,
            sample_rate_hertz=44100,
            language="en-US"
        )
        
        # Initialize the conversational agent with microphone input
        self.conversational_agent = DialogflowCX(conf=ca_conf, input_source=self.desktop_mic)
        
        self.logger.info("Initialized Conversational Agents... registering callback function")
        # Register a callback function to handle recognition results
        self.conversational_agent.register_callback(callback=self.on_recognition)
    
    def run(self):
        """Main application loop."""
        self.logger.info(" -- Starting Conversational Agents Demo -- ")
        
        try:
            while not self.shutdown_event.is_set():
                self.logger.info(" ----- Conversation turn")
                
                # Request intent detection with the current session
                reply = self.conversational_agent.request(DetectIntentRequest(self.session_id))
                
                # Log the detected intent
                if reply.intent:
                    self.logger.info("The detected intent: {intent} (confidence: {conf})".format(
                        intent=reply.intent,
                        conf=reply.intent_confidence if reply.intent_confidence else "N/A"
                    ))
                else:
                    self.logger.info("No intent detected")
                
                # Log the transcript
                if reply.transcript:
                    self.logger.info("User said: {text}".format(text=reply.transcript))
                
                # Log the agent's response
                if reply.fulfillment_message:
                    self.logger.info("Agent reply: {text}".format(text=reply.fulfillment_message))
                else:
                    self.logger.info("No fulfillment message")
                
                # Log any parameters
                if reply.parameters:
                    self.logger.info("Parameters: {params}".format(params=reply.parameters))
                    
        except KeyboardInterrupt:
            self.logger.info("Demo interrupted by user")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = DialogflowCXDemo()
    demo.run()

