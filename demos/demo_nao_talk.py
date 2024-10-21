from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest

nao = Nao(ip='192.168.2.7') # adjust this to the IP adress of your robot.

nao.tts.request(NaoqiTextToSpeechRequest("Hello!"))
