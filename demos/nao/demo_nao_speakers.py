"""
This script demonstrates how to use the Nao speakers to play a wav file.
"""

import wave

from sic_framework.core.message_python2 import AudioMessage, AudioRequest
from sic_framework.devices import Nao

# Read the wav file
wavefile = wave.open("test_sound_dialogflow.wav", "rb")
samplerate = wavefile.getframerate()

print("Audio file specs:")
print("  sample rate:", wavefile.getframerate())
print("  length:", wavefile.getnframes())
print("  data size in bytes:", wavefile.getsampwidth())
print("  number of chanels:", wavefile.getnchannels())
print()


nao = Nao(ip="XXX")

print("Sending audio!")
sound = wavefile.readframes(wavefile.getnframes())
message = AudioRequest(sample_rate=samplerate, waveform=sound)
nao.speaker.request(message)

print("Audio sent, without waiting for it to complete playing.")
