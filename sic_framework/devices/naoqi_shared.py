from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoqiAutonomousActuator, NaoqiAutonomous
from sic_framework.devices.common_naoqi.naoqi_leds import NaoqiLEDs, \
    NaoqiLEDsActuator
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiMotionActuator, NaoqiMotion
from sic_framework.devices.common_naoqi.naoqi_camera import NaoqiTopCameraSensor, \
    NaoqiBottomCameraSensor, NaoqiTopCamera, \
    NaoqiBottomCamera
from sic_framework.devices.common_naoqi.naoqi_microphone import \
    NaoqiMicrophone, NaoqiMicrophoneSensor
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import NaoqiMotionRecorderActuator, NaoqiMotionRecorder
from sic_framework.devices.common_naoqi.naoqi_motion_streamer import NaoqiMotionStreamerService, NaoqiMotionStreamer
from sic_framework.devices.common_naoqi.naoqi_speakers import NaoqiSpeakerComponent, NaoqiSpeaker
from sic_framework.devices.common_naoqi.naoqi_stiffness import NaoqiStiffnessActuator, NaoqiStiffness
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import \
    NaoqiTextToSpeechActuator, NaoqiTextToSpeech
from sic_framework.devices.device import SICDevice
from abc import ABCMeta


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
    NaoqiLEDsActuator,
    NaoqiSpeakerComponent,
]


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
                 speaker_conf=None,
                 ):
        super().__init__(ip)

        self.configs[NaoqiTopCamera] = top_camera_conf
        self.configs[NaoqiBottomCamera] = bottom_camera_conf
        self.configs[NaoqiMicrophone] = mic_conf
        self.configs[NaoqiMotionActuator] = motion_conf
        self.configs[NaoqiTextToSpeechActuator] = tts_conf
        self.configs[NaoqiMotionRecorder] = motion_record_conf
        self.configs[NaoqiMotionStreamer] = motion_stream_conf
        self.configs[NaoqiStiffnessActuator] = stiffness_conf
        self.configs[NaoqiSpeakerComponent] = speaker_conf

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

    @property
    def leds(self):
        return self._get_connector(NaoqiLEDs)

    @property
    def speaker(self):
        return self._get_connector(NaoqiSpeaker)



if __name__ == "__main__":
    pass
