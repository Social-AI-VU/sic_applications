import argparse

from sic_framework import SICComponentManager
from sic_framework.devices.common_desktop.desktop_camera import DesktopCamera, \
    DesktopCameraSensor
from sic_framework.devices.common_desktop.desktop_microphone import DesktopMicrophone, \
    DesktopMicrophoneSensor
from sic_framework.devices.common_desktop.desktop_speakers import DesktopSpeakers, \
    DesktopSpeakersActuator
from sic_framework.devices.device import SICDevice


class Desktop(SICDevice):
    def __init__(self, camera_conf=None, mic_conf=None, speakers_conf=None):
        super(Desktop, self).__init__(ip="127.0.0.1")

        self.configs[DesktopCamera] = camera_conf
        self.configs[DesktopMicrophone] = mic_conf
        self.configs[DesktopSpeakers] = speakers_conf

    @property
    def camera(self):
        return self._get_connector(DesktopCamera)

    @property
    def mic(self):
        return self._get_connector(DesktopMicrophone)

    @property
    def speakers(self):
        return self._get_connector(DesktopSpeakers)


if __name__ == '__main__':
    SICComponentManager([DesktopMicrophoneSensor, DesktopCameraSensor, DesktopSpeakersActuator])
