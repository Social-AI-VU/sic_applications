import time

import cv2
import pyaudio

from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices import Nao
from sic_framework.devices.common_desktop.desktop_camera import DesktopCamera
import queue

from sic_framework.devices.desktop import Desktop
from sic_framework.services.openai_whisper_speech_to_text.whisper_speech_to_text import SICWhisper, Transcript, \
    GetTranscript

""" 
This demo should display a camera image from your webcam on your laptop.
"""

# import speech_recognition as sr
#
# # obtain audio from the microphone
# print("mics", sr.Microphone.list_microphone_names())
# r = sr.Recognizer()
#
# device = pyaudio.PyAudio()
#
# p = pyaudio.PyAudio()
# for i in range(p.get_device_count()):
#     print(p.get_device_info_by_index(i))
#
# print("say something")
# with sr.Microphone() as source:
#     audio = r.listen(source, timeout=5)
#
# print("Transcribing")
# transcript = r.recognize_whisper(audio, language="english")
# print("Whisper thinks you said " + transcript)


def on_transcript(message: Transcript):
    print(message.transcript)


robot = Nao(ip="192.168.0.151")

whisper = SICWhisper()

whisper.connect(robot.mic)

time.sleep(1)


whisper.register_callback(on_transcript)

for i in range(10):
    print("Talk now!")
    transcript = whisper.request(GetTranscript())
    print("transcript", transcript.transcript)
print("done")