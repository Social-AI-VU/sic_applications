"""
Google speech-to-text service should be running. You can start it with:

IMPORTANT
Google speech-to-text dependency needs to be installed and the service needs to be running:
1. pip install social-interaction-cloud[google-stt]
2. run-google-stt

NOTE: you need to have setup Cloud Speech-to-Text API in your Google Cloud Console and configure the credential keyfile.
See https://cloud.google.com/speech-to-text/v2/docs
"""

import json
from os.path import abspath, join
import time

from sic_framework.devices.desktop import Desktop
from sic_framework.services.speech2text.google_STT import (
    GoogleSpeechToText,
    GoogleSpeechToTextConf,
    GetStatementRequest,
)

# initialize the desktop device to get the microphone
desktop = Desktop()
desktop_mic = desktop.mic

# initialize the speech-to-text service
stt_conf = GoogleSpeechToTextConf(
    keyfile_json=json.load(open(abspath(join("..", "..", "conf", "google", "google-key.json")))),
    sample_rate_hertz=44100,
    language="en-US",
)

stt = GoogleSpeechToText(conf=stt_conf, input_source=desktop_mic)

# register a callback function to act upon arrival of recognition_result
def on_stt(result):
    transcript = result.response.alternatives[0].transcript
    # NOTE: uncomment to print interim results (before it detects that the user has finished speaking)
    # print("Interim result:\n", transcript)

# register a callback function to act upon arrival of recognition_result
stt.register_callback(callback=on_stt)

# Demo starts
print(" -- Starting Demo -- ")

for i in range(10):
    # For more info on what is returned, see Google's documentation on the response object:
    # https://cloud.google.com/php/docs/reference/cloud-speech/latest/V2.StreamingRecognizeResponse
    result = stt.request(GetStatementRequest())
    # alternative is a list of possible transcripts, we take the first one which is the most likely
    transcript = result.response.alternatives[0].transcript
    print("User said:\n", transcript)
