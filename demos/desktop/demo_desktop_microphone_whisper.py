import time

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
# with open("openai_key", "rb") as f:
#     openai_key = f.read()
#     openai_key = openai_key.decode("utf-8").strip()

# whisper_conf = WhisperConf(openai_key=openai_key)
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
