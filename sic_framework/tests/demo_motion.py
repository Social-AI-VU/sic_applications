import time

from sic_framework.core.connector import SICApplication
from sic_framework.devices.common_naoqi.nao_motion import NaoMotionActuator, NaoPostureRequest, NaoRestRequest

""" 
This demo makes the nao move
"""


class DemoMotion(SICApplication):

    def run(self) -> None:
        motion = self.start_service(NaoMotionActuator, device_id='nao', inputs_to_service=[self])

        a = NaoPostureRequest("Stand", .5)

        reply = motion.request(a)

        time.sleep(1)

        a = NaoPostureRequest("Crouch", .5)

        reply = motion.request(a)

        a = NaoRestRequest()

        motion.request(a)

        self.stop()


if __name__ == '__main__':
    test_app = DemoMotion()
    test_app.run()


