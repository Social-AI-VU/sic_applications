import argparse

from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.devices.common_naoqi.nao_motion import NaoMotionActuator
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoCameraSensor, BottomNaoCameraSensor, TopNaoCamera, \
    BottomNaoCamera
from sic_framework.devices.common_naoqi.naoqi_microphone import \
    NaoqiMicrophone, NaoqiMicrophoneSensor
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import NaoMotionRecorderActuator
from sic_framework.devices.common_naoqi.naoqi_speakers import \
    NaoqiTextToSpeechActuator, NaoqiTextToSpeech
from sic_framework.devices.device import SICDevice


class NaoLite(object):
    def __init__(self, ip):
        self.ip = ip

    def mic(self, *args, **kwargs):
        return NaoqiMicrophone(self.ip, *args, **kwargs)

    def tts(self, *args, **kwargs):
        return NaoqiTextToSpeech(self.ip, *args, **kwargs)


class Nao(SICDevice):
    @property
    def top_camera(self):
        return self._get_connector(TopNaoCamera)

    @property
    def bottom_camera(self):
        return self._get_connector(BottomNaoCamera)

    @property
    def mic(self):
        return self._get_connector(NaoqiMicrophone)

    @property
    def motion(self):
        return self._get_connector(NaoMotionActuator)

    @property
    def tts(self):
        return self._get_connector(NaoqiTextToSpeechActuator)


if __name__ == '__main__':
    s = [
        TopNaoCameraSensor,
        BottomNaoCameraSensor,
        NaoqiMicrophoneSensor,
        NaoqiTextToSpeechActuator,
        NaoMotionActuator,
        NaoMotionRecorderActuator
    ]
    SICComponentManager(s)
    #
    # s = [
    #     NaoMotionStreamConsumer,
    #     NaoMotionStreamProducer,
    # ]


