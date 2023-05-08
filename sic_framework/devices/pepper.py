import argparse

from sic_framework.core.component_manager_python2 import SICComponentManager, SICSensorManager
from sic_framework.devices.common_naoqi.nao_motion import NaoMotionActuator
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoCameraSensor, BottomNaoCameraSensor, StereoPepperCameraSensor, DepthPepperCameraSensor
from sic_framework.devices.common_naoqi.naoqi_microphone import NaoqiMicrophoneSensor
from sic_framework.devices.common_naoqi.naoqi_speakers import NaoqiTextToSpeechActuator
from sic_framework.devices.common_naoqi.pepper_tablet import NaoqiTabletService
from sic_framework.devices.device import SICDevice


class Pepper(SICDevice):
    @property
    def top_camera(self):
        return self._get_connector(TopNaoCameraSensor)

    @property
    def bottom_camera(self):
        return self._get_connector(BottomNaoCameraSensor)

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
    def text_to_speech(self):
        return self._get_connector(NaoqiTextToSpeechActuator)

    @property
    def tablet_load_url(self):
        return self._get_connector(NaoqiTabletService)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--robot_name', required=True, type=str, help="Provide a name for the robot to use as identifier")
    args = parser.parse_args()

    s = [
        TopNaoCameraSensor,
        BottomNaoCameraSensor,
        StereoPepperCameraSensor,
        DepthPepperCameraSensor,
        NaoqiMicrophoneSensor,
    ]
    sensors = SICSensorManager(s, args.robot_name)

    s = [
        NaoMotionActuator,
        NaoqiTextToSpeechActuator,
        NaoqiTabletService,

    ]

    actions = SICComponentManager(s, args.robot_name)
    try:
        actions.serve()
    except KeyboardInterrupt:
        sensors.shutdown()
        actions.shutdown()



"""
Robot exports

export DB_PASS=changemeplease
export DB_SSL_SELFSIGNED=1
export DB_IP=192.168.0.FOO
"""