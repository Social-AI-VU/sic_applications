"""
This script demonstrates how to use the Nao TTS to say something.
"""

from time import sleep

from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoWakeUpRequest, NaoRestRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiAnimationRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import (
    NaoqiTextToSpeechRequest,
)
from sic_framework.core.sic_application import (
    set_log_level,
    set_log_file,
    get_app_logger, 
    get_shutdown_event
)
from sic_framework.core import sic_logging

# In case you want to use the logger with a neat format as opposed to logger.info statements.
logger = get_app_logger()

# can be DEBUG, INFO, WARNING, ERROR, CRITICAL
set_log_level(sic_logging.DEBUG)

# Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
# set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")

# Use the shutdown event as a loop condition.
shutdown_flag = get_shutdown_event()


class NaoTalkDemo:

    def __init__(self, ip: str):
        # adjust this to the IP address of your robot.
        # self.nao = Nao(ip="XXX")
        # nao = Nao(ip="10.0.0.222", dev_test=True, test_repo="/Users/apple/Desktop/SAIL/SIC_Development/social-interaction-cloud")
        self.nao = Nao(ip="10.0.0.222", dev_test=True)


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
    nao_talk = NaoTalkDemo(ip="XXX")
    nao_talk.wakeup()
    nao_talk.say()
    sleep(2)
    nao_talk.say_animated()
    sleep(2)
    nao_talk.say_with_gesture()
    sleep(2)
    nao_talk.rest()
