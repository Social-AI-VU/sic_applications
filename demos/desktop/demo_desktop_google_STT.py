"""
Google speech-to-text service should be running. You can start it with:

IMPORTANT
Google speech-to-text dependency needs to be installed and the service needs to be running:
1. pip install social-interaction-cloud[google-stt]
2. run-google-stt

NOTE: you need to have setup Cloud Speech-to-Text API in your Google Cloud Console and configure the credential keyfile.
See https://social-ai-vu.github.io/social-interaction-cloud/tutorials/6_google_cloud.html
"""

import json
from os.path import abspath, join
import time

from sic_framework.devices.desktop import Desktop
from sic_framework.services.google_stt.google_stt import (
    GoogleSpeechToText,
    GoogleSpeechToTextConf,
    GetStatementRequest,
)
from sic_framework.core.sic_application import (
    set_log_level,
    set_log_file,
    get_app_logger, 
    get_shutdown_event
)
from sic_framework.core import sic_logging

# In case you want to use the logger with a neat format as opposed to print statements.
logger = get_app_logger()

# can be DEBUG, INFO, WARNING, ERROR, CRITICAL
set_log_level(sic_logging.INFO)

# Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
# set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")

# Use the shutdown event as a loop condition.
shutdown_flag = get_shutdown_event()

# initialize the desktop device to get the microphone
desktop = Desktop()
desktop_mic = desktop.mic

# initialize the speech-to-text service
stt_conf = GoogleSpeechToTextConf(
    keyfile_json=json.load(open(abspath(join("..", "..", "conf", "google", "google-key.json")))),
    sample_rate_hertz=44100,
    language="en-US",
    interim_results=False,
)

stt = GoogleSpeechToText(conf=stt_conf, input_source=desktop_mic)

# register a callback function to act upon arrival of recognition_result
def on_stt(result):
    transcript = result.response.alternatives[0].transcript
    print("Interim result:\n", transcript)

# register a callback function to act upon arrival of recognition_result
stt.register_callback(callback=on_stt)

# Demo starts
print(" -- Starting Demo -- ")

try:
    while not shutdown_flag.is_set():
        # For more info on what is returned, see Google's documentation on the response object:
        # https://cloud.google.com/php/docs/reference/cloud-speech/latest/V2.StreamingRecognizeResponse
        result = stt.request(GetStatementRequest())
        if not result or not hasattr(result.response, 'alternatives') or not result.response.alternatives:
            print("No transcript received")
            continue
        # alternative is a list of possible transcripts, we take the first one which is the most likely
        transcript = result.response.alternatives[0].transcript
        print("User said:\n", transcript)
        # Small delay between requests to allow proper cleanup
        time.sleep(0.1)
except Exception as e:
    print("Exception: ", e)