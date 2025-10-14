"""

This demo shows how to use the dialogflow to get a transcript and an OpenAI GPT model to get responses to user input,
and a secret API key is required to run it


IMPORTANT

First, you need to obtain your own keyfile.json from Dialogflow, place it in conf/dialogflow, and point to it in the main 
How to get a key? See https://social-ai-vu.github.io/social-interaction-cloud/tutorials/6_google_cloud.html

Second, you need an openAI key:
Generate your personal openai api key here: https://platform.openai.com/api-keys
Either add your openai key to your systems variables (and comment the next line out) or
create a .openai_env file in the conf/openai folder and add your key there like this:
OPENAI_API_KEY="your key"

Third, you need to have espeak installed.
[Windows]
download and install espeak: http://espeak.sourceforge.net/
add eSpeak/command-line to PATH
[Linux]
`sudo apt-get install espeak libespeak-dev`
[MacOS]
brew install espeak

Fourth, Dialogflow and OpenAI gpt service need to be running:

1. pip install --upgrade social-interaction-cloud[dialogflow,openai-gpt]
2. in new terminal: run-gpt
3. in new terminal: run-dialogflow

"""

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
)
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest

# Import libraries necessary for the demo
import json
from os import environ
from os.path import abspath, join
from subprocess import call
import numpy as np
from dotenv import load_dotenv


class ChatApp(SICApplication):
    """
    Chat application demo using Dialogflow and OpenAI GPT.
    
    IMPORTANT:
    First, you need to obtain your own keyfile.json from Dialogflow, place it in conf/dialogflow, and point to it in the main 
    How to get a key? See https://social-ai-vu.github.io/social-interaction-cloud/tutorials/6_google_cloud.html
    
    Second, you need an openAI key:
    Generate your personal openai api key here: https://platform.openai.com/api-keys
    Either add your openai key to your systems variables (and comment the next line out) or
    create a .openai_env file in the conf/openai folder and add your key there like this:
    OPENAI_API_KEY="your key"
    
    Third, you need to have espeak installed.
    [Windows] download and install espeak: http://espeak.sourceforge.net/, add eSpeak/command-line to PATH
    [Linux] `sudo apt-get install espeak libespeak-dev`
    [MacOS] brew install espeak
    
    Fourth, Dialogflow and OpenAI gpt service need to be running:
    1. pip install --upgrade social-interaction-cloud[dialogflow,openai-gpt]
    2. in new terminal: run-gpt
    3. in new terminal: run-dialogflow
    """

    def __init__(self, dialogflow_keyfile_path, sample_rate_hertz=44100, language="en", log_level=sic_logging.INFO):
        # Call parent constructor (handles singleton initialization)
        super(ChatApp, self).__init__(log_level=log_level)
        
        # Demo-specific initialization
        self.dialogflow_keyfile_path = dialogflow_keyfile_path
        self.sample_rate_hertz = sample_rate_hertz
        self.language = language
        self.desktop = None
        self.gpt = None
        self.dialogflow = None
        self.can_listen = True
        self.session_id = np.random.randint(10000)
        
        self.setup()

    def setup(self):
        """Initialize and configure Desktop, GPT, and Dialogflow."""
        self.logger.info("Setting up Chat App...")
        
        # Load OpenAI API key
        load_dotenv(abspath(join("..", "..", "conf", "openai", ".openai_env")))

        # set-up desktop client
        self.desktop = Desktop()

        # Setup GPT client
        conf = GPTConf(openai_key=environ["OPENAI_API_KEY"])
        self.gpt = GPT(conf=conf)

        # set up the config for dialogflow
        dialogflow_conf = DialogflowConf(
            keyfile_json=json.load(open(self.dialogflow_keyfile_path)),
            sample_rate_hertz=self.sample_rate_hertz,
            language=self.language
        )

        # initiate Dialogflow object
        self.dialogflow = Dialogflow(ip="localhost", conf=dialogflow_conf, input_source=self.desktop.mic)

        # register a callback function to act upon arrival of recognition_result
        self.dialogflow.register_callback(self.on_dialog)

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
                print("Transcript:", message.response.recognition_result.transcript)

    def local_tts(self, text):
        """Use local espeak for text-to-speech."""
        call(["espeak", "-s140 -ven+18 -z", text])

    def run(self):
        """Main application logic."""
        self.logger.info("Starting Chat App")
        
        try:
            self.local_tts("What is your favorite hobby?")
            reply = self.dialogflow.request(GetIntentRequest(self.session_id))
            if reply.response.query_result.query_text:
                gpt_response = self.gpt.request(GPTRequest(
                    f'You are a chat bot. The bot just asked about a hobby of the user make a brief '
                    f'positive comment about the hobby and ask a '
                    f'follow up question expanding the conversation.'
                    f'This was the input by the user: "{reply.response.query_result.query_text}"'
                ))
                self.local_tts(gpt_response.response)
            
            self.logger.info("Chat completed")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    chat_app = ChatApp(abspath(join('..', '..', 'conf', 'google', 'google-key.json')))
    chat_app.run()