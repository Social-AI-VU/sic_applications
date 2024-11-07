import json
from os import environ
from os.path import abspath, join
from subprocess import call

import numpy as np
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest
from dotenv import load_dotenv

from sic_framework.devices.desktop import Desktop
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
)


"""

This demo shows how to use the dialogflow to get a transcript and an OpenAI GPT model to get responses to user input,
and a secret API key is required to run it


IMPORTANT

First, you need to obtain your own keyfile.json from Dialogflow, place it in conf/dialogflow, and point to it in the main 
How to get a key? See https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/2205155343/Getting+a+google+dialogflow+key for more information.

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


class ChatApp:

    def __init__(self, dialogflow_keyfile_path, sample_rate_hertz=44100, language="en"):
        # Generate your personal openai api key here: https://platform.openai.com/api-keys
        # Either add your openai key to your systems variables (and comment the next line out) or
        # create a .openai_env file in the conf/openai folder and add your key there like this:
        # OPENAI_API_KEY="your key"
        load_dotenv(abspath(join("..", "..", "conf", "openai", ".openai_env")))

        # set-up desktop client
        self.desktop = Desktop()

        # Setup GPT client
        conf = GPTConf(openai_key=environ["OPENAI_API_KEY"])
        self.gpt = GPT(conf=conf)

        # set up the config for dialogflow
        dialogflow_conf = DialogflowConf(keyfile_json=json.load(open(dialogflow_keyfile_path)),
                                         sample_rate_hertz=sample_rate_hertz, language=language)

        # initiate Dialogflow object
        self.dialogflow = Dialogflow(ip="localhost", conf=dialogflow_conf)

        # connect the output of DesktopMicrophone as the input of DialogflowComponent
        self.dialogflow.connect(self.desktop.mic)

        # register a callback function to act upon arrival of recognition_result
        self.dialogflow.register_callback(self.on_dialog)

        # flag to signal when the app should listen (i.e. transmit to dialogflow)
        self.can_listen = True

    def on_dialog(self, message):
        if message.response:
            if message.response.recognition_result.is_final:
                print("Transcript:", message.response.recognition_result.transcript)

    def local_tts(self, text):
        call(["espeak", "-s140 -ven+18 -z", text])

    def run(self):
        x = np.random.randint(10000)
        self.local_tts("What is your favorite hobby?")
        reply = self.dialogflow.request(GetIntentRequest(x))
        if reply.response.query_result.query_text:
            gpt_response = self.gpt.request(GPTRequest(f'You are a chat bot. The bot just asked about a hobby of the user make a brief '
                                   f'positive comment about the hobby and ask a '
                                   f'follow up question expanding the conversation.'
                                   f'This was the input by the user: "{reply.response.query_result.query_text}"'))
            self.local_tts(gpt_response.response)

if __name__ == "__main__":
    chat_app = ChatApp(abspath(join('..', '..', 'conf', 'dialogflow', 'dialogflow-tutorial.json')))
    chat_app.run()


