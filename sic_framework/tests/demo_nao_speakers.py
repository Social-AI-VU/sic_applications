import json
import threading
import time
import wave
from typing import io

import pyaudio

from sic_framework.core.message_python2 import AudioMessage, AudioRequest
from sic_framework.devices import Pepper
from sic_framework.services.dialogflow.dialogflow import DialogflowConf, GetIntentRequest, Dialogflow, \
    StopListeningMessage

# Read the wav file

wavefile = wave.open('test_sound_dialogflow.wav', 'rb')
samplerate = wavefile.getframerate()

print("Audio file specs:")
print("  sample rate:", wavefile.getframerate())
print("  length:", wavefile.getnframes())
print("  data size in bytes:", wavefile.getsampwidth())
print("  number of chanels:", wavefile.getnchannels())
print()

pepper = Pepper(ip="192.168.0.197")





print("Sending audio!")

# bugged
# sound = wavefile.readframes(wavefile.getnframes())
# message = AudioRequest(sample_rate=samplerate, waveform=sound)
# pepper.speaker.request(message)

# print("Audio is done playing!")


sound = wavefile.readframes(wavefile.getnframes())
message = AudioMessage(sample_rate=samplerate, waveform=sound)
pepper.speaker.send_message(message)

print("Audio sent, without waiting for it to complete playing.")






