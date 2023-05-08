import argparse

from sic_framework.core.component_manager_python2 import SICComponentManager, SICSensorManager
from sic_framework.devices.common_naoqi.nao_motion import NaoMotionActuator
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoCameraSensor, BottomNaoCameraSensor, TopNaoCamera, \
    BottomNaoCamera
from sic_framework.devices.common_naoqi.naoqi_microphone import NaoqiMicrophoneSensor
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import NaoMotionRecorderAction, NaoMotionReplayAction
from sic_framework.devices.common_naoqi.naoqi_motion_streamer import NaoMotionStreamConsumer, NaoMotionStreamProducer
from sic_framework.devices.common_naoqi.naoqi_speakers import NaoqiTextToSpeechActuator
from sic_framework.devices.device import SICDevice


class Nao(SICDevice):
    @property
    def top_camera(self):
        return self._get_connector(TopNaoCamera)

    @property
    def bottom_camera(self):
        return self._get_connector(BottomNaoCamera)

    @property
    def mic(self):
        return self._get_connector(NaoqiMicrophoneSensor)

    @property
    def motion(self):
        return self._get_connector(NaoMotionActuator)

    @property
    def tts(self):
        return self._get_connector(NaoqiTextToSpeechActuator)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--robot_name', required=True, type=str,
                        help="Provide a name for the robot to use as identifier")
    args = parser.parse_args()

    s = [
        TopNaoCameraSensor,
        BottomNaoCameraSensor,
        NaoqiMicrophoneSensor,
    ]
    sensors = SICSensorManager(s, args.robot_name)

    s = [
        NaoMotionActuator,
        NaoqiTextToSpeechActuator,
        NaoMotionStreamConsumer,
        NaoMotionStreamProducer,
        NaoMotionRecorderAction,
        NaoMotionReplayAction,
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
export DB_IP=192.168.0.FOO
"""
