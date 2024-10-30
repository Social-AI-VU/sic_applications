import time
from os import environ
from os.path import abspath, join

from dotenv import load_dotenv
from sic_framework.devices.desktop import Desktop
from sic_framework.services.openai_whisper_speech_to_text.whisper_speech_to_text import (
    GetTranscript,
    SICWhisper,
    Transcript,
    WhisperConf,
)

"""
This demo shows how to use Whisper to transcribe your speech to text,
either using a local model or the online OpenAI model by providing your API key

IMPORTANT
whisper service needs to be running:

1. pip install social-interaction-cloud[whisper-speech-to-text]
2. run-whisper

"""


def on_transcript(message: Transcript):
    print(message.transcript)


desktop = Desktop()

# if you have a secret OpenAI key, you can pass it here
# Generate your personal openai api key here: https://platform.openai.com/api-keys
# Either add your openai key to your systems variables (and don't uncomment the first line) or
# create a .openai_env file in the conf/openai folder and add your key there like this:
# OPENAI_API_KEY="your key"
# load_dotenv(abspath(join("..", "..", "conf", "openai", ".openai_env")))
#
# whisper_conf = WhisperConf(openai_key=environ["OPENAI_API_KEY"])
# whisper = SICWhisper(conf=whisper_conf)

whisper = SICWhisper()

whisper.connect(desktop.mic)

time.sleep(1)

whisper.register_callback(on_transcript)

for i in range(10):
    print("Talk now!")
    transcript = whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
    print("transcript", transcript.transcript)
print("done")
