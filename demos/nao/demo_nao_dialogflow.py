"""
This demo should have Nao picking up your intent and replying according to your trained agent using dialogflow.

IMPORTANT

First, you need to obtain your own keyfile.json from Dialogflow and place it in a location that the code at line 41 can load.
How to get a key? See https://social-ai-vu.github.io/social-interaction-cloud/tutorials/6_google_cloud.html for more information.

Second, the Dialogflow service needs to be running:

1. pip install social-interaction-cloud[dialogflow]
2. run-dialogflow

"""

import json
from os.path import abspath, join

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
from sic_framework.core.sic_application import (
    set_log_level,
    set_log_file,
    get_app_logger, 
    get_shutdown_event
)
from sic_framework.core import sic_logging

# In case you want to use the logger with a neat format as opposed to logger.info statements.
logger = get_app_logger()

# can be DEBUG, INFO, WARNING, ERROR, CRITICAL
set_log_level(sic_logging.DEBUG)

# Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
# set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")

# Use the shutdown event as a loop condition.
shutdown_flag = get_shutdown_event()

# the callback function
def on_dialog(message):
    if message.response:
        if message.response.recognition_result.is_final:
            logger.info("Transcript:", message.response.recognition_result.transcript)

logger.info("Initializing Nao...")

nao = Nao(ip="XXX")

nao_mic = nao.mic

# load the key json file (you need to get your own keyfile.json)
keyfile_json = json.load(open(abspath(join("..", "..", "conf", "google", "google-key.json"))))

# set up the config
conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=16000)

logger.info("Initializing Dialogflow...")
# initiate Dialogflow object
dialogflow = Dialogflow(ip="localhost", conf=conf, input_source=nao_mic)

# register a callback function to act upon arrival of recognition_result
dialogflow.register_callback(on_dialog)

# Demo starts
nao.tts.request(NaoqiTextToSpeechRequest("Hello, who are you?"))
logger.info(" -- Ready -- ")
x = np.random.randint(10000)

try:
    while not shutdown_flag.is_set():
        logger.info(" ----- Your turn to talk!")
        reply = dialogflow.request(GetIntentRequest(x))

        logger.info(reply.intent)

        if reply.fulfillment_message:
            text = reply.fulfillment_message
            logger.info("Reply:", text)
            nao.tts.request(NaoqiTextToSpeechRequest(text))
except Exception as e:
    logger.error(f"Exception: {e}".format(e=e))
