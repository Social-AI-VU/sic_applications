"""
This demo shows how to use Whisper to transcribe your speech to text,
either using a local model or the online OpenAI model by providing your API key

IMPORTANT
whisper service needs to be running:

1. pip install social-interaction-cloud[whisper-speech-to-text]
2. run-whisper

Requires you to have a secret OpenAI key, you can generate your personal openai api key here: https://platform.openai.com/api-keys
Put your key in a .openai_env file in the conf/openai folder as OPENAI_API_KEY="your key"
"""

import time
from os import environ
from os.path import abspath, join

from dotenv import load_dotenv
from sic_framework.devices.desktop import Desktop
from sic_framework.services.openai_whisper_stt.whisper_stt import (
    GetTranscript,
    SICWhisper,
    Transcript,
    WhisperConf,
)
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# In case you want to use the logger with a neat format as opposed to logger.info statements.
app = SICApplication()
logger = app.get_app_logger()

# can be DEBUG, INFO, WARNING, ERROR, CRITICAL
app.set_log_level(sic_logging.INFO)

# Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
# app.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")

# Use the shutdown event as a loop condition.
shutdown_flag = app.get_shutdown_event()

def on_transcript(message: Transcript):
    print(message.transcript)

desktop = Desktop()

load_dotenv(abspath(join("..", "..", "conf", "openai", ".openai_env")))
whisper_conf = WhisperConf(openai_key=environ["OPENAI_API_KEY"])
whisper = SICWhisper(input_source=desktop.mic, conf=whisper_conf)

# whisper = SICWhisper(input_source=desktop.mic)

time.sleep(1)

whisper.register_callback(on_transcript)

try:
    while not shutdown_flag.is_set():
        logger.info("Talk now!")
        transcript = whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
        logger.info("transcript: {transcript}".format(transcript=transcript.transcript))
except Exception as e:
    logger.error("Exception: ", e)
