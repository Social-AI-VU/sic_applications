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
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

app = SICApplication()
logger = app.get_app_logger()

# can be DEBUG, INFO, WARNING, ERROR, CRITICAL
app.set_log_level(sic_logging.INFO)

# Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
# app.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")

# Use the shutdown event as a loop condition.
shutdown_flag = app.get_shutdown_event()

# the callback function
def on_dialog(message):
    if message.response:
        if message.response.recognition_result.is_final:
            logger.info("Transcript: {transcript}".format(transcript=message.response.recognition_result.transcript))

logger.info("initializing Desktop microphone")

# local desktop setup
desktop = Desktop()
desktop_mic = desktop.mic

logger.info("initializing Dialogflow")
# load the key json file, you need to get your own keyfile.json
with open(
    abspath(join("..", "..", "conf", "google", "google-key.json"))
) as f:
    keyfile_json = json.load(f)

dialogflow_conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=44100, language="en")

dialogflow = Dialogflow(conf=dialogflow_conf, input_source=desktop_mic)

logger.info("Initialized dialogflow... registering callback function")
# register a callback function to act upon arrival of recognition_result
dialogflow.register_callback(callback=on_dialog)

# Demo starts
logger.info(" -- Starting Demo -- ")
x = np.random.randint(10000)

try:
    while not shutdown_flag.is_set():
        logger.info(" ----- Conversation turn")
        # create context_name-lifespan pairs. If lifespan is set to 0, the context expires immediately
        contexts_dict = {"name": 1}
        reply = dialogflow.request(GetIntentRequest(x, contexts_dict))

        logger.info("The detected intent: {intent}".format(intent=reply.intent))

        # print("REPLY:", reply)

        if reply.fulfillment_message:
            text = reply.fulfillment_message
            logger.info("Reply: {text}".format(text=text))
except Exception as e:
    logger.error("Exception: ", e)
