import json
import numpy as np

from sic_framework.devices.desktop import Desktop
from sic_framework.services.dialogflow.dialogflow import (DialogflowConf, GetIntentRequest, RecognitionResult,
                                                          QueryResult, Dialogflow)
""" 
This demo should have your local microphone picking up your intent and printing out the reply from Dialogflow

The Dialogflow should be running. You can start it with:
[services/dialogflow] python dialogflow.py
"""

# the callback function
def on_dialog(message):
    if message.response:
        if message.response.recognition_result.is_final:
            print("Transcript:", message.response.recognition_result.transcript)

# local desktop setup
desktop = Desktop()

# load the key json file
keyfile_json = json.load(open("dialogflow-tutorial.json"))

# set up the config
conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=44100, language="en")

# initiate Dialogflow object
dialogflow = Dialogflow(ip='localhost', conf=conf)

# connect the output of DesktopMicrophone as the input of DialogflowComponent
dialogflow.connect(desktop.mic)

# register a callback function to act upon arrival of recognition_result
dialogflow.register_callback(on_dialog)

# Demo starts
print(" -- Ready -- ")
x = np.random.randint(10000)

try:
    for i in range(25):
        print(" ----- Conversation turn", i)
        # create context_name-lifespan pairs. If lifespan is set to 0, the context expires immediately
        contexts_dict = {"name": 1}
        reply = dialogflow.request(GetIntentRequest(x, contexts_dict))

        print("The detected intent:", reply.intent)

        if reply.fulfillment_message:
            text = reply.fulfillment_message
            print("Reply:", text)
except KeyboardInterrupt:
    print("Stop the dialogflow component.")
    dialogflow.stop()
