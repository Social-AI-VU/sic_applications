"""
This demo should simultaneously display images from all cameras (stereo camera, depth camera, mono camera) and play the sound from the microphone.
"""
import time

import cv2

from sic_framework import SICApplication
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoqiCameraSensor, BottomNaoqiCameraSensor, StereoPepperCameraSensor, \
    DepthPepperCameraSensor


class DemoDisplayCameras(SICApplication):

    def top(self, img_message):
        cv2.imshow("top", img_message.image[..., ::-1])
        cv2.waitKey(1)

    def bottom(self, img_message):
        cv2.imshow("bottom", img_message.image[..., ::-1])
        cv2.waitKey(1)

    def stereo(self, img_message):
        cv2.imshow("stereo", img_message.image[..., ::-1])
        cv2.waitKey(1)

    def depth(self, img_message):
        cv2.imshow("depth", img_message.image[..., ::-1])
        cv2.waitKey(1)

    def run(self) -> None:
        # Connect to all cameras and microphone
        top_cam = self.start_service(TopNaoqiCameraSensor, device_id='pepper')
        top_cam.register_callback(self.top)
        self.top_cam = top_cam

        time.sleep(1)
        self.image.show

        bottom_cam = self.start_service(BottomNaoqiCameraSensor, device_id='pepper')
        bottom_cam.register_callback(self.bottom)

        stereo_cam = self.start_service(StereoPepperCameraSensor, device_id='pepper')
        stereo_cam.register_callback(self.stereo)

        depth_cam = self.start_service(DepthPepperCameraSensor, device_id='pepper')
        depth_cam.register_callback(self.depth)

        time.sleep(100)


if __name__ == '__main__':
    test_app = DemoDisplayCameras()
    test_app.run()
    test_app.stop()
