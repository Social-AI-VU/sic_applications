import io
import logging
import threading
import time

import cv2
import numpy as np
from matplotlib import pyplot as plt

from sic_framework.core.connector import SICApplication
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiMotionActuator, NaoPostureRequest, NaoRestRequest, \
    NaoqiMoveToRequest
import tqdm

""" This demo should display a camera image
"""



class DemoMotion(SICApplication):

    def run(self) -> None:
        #### use camera

        ips = [
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
        threads = []
        for nao in ips:

            def do_start():
                motion = self.start_service(NaoqiMotionActuator, device_id=nao, inputs_to_service=[self], log_level=logging.INFO)
                motions.append(motion)

            t = threading.Thread(target=do_start)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()


        for motion in motions:
            a = NaoPostureRequest("Stand", .5)

            reply = motion.request(a, block=False)

        time.sleep(3)
        print("MOVE")

        for motion in motions:
            a = NaoqiMoveToRequest(.7, 0, 0)
            reply = motion.request(a, block=False)

        #
        # print("ROTATE")
        # time.sleep(5)
        #
        # for motion in motions:
        #     a = NaoMoveToRequest(0,0,1)
        #     reply = motion.request(a, block=False)

        print("SIT")
        time.sleep(5)

        for motion in motions:

            a = NaoRestRequest()

            motion.request(a, block=False)

        time.sleep(10)

        self.stop()


if __name__ == '__main__':
    test_app = DemoMotion()
    test_app.redis._redis.flushall()

    test_app.run()

"""
Robot exports

export DB_PASS=changemeplease
export DB_SSL_SELFSIGNED=1
export DB_IP=192.168.0.FOO
"""



