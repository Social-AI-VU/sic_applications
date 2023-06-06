import argparse
import os

from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.devices.common_naoqi.nao_motion import NaoMotionActuator
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoqiCameraSensor, \
    BottomNaoqiCameraSensor, TopNaoqiCamera, \
    BottomNaoqiCamera
from sic_framework.devices.common_naoqi.naoqi_microphone import \
    NaoqiMicrophone, NaoqiMicrophoneSensor
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import NaoqiMotionRecorderActuator, \
    NaoMotionRecorderActuator
from sic_framework.devices.common_naoqi.naoqi_motion_streamer import NaoMotionStreamerService
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import \
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
        return self._get_connector(TopNaoqiCamera)

    @property
    def bottom_camera(self):
        return self._get_connector(BottomNaoqiCamera)

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
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis_ip', type=str, required=True,
                        help="IP address where Redis is running")
    args = parser.parse_args()

    os.environ['DB_IP'] = args.redis_ip

    s = [
        TopNaoqiCameraSensor,
        BottomNaoqiCameraSensor,
        NaoqiMicrophoneSensor,
        NaoqiTextToSpeechActuator,
        NaoMotionActuator,
        NaoMotionRecorderActuator,
        NaoMotionStreamerService,
    ]
    SICComponentManager(s)
