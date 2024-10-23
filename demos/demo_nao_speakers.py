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


nao = Nao(ip="192.168.0.0")

print("Sending audio!")
sound = wavefile.readframes(wavefile.getnframes())
message = AudioMessage(sample_rate=samplerate, waveform=sound)
nao.speaker.send_message(message)

print("Audio sent, without waiting for it to complete playing.")
