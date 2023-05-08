import logging
import time

from sic_framework.core.connector import SICApplication
from sic_framework.devices.desktop.desktop_speakers import DesktopSpeakers
from sic_framework.services.text2speech.text2speech_service import GetSpeechRequest, Text2SpeechConf, Text2Speech, SpeechResult


class DemoText2Speech(SICApplication):
    """
    This demo showcases the use of the Google Text-to-Speech API through the Text2Speech SICAction.
    It will play three sentences on your machine using different voices.
    """
    def run(self) -> None:
        conf = Text2SpeechConf(keyfile="/home/thomas/vu/SAIL/docker/sic/sic_framework/tests/sail-380610-0dea39e1a452.json")
        pepper_speaker = self.start_service(DesktopSpeakers, device_id='local', inputs_to_service=[tts])

        tts = self.start_service(Text2Speech, device_id='local')
        speaker = self.start_service(DesktopSpeakers, device_id='local', inputs_to_service=[tts])

        audio = tts.request(GetSpeechRequest(text="Hello, how are you?"))
        pepper_speaker.request(audio, block=False)


        tts.request(GetSpeechRequest(text="Hello, how are you?", voice_name="en-US-Neural2-G", ssml_gender="FEMALE"))
        tts.request(GetSpeechRequest(text="Hello, how are you?", voice_name="en-US-Neural2-I", ssml_gender="MALE"))

        print(audio)

        speaker.send_message(audio)

if __name__ == '__main__':
    test_app = DemoText2Speech()
    test_app.run()
    time.sleep(1000)
    test_app.stop()
