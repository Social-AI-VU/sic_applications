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

"""
This demo should have Nao picking up your intent and replying according to your trained agent using dialogflow.

IMPORTANT

First, you need to obtain your own keyfile.json from Dialogflow and place it in a location that the code at line 39 can load.
How to get a key? See https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/2205155343/Getting+a+google+dialogflow+key for more information.
Save the key in conf/dialogflow/dialogflow-tutorial.json

Second, the Dialogflow service needs to be running:

1. pip install social-interaction-cloud[dialogflow]
2. run-dialogflow

"""

# the callback function
def on_dialog(message):
    if message.response:
        if message.response.recognition_result.is_final:
            print("Transcript:", message.response.recognition_result.transcript)


print("initializing Desktop microphone")

# local desktop setup
desktop = Desktop()
desktop_mic_output = desktop.mic.get_output_channel()

print("Desktop microphone output channel: ", desktop_mic_output)

print("loading in Dialogflow keyfile")
# load the key json file, you need to get your own keyfile.json
with open(
    abspath(join("..", "..", "conf", "dialogflow", "dialogflow-key.json"))
) as f:
    keyfile_json = json.load(f)

print("initializing Dialogflow")

dialogflow_conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=44100, language="en")

# initiate Dialogflow object
dialogflow = Dialogflow(ip="localhost", conf=dialogflow_conf, input_channel=desktop_mic_output)
dialogflow_output = dialogflow.get_output_channel()

print("Initialized dialogflow... registering callback function")

# register a callback function to act upon arrival of recognition_result
dialogflow.register_callback(output_channel=dialogflow_output, callback=on_dialog)

print("Registered callback")

# Demo starts
print(" -- Ready -- ")
x = np.random.randint(10000)

print("starting demo")
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
