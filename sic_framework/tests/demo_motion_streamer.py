import logging
import threading
import time

from sic_framework.core.connector import SICApplication
from sic_framework.devices.common_naoqi.naoqi_motion_streamer import NaoMotionStreamProducer, NaoMotionStreamConsumer
from sic_framework.devices.nao import Nao

""" This demo should display a camera image
"""


class DemoMotion(SICApplication):

    def run(self) -> None:
        #### use camera

        streamer = self.start_service(NaoMotionStreamProducer, device_id='192.168.0.236', inputs_to_service=[], log_level=logging.INFO)

        ips = [
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
                motion = self.start_service(NaoMotionStreamConsumer, device_id=nao, inputs_to_service=[streamer],
                                            log_level=logging.INFO)

                motions.append(motion)

            t = threading.Thread(target=do_start)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()





        time.sleep(30)

        print("end")


if __name__ == '__main__':
    test_app = DemoMotion()

    test_app.run()
    test_app.stop()

"""
Robot exports

export DB_PASS=changemeplease
export DB_SSL_SELFSIGNED=1
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~/sic/core/lib/libtubojpeg/lib32/
export DB_IP=192.168.0.FOO
"""
