import json
import threading
import time
import wave

import pyaudio

from sic_framework.core.message_python2 import AudioMessage
from sic_framework.services.dialogflow.dialogflow import (DialogflowConf, GetIntentRequest, Dialogflow,
                                                          StopListeningMessage, RecognitionResult, QueryResult)


"""
NOTE: This is not the best way to transcribe audio.This demo is here for two reasons:

To provide a platform independent way to test your dialogflow setup

To demonstrate how to work with audio and dialogflow in the framework

The Dialogflow should be running. You can start it with:
[services/dialogflow] python dialogflow.py
"""

# Read the wav file

wavefile = wave.open('test_sound_dialogflow.wav', 'rb')
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
keyfile_json = json.load(open("dialogflow-test-project-wiggers.json"))
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

# To make dialogflow listen to the audio, we need to ask it to "listen for intent".
# This means it will try to determine what the intention is of what is being said by the person speaking.
# Instead of using this intent, we simply store the transcript and ask it to listen for intent again.

print("Listening for first sentence")
dialogflow.request(GetIntentRequest(), block=False)

# send the audio in chunks of one second
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

time.sleep(1)
dialogflow.send_message(StopListeningMessage())

print("\n\n")
print("Final transcript")
print(transcripts)

with open('transcript.txt', 'w') as f:
    for line in transcripts:
        f.write(f"{line}\n")

output.close()
p.terminate()

dialogflow.stop()