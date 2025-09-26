"""
Google text2speech service should be running. You can start it with:

IMPORTANT
Google text2speech dependency needs to be installed and the service needs to be running:
1. pip install social-interaction-cloud[google-tts]
2. run-google-tts (in a separate terminal)

NOTE: you need to have setup Cloud Text-to-Speech API in your Google Cloud Console and configure the credential keyfile.
See https://social-ai-vu.github.io/social-interaction-cloud/tutorials/6_google_cloud.html
"""

import json
import time
from os.path import abspath, join

from sic_framework.core.message_python2 import AudioRequest
from sic_framework.devices.desktop import Desktop
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.services.google_tts.google_tts import (
    GetSpeechRequest,
    Text2Speech,
    Text2SpeechConf,
)
from sic_framework.core.sic_application import (
    set_log_level,
    set_log_file,
    get_app_logger
)
from sic_framework.core import sic_logging

# In case you want to use the logger with a neat format as opposed to print statements.
logger = get_app_logger()

# can be DEBUG, INFO, WARNING, ERROR, CRITICAL
set_log_level(sic_logging.INFO)

# Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
# set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")

# initialize the text2speech service
tts_conf = Text2SpeechConf(
    keyfile_json=json.load(open(abspath(join("..", "..", "conf", "google", "google-key.json"))))
)
tts = Text2Speech(conf=tts_conf)
reply = tts.request(
    GetSpeechRequest(text="Hi, I am your computer", voice_name="en-US-Standard-C")
)

# Make sure that the sample rate of the speakers is the same as the sample rate of the audio from Google
desktop = Desktop(speakers_conf=SpeakersConf(sample_rate=reply.sample_rate))

response = desktop.speakers.request(AudioRequest(reply.waveform, reply.sample_rate))