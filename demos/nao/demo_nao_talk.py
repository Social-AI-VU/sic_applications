from time import sleep

from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoWakeUpRequest, NaoRestRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import (
    NaoqiTextToSpeechRequest,
)


class NaoTalkDemo:

    def __init__(self, ip: str):
        self.nao = Nao(ip=ip)  # adjust this to the IP address of your robot.

    def say(self):
        self.nao.tts.request(NaoqiTextToSpeechRequest("Say."))
        self.nao.tts.request(NaoqiTextToSpeechRequest("Hello, I am a Nao robot!"))

    def say_animated(self):
        self.nao.tts.request(NaoqiTextToSpeechRequest("Animated Say."))
        self.nao.tts.request(NaoqiTextToSpeechRequest("Hello, I am a Nao robot! And I like to chat.", animated=True))

    def say_with_gesture(self):
        self.nao.tts.request(NaoqiTextToSpeechRequest("Say and gesture."))
        self.nao.tts.request(NaoqiTextToSpeechRequest("Hello, I am a Nao robot! And I like to chat."), block=False)
        self.nao.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Hey_1"))

    def wakeup(self):
        self.nao.autonomous.request(NaoWakeUpRequest())

    def rest(self):
        self.nao.autonomous.request(NaoRestRequest())


if __name__ == '__main__':
    nao_talk = NaoTalkDemo(ip="10.0.0.?")
    nao_talk.wakeup()
    nao_talk.say()
    sleep(2)
    nao_talk.say_animated()
    sleep(2)
    nao_talk.say_with_gesture()
    sleep(2)
    nao_talk.rest()
