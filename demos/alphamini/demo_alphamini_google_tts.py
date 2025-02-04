from os.path import abspath, join

from sic_framework.core.message_python2 import AudioMessage, AudioRequest
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.devices.desktop import Desktop
from sic_framework.services.text2speech.text2speech_service import Text2Speech, Text2SpeechConf, GetSpeechRequest, SpeechResult
from sic_framework.devices.minirobot import MiniRobot
from sic_framework.devices.common_mini.mini_speaker import MiniSpeakersConf


"""
Google Text2Speech service should be running. You can start it with:
[services/text2speech] python text2speech_service.py 

NOTE: you need to have setup Cloud Text-to-Speech API in your Google Cloud Console and configure the credential keyfile.
See https://console.cloud.google.com/apis/api/texttospeech.googleapis.com/ 
save the file in conf/dialogflow/google_tts_keyfile.json
"""

tts_conf = Text2SpeechConf(keyfile=abspath(join('..', '..', 'conf', 'dialogflow', 'google_tts_keyfile.json')))
tts = Text2Speech(conf=tts_conf)
reply = tts.request(GetSpeechRequest(text="Hallo, Ik ben een alphamini", voice_name="nl-NL-Standard-G", ssml_gender="NEUTRAL"))
mini = MiniRobot(speaker_conf=MiniSpeakersConf(sample_rate=reply.sample_rate))
mini.speaker.request(AudioRequest(reply.waveform, reply.sample_rate))
