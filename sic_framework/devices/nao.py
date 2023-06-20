import argparse
import os
from abc import ABCMeta

from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoqiAutonomousActuator, NaoqiAutonomous
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiMotionActuator, NaoqiMotion
from sic_framework.devices.common_naoqi.naoqi_camera import NaoqiTopCameraSensor, \
    NaoqiBottomCameraSensor, NaoqiTopCamera, \
    NaoqiBottomCamera
from sic_framework.devices.common_naoqi.naoqi_microphone import \
    NaoqiMicrophone, NaoqiMicrophoneSensor
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import NaoqiMotionRecorderActuator, \
    NaoqiMotionRecorderActuator, NaoqiMotionRecorder
from sic_framework.devices.common_naoqi.naoqi_motion_streamer import NaoqiMotionStreamerService, NaoqiMotionStreamer
from sic_framework.devices.common_naoqi.naoqi_stiffness import NaoqiStiffness, NaoqiStiffnessActuator
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import \
    NaoqiTextToSpeechActuator, NaoqiTextToSpeech
from sic_framework.devices.device import SICDevice


class Naoqi(SICDevice):
    __metaclass__ = ABCMeta

    def __init__(self, ip,
                 top_camera_conf=None,
                 bottom_camera_conf=None,
                 mic_conf=None,
                 motion_conf=None,
                 tts_conf=None,
                 motion_record_conf=None,
                 motion_stream_conf=None,
                 stiffness_conf=None,
                 ):
        super().__init__(ip)

        self.configs[NaoqiTopCamera] = top_camera_conf
        self.configs[NaoqiBottomCamera] = bottom_camera_conf
        self.configs[NaoqiMicrophone] = mic_conf
        self.configs[NaoqiMotionActuator] = motion_conf
        self.configs[NaoqiTextToSpeechActuator] = tts_conf
        self.configs[NaoqiMotionRecorder] = motion_record_conf
        self.configs[NaoqiMotionStreamer] = motion_stream_conf
        self.configs[NaoqiStiffness] = stiffness_conf

    @property
    def top_camera(self):
        return self._get_connector(NaoqiTopCamera)

    @property
    def bottom_camera(self):
        return self._get_connector(NaoqiBottomCamera)

    @property
    def mic(self):
        return self._get_connector(NaoqiMicrophone)

    @property
    def motion(self):
        return self._get_connector(NaoqiMotion)

    @property
    def tts(self):
        return self._get_connector(NaoqiTextToSpeech)

    @property
    def motion_record(self):
        return self._get_connector(NaoqiMotionRecorder)

    @property
    def motion_stream(self):
        return self._get_connector(NaoqiMotionStreamer)

    @property
    def stiffness(self):
        return self._get_connector(NaoqiStiffness)

    @property
    def autonomous(self):
        return self._get_connector(NaoqiAutonomous)


shared_naoqi_components = [
    NaoqiTopCameraSensor,
    NaoqiBottomCameraSensor,
    NaoqiMicrophoneSensor,
    NaoqiMotionActuator,
    NaoqiTextToSpeechActuator,
    NaoqiMotionRecorderActuator,
    NaoqiMotionStreamerService,
    NaoqiStiffnessActuator,
    NaoqiAutonomousActuator,
]


class Nao(Naoqi):
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis_ip', type=str, required=True,
                        help="IP address where Redis is running")
    args = parser.parse_args()

    os.environ['DB_IP'] = args.redis_ip

    nao_components = shared_naoqi_components + [
        # todo,
    ]

    SICComponentManager(nao_components)
