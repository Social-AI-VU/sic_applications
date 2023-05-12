import argparse
from sic_framework import SICSensorManager
from sic_framework.devices.desktop.desktop_camera import DesktopCamera, \
    DesktopCameraSensor
from sic_framework.devices.desktop.desktop_microphone import DesktopMicrophone, \
    DesktopMicrophoneSensor
from sic_framework.devices.desktop.desktop_speakers import DesktopSpeakers, \
    DesktopSpeakersActuator
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
    SICSensorManager([DesktopMicrophoneSensor, DesktopCameraSensor, DesktopSpeakersActuator])
