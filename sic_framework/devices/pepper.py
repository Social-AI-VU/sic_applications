import argparse
import os

from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.devices.common_naoqi.nao_motion import NaoMotionActuator
from sic_framework.devices.common_naoqi.naoqi_autonomous import \
    NaoqiAutonomousActuator
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoqiCameraSensor, BottomNaoqiCameraSensor, \
    StereoPepperCameraSensor, DepthPepperCameraSensor
from sic_framework.devices.common_naoqi.naoqi_lookat import NaoqiLookAtComponent
from sic_framework.devices.common_naoqi.naoqi_microphone import NaoqiMicrophoneSensor
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import NaoMotionRecorderActuator, \
    PepperMotionRecorderActuator
from sic_framework.devices.common_naoqi.naoqi_motion_streamer import NaoMotionStreamerService
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechActuator
from sic_framework.devices.common_naoqi.pepper_tablet import NaoqiTabletService
from sic_framework.devices.device import SICDevice


class Pepper(SICDevice):
    @property
    def top_camera(self):
        return self._get_connector(TopNaoqiCameraSensor)

    @property
    def bottom_camera(self):
        return self._get_connector(BottomNaoqiCameraSensor)

    @property
    def stereo_camera(self):
        return self._get_connector(StereoPepperCameraSensor)

    @property
    def depth_camera(self):
        return self._get_connector(DepthPepperCameraSensor)

    @property
    def mic(self):
        return self._get_connector(NaoMotionActuator)

    @property
    def autonomous(self):
        return self._get_connector(NaoqiAutonomousActuator)

    @property
    def text_to_speech(self):
        return self._get_connector(NaoqiTextToSpeechActuator)

    @property
    def tablet_load_url(self):
        return self._get_connector(NaoqiTabletService)


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
        NaoMotionActuator,  # TODO make pepper variant
        NaoqiAutonomousActuator,
        PepperMotionRecorderActuator,
        NaoMotionStreamerService,  # TODO make pepper variant
        NaoqiLookAtComponent,
        # NaoqiTabletService,
        # DepthPepperCameraSensor,
        # StereoPepperCameraSensor,

    ]
    SICComponentManager(s)
