from sic_framework import SICApplication
from sic_framework.devices.common_naoqi.naoqi_speakers import NaoqiTextToSpeechActuator, NaoqiTextToSpeechRequest

""" 
This demo should make the nao say something
"""


class DemoTextToSpeech(SICApplication):

    def run(self) -> None:
        nao3_action = self.start_service(NaoqiTextToSpeechActuator, device_id='nao')
        nao3_action.request(NaoqiTextToSpeechRequest("Hello world!"))


if __name__ == '__main__':
    test_app = DemoTextToSpeech()
    test_app.run()
