"""
Demo: AlphaMini recognizes user intent and replies using Dialogflow and Text-to-Speech.

Instructions:
1. Obtain your own Google Cloud Platform keyfile.json. Make sure to enable the Dialogflow and Text-to-Speech services in the Google Cloud Platform. Place it at:
   conf/google/google-key.json
   → How to get a key:
     https://social-ai-vu.github.io/social-interaction-cloud/tutorials/6_google_cloud.html

2. Ensure Dialogflow and Google Text-to-Speech services are running:
   $ pip install social-interaction-cloud[alphamini,dialogflow,google-tts]
   $ run-dialogflow
   $ run-google-tts (in another terminal)
"""

import json
from os.path import abspath, join

import numpy as np
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.devices.alphamini import Alphamini
from sic_framework.devices.common_mini.mini_speaker import MiniSpeakersConf
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
)
from sic_framework.services.google_tts.google_tts import (
    GetSpeechRequest,
    Text2Speech,
    Text2SpeechConf,
)
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Create the SICApplication instance to be able to use the logger and the shutdown event
app = SICApplication()
logger = app.get_app_logger()
app.set_log_level(sic_logging.DEBUG)

# the callback function
def on_dialog(message):
    if message.response:
        if message.response.recognition_result.is_final:
            logger.info("Transcript:", message.response.recognition_result.transcript)


# setup the tts service
tts_conf = Text2SpeechConf(
    keyfile_json=json.load(open(abspath(join("..", "..", "conf", "google", "google-key.json"))))
)
tts = Text2Speech(conf=tts_conf)

# intro message
tts_reply = tts.request(
    GetSpeechRequest(
        text="Hi, I am an alphamini, what is your name?",
        voice_name="en-US-Standard-C",
        ssml_gender="FEMALE",
    )
)

# local desktop setup
mini = Alphamini(
    ip="XXX",
    mini_id="000XXX",
    mini_password="mini",
    redis_ip="XXX",
    speaker_conf=MiniSpeakersConf(sample_rate=tts_reply.sample_rate),
)


# load the key json file, you need to get your own keyfile.json
keyfile_json = json.load(
    open(abspath(join("..", "..", "conf", "google", "google-key.json")))
)
# set up the config
df_conf = DialogflowConf(
    keyfile_json=keyfile_json, sample_rate_hertz=44100, language="en"
)

# initiate Dialogflow object
dialogflow = Dialogflow(ip="localhost", conf=df_conf, input_source=mini.mic)

# register a callback function to act upon arrival of recognition_result
dialogflow.register_callback(on_dialog)

# Demo starts
mini.speaker.request(AudioRequest(tts_reply.waveform, tts_reply.sample_rate))
logger.info(" -- Ready -- ")
session_id = np.random.randint(10000)

try:
    for i in range(25):
        logger.info(" ----- Conversation turn {}".format(i))
        # create context_name-lifespan pairs. If lifespan is set to 0, the context expires immediately
        contexts_dict = {"name": 1}
        reply = dialogflow.request(GetIntentRequest(session_id, contexts_dict))

        logger.info("The detected intent: {}".format(reply.intent))

        if reply.fulfillment_message:
            text = reply.fulfillment_message
            logger.info("Reply: {}".format(text))

            # send the fulfillment text to TTS for speech synthesis
            reply = tts.request(
                GetSpeechRequest(
                    text=text,
                    voice_name="en-US-Standard-C",
                    ssml_gender="FEMALE",
                )
            )
            mini.speaker.request(AudioRequest(reply.waveform, reply.sample_rate))

except Exception as e:
    logger.error("Exception: {}".format(e))
finally:
    app.shutdown()