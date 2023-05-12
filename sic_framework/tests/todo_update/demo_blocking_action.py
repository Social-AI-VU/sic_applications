import time

import cv2

# TODO from sic_v2.slow_action_test import SlowActionTest, TestSlowActionMessage
# TODO breaks when sending a message to a device
from sic_framework import SICApplication, sic_logging

import tqdm
from sic_framework.tests.services.slow_action_test import SlowActionTest, TestSlowActionRequest


""" This demo should display a camera image
"""


class DemoSlowAction(SICApplication):

    def run(self) -> None:
        ### use speakers

        nao3_action = test_app.start_service(SlowActionTest, device_id='nao', inputs_to_service=[self])

        nao3_action.register_callback(print)

        nao3_action.request(TestSlowActionRequest("hello!"))

        start = time.time()
        print("Duration:", time.time() - start)


if __name__ == '__main__':
    test_app = DemoSlowAction()

    test_app.run()
