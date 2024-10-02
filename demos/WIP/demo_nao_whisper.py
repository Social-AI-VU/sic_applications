import json
import threading
import time
import wave
from tempfile import NamedTemporaryFile
from typing import io

import pyaudio
import torch

from sic_framework.core.message_python2 import AudioMessage, AudioRequest
from sic_framework.devices import Pepper, Nao
from sic_framework.services.dialogflow.dialogflow import DialogflowConf, GetIntentRequest, Dialogflow, \
    StopListeningMessage

# Read the wav file

wavefile = wave.open('../test_sound_dialogflow.wav', 'rb')
samplerate = wavefile.getframerate()

print("Audio file specs:")
print("  sample rate:", wavefile.getframerate())
print("  length:", wavefile.getnframes())
print("  data size in bytes:", wavefile.getsampwidth())
print("  number of chanels:", wavefile.getnchannels())
print()

robot = Nao(ip="192.168.0.151")

audio_bytes = b""
def on_audio(audio_message):
    global audio_bytes
    audio_bytes += audio_message.waveform

robot.mic.register_callback(on_audio)
print("start talking")

import whisper

model = whisper.load_model("base.en")

from pydub import AudioSegment

# AudioSegment.from_wav("test_sound_dialogflow.wav").export("audio.mp3", format="mp3")
#
# start = time.time()
# result = model.transcribe("audio.mp3")
# print(time.time() - start)
#
# print("result", result)

time.sleep(2)
print("Sending audio!")


# Write wav data to the temporary file as bytes.
temp_file = NamedTemporaryFile().name
with wave.open(temp_file, 'wb') as f:
    f.setnchannels(1)
    f.setsampwidth(2)  # number of bytes
    f.setframerate(16000)
    f.writeframesraw(audio_bytes)



# Read the transcription.
result = model.transcribe(temp_file, fp16=torch.cuda.is_available())
text = result['text'].strip()
print(text)

# bugged
# sound = wavefile.readframes(wavefile.getnframes())
# message = AudioRequest(sample_rate=samplerate, waveform=sound)
# pepper.speaker.request(message)

# print("Audio is done playing!")

#
# sound = wavefile.readframes(wavefile.getnframes())
# message = AudioMessage(sample_rate=samplerate, waveform=sound)
# pepper.tts.request(message)
#
# print("Audio sent, without waiting for it to complete playing.")






