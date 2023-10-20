import argparse
import atexit
import threading
import time

from sic_framework import SICComponentManager
from sic_framework.devices.common_desktop.desktop_camera import DesktopCamera, \
    DesktopCameraSensor
from sic_framework.devices.common_desktop.desktop_microphone import DesktopMicrophone, \
    DesktopMicrophoneSensor
from sic_framework.devices.common_desktop.desktop_speakers import DesktopSpeakers, \
    DesktopSpeakersActuator
from sic_framework.devices.common_desktop.desktop_text_to_speech import DesktopTextToSpeechActuator, DesktopTextToSpeech
from sic_framework.devices.device import SICDevice

desktop_active = False


def start_desktop_components():
    manager = SICComponentManager(desktop_component_list,
                                  auto_serve=False)

    atexit.register(manager.stop)

    from contextlib import redirect_stderr
    with redirect_stderr(None):
        manager.serve()


class Desktop(SICDevice):
    def __init__(self, camera_conf=None, mic_conf=None, speakers_conf=None, tts_conf=None):
        super(Desktop, self).__init__(ip="127.0.0.1")

        self.configs[DesktopCamera] = camera_conf
        self.configs[DesktopMicrophone] = mic_conf
        self.configs[DesktopSpeakers] = speakers_conf
        self.configs[DesktopTextToSpeech] = tts_conf

        global desktop_active

        if not desktop_active:
            # run the component manager in a thread
            thread = threading.Thread(target=start_desktop_components, name="DesktopComponentManager-singelton")
            thread.start()

            desktop_active = True

    @property
    def camera(self):
        return self._get_connector(DesktopCamera)

    @property
    def mic(self):
        return self._get_connector(DesktopMicrophone)

    @property
    def speakers(self):
        return self._get_connector(DesktopSpeakers)

    @property
    def tts(self):
        return self._get_connector(DesktopTextToSpeech)


desktop_component_list = [DesktopMicrophoneSensor, DesktopCameraSensor, DesktopSpeakersActuator,
                          DesktopTextToSpeechActuator]

if __name__ == '__main__':
    SICComponentManager(desktop_component_list)
