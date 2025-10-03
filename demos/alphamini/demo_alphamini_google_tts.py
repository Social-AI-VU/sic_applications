
"""
This demo shows how to use the Google Text2Speech service to have the alphamini speak.

Google Text2Speech service should be running. You can start it with: run-google-tts

NOTE: you need to have setup Cloud Text-to-Speech API in your Google Cloud Console and configure the credential keyfile.
See https://social-ai-vu.github.io/social-interaction-cloud/tutorials/6_google_cloud.html
save the file in conf/google/google-key.json
"""

from os.path import abspath, join
import json

from sic_framework.core.message_python2 import AudioMessage, AudioRequest
from sic_framework.services.google_tts.google_tts import Text2Speech, Text2SpeechConf, GetSpeechRequest, SpeechResult
from sic_framework.devices.alphamini import Alphamini
from sic_framework.devices.common_mini.mini_speaker import MiniSpeakersConf
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Create the SICApplication instance to be able to use the logger and the shutdown event
app = SICApplication()
logger = app.get_app_logger()
app.set_log_level(sic_logging.DEBUG)

try:

    tts_conf = Text2SpeechConf(keyfile_json=json.load(open(abspath(join('..', '..', 'conf', 'google', 'google-key.json')))))
    tts = Text2Speech(conf=tts_conf)
# 
    reply = tts.request(GetSpeechRequest(text="Hi, I am an alphamini", voice_name="en-US-Standard-C", ssml_gender="FEMALE"))
    logger.info("Initializing Alphamini...")

    mini = Alphamini(ip="XXX", mini_id="000XXX", mini_password="mini", redis_ip="XXX", speaker_conf=MiniSpeakersConf(sample_rate=reply.sample_rate))

    logger.info("Alphamini speaking...")
    reply = mini.speaker.request(AudioRequest(reply.waveform, reply.sample_rate))

except Exception as e:
    logger.error("Exception: {}".format(e))
finally:
    app.shutdown()