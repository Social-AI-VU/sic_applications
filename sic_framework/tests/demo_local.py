import time

import cv2

from sic_framework.core.connector import SICApplication
from services.stream_img_test import StreamImgService, ImgMessage

""" This demo should display a camera image
"""


def show(image_message):
    cv2.imshow("", image_message.image[..., ::-1])
    cv2.waitKey(1)

class DemoDisplayImage(SICApplication):

    def run(self) -> None:
        #### use camera

        cam = test_app.start_service(StreamImgService, device_id='local', )

        cam.register_callback(show)

        time.sleep(10)





if __name__ == '__main__':
    test_app = DemoDisplayImage()

    test_app.run()
