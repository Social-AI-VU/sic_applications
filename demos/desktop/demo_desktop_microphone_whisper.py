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

def on_transcript(message: Transcript):
    print(message.transcript)

desktop = Desktop()

load_dotenv(abspath(join("..", "..", "conf", "openai", ".openai_env")))
whisper_conf = WhisperConf(openai_key=environ["OPENAI_API_KEY"])
whisper = SICWhisper(input_source=desktop.mic, conf=whisper_conf)

# whisper = SICWhisper(input_source=desktop.mic)

time.sleep(1)

whisper.register_callback(on_transcript)

for i in range(10):
    print("Talk now!")
    transcript = whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
    print("transcript: ", transcript.transcript)
print("done")
