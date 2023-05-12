import logging
import time

from sic_framework import SICApplication
from sic_framework.devices.common_naoqi.naoqi_speakers import NaoqiTextToSpeechActuator, NaoqiTextToSpeechRequest

""" This demo should display a camera image
"""


class DemoTextToSpeech(SICApplication):

    def run(self) -> None:
        # nao3_action = self.connect(NaoqiTextToSpeechAction, device_id='nao')
        #
        # start = time.time()
        # nao3_action.request(NaoqiTextToSpeechRequest("Hi, im nao!"))
        # print("duration {}".format(time.time() - start))

        names = ["nao1", "nao2", "nao3", "nao4"]
        names = [
            "192.168.0.236",
            "192.168.0.209",
            "192.168.0.238",
            "192.168.0.121",
            "192.168.0.135",
            "192.168.0.191",
            "192.168.0.106",
            "192.168.0.183",
            "192.168.0.226",
            "192.168.0.237",
        ]

        motions = []
        for nao in names:
            motion = self.start_service(NaoqiTextToSpeechActuator, device_id=nao, inputs_to_service=[self], log_level=logging.INFO)
            motions.append(motion)

        time.sleep(1)

        for i, motion in enumerate(motions):
            a = NaoqiTextToSpeechRequest(f"Hello, we are the nao army!")
            time.sleep(.04)
            reply = motion.request(a, block=False)



if __name__ == '__main__':
    test_app = DemoTextToSpeech()

    test_app.run()
    test_app.stop()
