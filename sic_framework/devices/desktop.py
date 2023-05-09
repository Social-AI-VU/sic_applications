import argparse

from sic_framework import SICComponentManager
from sic_framework.devices.desktop.desktop_camera import DesktopCamera, \
    DesktopCameraSensor
from sic_framework.devices.desktop.desktop_microphone import DesktopMicrophone, \
    DesktopMicrophoneSensor
from sic_framework.devices.desktop.desktop_speakers import DesktopSpeakers, \
    DesktopSpeakersSensor
from sic_framework.devices.device import SICDevice


class Desktop(SICDevice):
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
    SICComponentManager([DesktopMicrophoneSensor, DesktopCameraSensor, DesktopSpeakersSensor])
