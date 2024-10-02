"""
This demo displays the depth image, calculated based on the stereo camera.
"""
import time
import cv2
from sic_framework import SICApplication
from sic_framework.devices.common_naoqi.naoqi_camera import StereoPepperCameraSensor, NaoStereoCameraConf
from sic_framework.devices.pepper import Pepper
import logging
from sic_framework.services.depth_estimation.depth_estimation_service import DepthEstimationService
import numpy as np
import matplotlib.pyplot as plt


class Display:
    def __init__(self, wait_for_event=False, size=(1280, 360)):
        import pygame
        self.pygame = pygame
        self.wait = wait_for_event

        self.pygame.init()
        self.size = size
        self.display_surface = self.pygame.display.set_mode(self.size)

        self.font = self.pygame.font.SysFont('robotoslab', 30)

    @staticmethod
    def gray(im):
        im = 255 * (im / im.max())
        w, h = im.shape
        ret = np.empty((w, h, 3), dtype=np.uint8)
        ret[:, :, 2] = ret[:, :, 1] = ret[:, :, 0] = im
        return ret

    def clear(self, text=None):
        white = (255, 255, 255)
        self.display_surface.fill(white)

        if text:
            textsurface = self.font.render(text, False, (0, 0, 0))
            self.display_surface.blit(textsurface, (0, 0))

        self.pygame.display.update()

    def show(self, arr, scale=True):
        white = (255, 255, 255)
        assert arr.ndim in [2, 3], "incorrect dimensions"
        img = arr

        # unnormalize
        if arr.dtype in [np.float, np.float32, np.float64]:
            arr -= arr.min()
            arr /= arr.max()
            arr *= 255
            arr = arr.astype(np.int)

        # gray to color
        if arr.ndim == 2:
            arr = self.gray(arr)

        arr = arr.swapaxes(0, 1)  # Fix pygame transposed rendering
        surf = self.pygame.surfarray.make_surface(arr)
        # surf = self.pygame.transform.rotate(surf, -90) # now done by swapaxis

        if scale:
            surf = self.pygame.transform.scale(surf, self.size)

        self.display_surface.fill(white)
        self.display_surface.blit(surf, (0, 0))
        self.pygame.display.update()

        if self.wait:
            self.pygame.event.clear()
            while True:
                event = self.pygame.event.wait()
                if event.type == self.pygame.QUIT:
                    self.close()
                    break

                elif event.type == self.pygame.KEYDOWN:
                    if event.key == self.pygame.K_i:
                        plt.imshow(img)
                        plt.show()
                    else:
                        break

    def wait_for_key(self):
        self.pygame.event.clear()
        while True:
            event = self.pygame.event.wait()
            if event.type == self.pygame.QUIT:
                self.close()
                break

            elif event.type == self.pygame.KEYDOWN:
                return event.key

    def set_caption(self, string):
        self.pygame.display.set_caption(string)

    def close(self):
        self.pygame.quit()

disp = Display()


class DemoDisplayDepth(SICApplication):
    def on_stereo(self, img_message):
        # disp.show(np.hstack([img_message.left_image, img_message.right_image]), scale=False)
        pass
        # cv2.imshow("stereo_left", img_message.left_image[..., ::-1])
        # cv2.imshow("stereo_right", img_message.right_image[..., ::-1])
        # cv2.waitKey(1)

    def on_depth(self, img_message):
        print(np.sum(img_message.image == -1))
        np.save('temp.npy', img_message.image)
        disp.show(img_message.image, scale=False)

        # disp.show(img_message.image[..., ::-1])
        # print("GOT IMG", img_message.image.min(), img_message.image.max())
        # cv2.imshow("depth", img_message.image[..., ::-1].astype(np.uint8))
        # cv2.waitKey(1)
        pass

    def run(self) -> None:
        # Calibration values
        cammtrx = np.array([[309.90368652, 0., 297.5],
                            [0., 358.62393188, 165.],
                            [0., 0., 1.]])
        K = np.array([[349.7968421, 0., 256.92867768],
                      [0., 350.14732589, 190.6236813],
                      [0., 0., 1.]])
        D = np.array([[-0.11309382, -0.12237389, 0.00051051, -0.00025434, 0.12276008]])
        H1 = np.array([[1.41670247e-01, -3.79925977e-03, -1.46349568e-01],
                       [1.05185492e-13, 1.42857143e-01, 1.00000000e+00],
                       [4.94224554e-16, 4.37517251e-16, 1.42857143e-01]])
        H2 = np.array([[1.00000000e+00, 7.60503536e-14, -1.77919901e-11],
                       [-7.60503536e-14, 1.00000000e+00, 1.25055521e-11],
                       [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])

        # Connect to Depth service and stereo camera
        pepper = Pepper(device_id='pepper', application=self)
        stereo_conf = NaoStereoCameraConf(cameramtrx=cammtrx, K=K, D=D, H1=H1, H2=H2, cam_id=3, res_id=14, convert_bw=True)
        pepper.set_config(StereoPepperCameraSensor, stereo_conf)
        pepper.stereo_camera.register_callback(self.on_stereo)

        depth = self.start_service(DepthEstimationService, device_id='local', inputs_to_service=[pepper.stereo_camera], log_level=logging.INFO)
        depth.register_callback(self.on_depth)

        time.sleep(100000)


if __name__ == '__main__':
    test_app = DemoDisplayDepth()
    test_app.run()
    test_app.stop()
