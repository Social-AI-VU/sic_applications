"""
Google text2speech service should be running. You can start it with:

IMPORTANT
Google text2speech dependency needs to be installed and the service needs to be running:
1. pip install social-interaction-cloud[google-tts]
2. run-google-tts

NOTE: you need to have setup Cloud Text-to-Speech API in your Google Cloud Console and configure the credential keyfile.
See https://console.cloud.google.com/apis/api/texttospeech.googleapis.com/
"""

import json
from os.path import abspath, join

from sic_framework.core.message_python2 import AudioRequest
from sic_framework.devices.desktop import Desktop
from sic_framework.services.text2speech.text2speech_service import (
    GetSpeechRequest,
    Text2Speech,
    Text2SpeechConf,
)

# initialize the text2speech service
tts_conf = Text2SpeechConf(
    keyfile_json=json.load(open(abspath(join("..", "..", "conf", "dialogflow", "dialogflow-key.json"))))
)
tts = Text2Speech(conf=tts_conf)
reply = tts.request(
    GetSpeechRequest(text="Hi, I am an alphamini", voice_name="en-US-Standard-C")
)

# initialize the desktop device to play the audio
desktop = Desktop()

# TODO the voice is high pitched, maybe it's due to sample rate mismatch
desktop.speakers.request(AudioRequest(reply.waveform, reply.sample_rate))
