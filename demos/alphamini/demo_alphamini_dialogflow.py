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
from sic_framework.services.text2speech.text2speech_service import (
    GetSpeechRequest,
    Text2Speech,
    Text2SpeechConf,
)

"""
Demo: AlphaMini recognizes user intent and replies using Dialogflow and Text-to-Speech.

Instructions:
1. Obtain your own Dialogflow keyfile.json. Place it at:
   conf/dialogflow/dialogflow-tutorial.json
   → How to get a key:
     https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/2205155343/Getting+a+google+dialogflow+key

2. Obtain your own Google Text-to-Speech keyfile.json. Place it at:
    conf/dialogflow/google_tts_keyfile.json
    → How to get a key:
      https://console.cloud.google.com/apis/api/texttospeech.googleapis.com/

3. Ensure Dialogflow and Google Text-to-Speech services are running:
   $ pip install social-interaction-cloud[alphamini,dialogflow,google-tts]
   $ run-dialogflow
   $ run-google-tts (in another terminal)
"""


# the callback function
def on_dialog(message):
    if message.response:
        if message.response.recognition_result.is_final:
            print("Transcript:", message.response.recognition_result.transcript)


# setup the tts service
tts_conf = Text2SpeechConf(
    keyfile=abspath(join("..", "..", "conf", "dialogflow", "google_tts_keyfile.json"))
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
    ip="192.168.178.111",
    mini_id="00297",
    mini_password="mini",
    redis_ip="192.168.178.123",
    speaker_conf=MiniSpeakersConf(sample_rate=tts_reply.sample_rate),
)


# load the key json file, you need to get your own keyfile.json
keyfile_json = json.load(
    open(abspath(join("..", "..", "conf", "dialogflow", "dialogflow-tutorial.json")))
)
# set up the config
df_conf = DialogflowConf(
    keyfile_json=keyfile_json, sample_rate_hertz=44100, language="en"
)

# initiate Dialogflow object
dialogflow = Dialogflow(ip="localhost", conf=df_conf)

# connect the output of DesktopMicrophone as the input of DialogflowComponent
dialogflow.connect(mini.mic)

# register a callback function to act upon arrival of recognition_result
dialogflow.register_callback(on_dialog)

# Demo starts
mini.speaker.request(AudioRequest(tts_reply.waveform, tts_reply.sample_rate))
print(" -- Ready -- ")
session_id = np.random.randint(10000)

try:
    for i in range(25):
        print(" ----- Conversation turn", i)
        # create context_name-lifespan pairs. If lifespan is set to 0, the context expires immediately
        contexts_dict = {"name": 1}
        reply = dialogflow.request(GetIntentRequest(session_id, contexts_dict))

        print("The detected intent:", reply.intent)

        if reply.fulfillment_message:
            text = reply.fulfillment_message
            print("Reply:", text)

            # send the fulfillment text to TTS for speech synthesis
            reply = tts.request(
                GetSpeechRequest(
                    text=text,
                    voice_name="en-US-Standard-C",
                    ssml_gender="FEMALE",
                )
            )
            mini.speaker.request(AudioRequest(reply.waveform, reply.sample_rate))

except KeyboardInterrupt:
    print("Stop the dialogflow component.")
    dialogflow.stop()
