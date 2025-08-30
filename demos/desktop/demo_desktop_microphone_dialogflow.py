"""
This demo should have your Desktop microphone picking up your intent and replying according to your trained agent using dialogflow.

IMPORTANT

First, you need to obtain your own keyfile.json from Dialogflow and place it in a location that the code at line 39 can load.
How to get a key? See https://social-ai-vu.github.io/social-interaction-cloud/tutorials/6_google_cloud.html for more information.
Save the key in conf/dialogflow/dialogflow-tutorial.json

Second, the Dialogflow service needs to be running:

1. pip install social-interaction-cloud[dialogflow]
2. run-dialogflow

"""

import json
from os.path import abspath, join

import numpy as np
from sic_framework.devices.desktop import Desktop
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
    QueryResult,
    RecognitionResult,
)

# the callback function
def on_dialog(message):
    if message.response:
        if message.response.recognition_result.is_final:
            print("Transcript:", message.response.recognition_result.transcript)

print("initializing Desktop microphone")

# local desktop setup
desktop = Desktop()
desktop_mic = desktop.mic

print("initializing Dialogflow")
# load the key json file, you need to get your own keyfile.json
with open(
    abspath(join("..", "..", "conf", "google", "google-key.json"))
) as f:
    keyfile_json = json.load(f)

dialogflow_conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=44100, language="en")

dialogflow = Dialogflow(conf=dialogflow_conf, input_source=desktop_mic)

print("Initialized dialogflow... registering callback function")
# register a callback function to act upon arrival of recognition_result
dialogflow.register_callback(callback=on_dialog)

# Demo starts
print(" -- Starting Demo -- ")
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
    print("Stopping dialogflow component.")
    dialogflow.stop()
