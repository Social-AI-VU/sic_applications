import json
import threading
import wave

import pyaudio

from sic_framework.core.message_python2 import AudioMessage
from sic_framework.services.dialogflow.dialogflow import DialogflowConf, GetIntentRequest, Dialogflow, \
    StopListeningMessage

# Read the wav file

wavefile = wave.open('office_top_short.wav', 'rb')
samplerate = wavefile.getframerate()

print("Audio file specs:")
print("  sample rate:", wavefile.getframerate())
print("  length:", wavefile.getnframes())
print("  data size in bytes:", wavefile.getsampwidth())
print("  number of chanels:", wavefile.getnchannels())
print()


# set up the callback and variables to contain the transcript results
# Dialogflow is not made for transcribing, so we'll have to work around this by "faking" a conversation

dialogflow_detected_sentence = threading.Event()
transcripts = []


def on_dialog(message):
    if message.response:
        t = message.response.recognition_result.transcript
        print("\r Transcript:", t, end="")

        if message.response.recognition_result.is_final:
            transcripts.append(t)
            dialogflow_detected_sentence.set()


# read you keyfile and connect to dialogflow
keyfile_json = json.load(open("your_keyfile_here.json"))
conf = DialogflowConf(keyfile_json=keyfile_json,
                      sample_rate_hertz=samplerate, )
dialogflow = Dialogflow(conf=conf)
dialogflow.register_callback(on_dialog)

# OPTIONAL: set up output device to play audio along transcript

p = pyaudio.PyAudio()
output = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=samplerate,
                output=True)

print("Listening for first sentence")
dialogflow.request(GetIntentRequest(), block=False)

for i in range(wavefile.getnframes() // wavefile.getframerate()):

    if dialogflow_detected_sentence.is_set():
        print()
        dialogflow.request(GetIntentRequest(), block=False)

        dialogflow_detected_sentence.clear()

    # grab one second of audio data
    chunk = wavefile.readframes(samplerate)

    output.write(chunk)  # replace with time.sleep to not send audio too fast if not playing audio

    message = AudioMessage(sample_rate=samplerate, waveform=chunk)
    dialogflow.send_message(message)

dialogflow.send_message(StopListeningMessage())

print("\n\n")
print("Final transcript")
print(transcripts)

with open('transcript.txt', 'w') as f:
    for line in transcripts:
        f.write(f"{line}\n")

output.close()
p.terminate()


