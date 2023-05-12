import io
import time

import cv2
import numpy as np
import wavio
from matplotlib import pyplot as plt
from sic_framework import SICApplication

import tqdm
from sic_framework.core.message_python2 import AudioMessage
from sic_framework.devices.common_naoqi.naoqi_microphone import NaoqiMicrophoneSensor
from sic_framework.devices.desktop.desktop_speakers import DesktopSpeakers
from sic_framework.devices.desktop.desktop_microphone import DesktopMicrophone

""" This demo should display a camera image
"""




class DemoMicrophone(SICApplication):

    def function(self, audio):
        print("audio", audio.waveform)

    def run(self) -> None:
        #### use camera

        mic = test_app.start_service(DesktopMicrophone, device_id='local')

        self.speaker = self.start_service(DesktopSpeakers, device_id='local', inputs_to_service=[mic])



        mic.register_callback(self.function)

        time.sleep(10)


if __name__ == '__main__':
    test_app = DemoMicrophone()

    test_app.run()
    test_app.stop()

"""
Robot exports

export DB_PASS=changemeplease
export DB_SSL_SELFSIGNED=1
export DB_IP=192.168.0.FOO
"""
