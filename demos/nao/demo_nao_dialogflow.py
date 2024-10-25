import json

import numpy as np
from sic_framework.devices import Nao
from sic_framework.devices.nao import NaoqiTextToSpeechRequest
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
    QueryResult,
    RecognitionResult,
)

"""
This demo should have Nao picking up your intent and replying according to your trained agent using dialogflow.

IMPORTANT

First, you need to obtain your own keyfile.json from Dialogflow and place it in a location that the code at line 41 can load.
How to get a key? See https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/2205155343/Getting+a+google+dialogflow+key for more information.

Second, the Dialogflow service needs to be running:

1. pip install social-interaction-cloud[dialogflow]
2. run-dialogflow

"""


# the callback function
def on_dialog(message):
    if message.response:
        if message.response.recognition_result.is_final:
            print("Transcript:", message.response.recognition_result.transcript)


# connect to the robot
nao = Nao(ip="192.168.178.153")

# load the key json file (you need to get your own keyfile.json)
keyfile_json = json.load(open("dialogflow-tutorial.json"))

# set up the config
conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=16000)

# initiate Dialogflow object
dialogflow = Dialogflow(ip="localhost", conf=conf)

# connect the output of NaoqiMicrophone as the input of DialogflowComponent
dialogflow.connect(nao.mic)

# register a callback function to act upon arrival of recognition_result
dialogflow.register_callback(on_dialog)

# Demo starts
nao.tts.request(NaoqiTextToSpeechRequest("Hello, who are you?"))
print(" -- Ready -- ")
x = np.random.randint(10000)

try:
    for i in range(25):
        print(" ----- Conversation turn", i)
        reply = dialogflow.request(GetIntentRequest(x))

        print(reply.intent)

        if reply.fulfillment_message:
            text = reply.fulfillment_message
            print("Reply:", text)
            nao.tts.request(NaoqiTextToSpeechRequest(text))
except KeyboardInterrupt:
    print("Stop the dialogflow component.")
    dialogflow.stop()
