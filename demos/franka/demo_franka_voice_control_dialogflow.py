# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.franka import Franka
from sic_framework.devices.desktop import Desktop

# Import the service(s) we will be using
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
)

# Import message types and requests
from sic_framework.devices.common_franka.franka_motion_recorder import (
    GoHomeRequest,
    PandaJointsRecording,
    PlayRecordingRequest,
)

# Import libraries necessary for the demo
import json
from os.path import abspath, join
import numpy as np


class FrankaVoiceControlDemo(SICApplication):
    """
    Franka voice control demo application.
    Demonstrates controlling the Franka robot and executing prerecorded motions using voice commands via Dialogflow.

    IMPORTANT:
    To run this demo, you need to install the correct version of the panda-python dependency.
    A version mismatch will cause problems.
    See Installation point 3 for instructions:
    https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/2412675074/Getting+started+with+Franka+Emika+Research+3#Installation%3A
    
    Voice commands:
    - "go home" or "home" → Robot returns to home position
    - "wave" or "waving" → Robot plays the wave motion
    """
    
    def __init__(self, dialogflow_keyfile_path, motion_file="wave.motion", 
                 num_turns=25, frequency=1000, log_level=sic_logging.INFO):
        # Call parent constructor (handles singleton initialization)
        super(FrankaVoiceControlDemo, self).__init__(log_level=log_level)
        
        # Demo-specific initialization
        self.dialogflow_keyfile_path = dialogflow_keyfile_path
        self.motion_file = motion_file
        self.num_turns = num_turns
        self.frequency = frequency
        self.desktop = None
        self.franka = None
        self.dialogflow = None
        self.session_id = np.random.randint(10000)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/franka/logs")
        
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
        """Initialize and configure Desktop, Franka, and Dialogflow."""
        self.logger.info("Starting Franka Voice Control Demo...")
        
        # Initialize devices
        self.desktop = Desktop()
        self.franka = Franka()
        
        # Load the key json file
        try:
            with open(self.dialogflow_keyfile_path) as f:
                keyfile_json = json.load(f)
        except FileNotFoundError:
            self.logger.warning("No keyfile found, using None")
            keyfile_json = None
        
        # Set up Dialogflow
        dialogflow_conf = DialogflowConf(
            keyfile_json=keyfile_json,
            sample_rate_hertz=44100,
            language="en"
        )
        
        self.dialogflow = Dialogflow(conf=dialogflow_conf, input_source=self.desktop.mic)
        
        self.logger.info("Initialized dialogflow... registering callback function")
        # Register a callback function to act upon arrival of recognition_result
        self.dialogflow.register_callback(callback=self.on_dialog)
    
    def run(self):
        """Main application loop."""
        self.logger.info(" -- Starting Demo -- ")
        
        try:
            for i in range(self.num_turns):
                self.logger.info(" ----- Conversation turn {}".format(i))
                # Create context_name-lifespan pairs. If lifespan is set to 0, the context expires immediately
                contexts_dict = {"name": 1}
                reply = self.dialogflow.request(GetIntentRequest(self.session_id, contexts_dict))
                
                query_text = reply.response.query_result.query_text
                self.logger.info("Query text: {}".format(query_text))
                
                # Process voice commands
                if "home" in query_text.lower():
                    self.logger.info("Going home!")
                    self.franka.motion_recorder.request(GoHomeRequest())
                
                if "wave" in query_text.lower() or "waving" in query_text.lower():
                    self.logger.info("Waving!")
                    loaded_joints = PandaJointsRecording.load(self.motion_file)
                    self.logger.info("Playing wave motion")
                    self.franka.motion_recorder.request(PlayRecordingRequest(loaded_joints, self.frequency))
            
            self.logger.info("Voice control demo completed successfully")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = FrankaVoiceControlDemo(
        dialogflow_keyfile_path=abspath(join("..", "..", "conf", "google", "google-key.json"))
    )
    demo.run()

