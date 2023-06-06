import argparse
from sic_framework import SICComponentManager, SICService, utils

from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import CompressedImageMessage, SICConfMessage, SICMessage
from sic_framework.core.sensor_python2 import SICSensor

if utils.PYTHON_VERSION_IS_2:
    from PIL import Image
    import numpy as np
    import random
    import cv2

    from naoqi import ALProxy
    import qi


class NaoqiCameraConf(SICConfMessage):
    def __init__(self, naoqi_ip='127.0.0.1', port=9559, cam_id=0, res_id=2, fps=30):
        """ params can be found at http://doc.aldebaran.com/2-8/family/nao_technical/video_naov6.html#naov6-video
        Camera ID:
        0 - TopCamera
        1 - BottomCamera

        Resolution ID:
        1  -  320x240px
        2  -  640x480px
        3  -  1280x960px
        4  -  2560x1920px
        """
        SICConfMessage.__init__(self)
        self.naoqi_ip = naoqi_ip
        self.port = port
        self.cam_id = cam_id
        self.res_id = res_id
        self.color_id = 11  # RGB
        self.fps = fps


class BaseNaoqiCameraSensor(SICSensor):
    def __init__(self, *args, **kwargs):
        super(BaseNaoqiCameraSensor, self).__init__(*args, **kwargs)

        self.s = qi.Session()
        self.s.connect('tcp://{}:{}'.format(self.params.naoqi_ip, self.params.port))

        self.video_service = self.s.service("ALVideoDevice")
        self.video_service.setParameter(0, 35, 1)  # TODO: do we want to change this? Is this brightness?
        self.videoClient = self.video_service.subscribeCamera("Camera_{}".format(random.randint(0, 100000)),
                                                              self.params.cam_id,
                                                              self.params.res_id, self.params.color_id,
                                                              self.params.fps)

    @staticmethod
    def get_conf():
        return NaoqiCameraConf()

    @staticmethod
    def get_inputs():
        return []

    @staticmethod
    def get_output():
        return CompressedImageMessage

    def execute(self):
        # get the actual image from the NaoImage type
        naoImage = self.video_service.getImageRemote(self.videoClient)
        imageWidth = naoImage[0]
        imageHeight = naoImage[1]
        array = naoImage[6]
        image_string = str(bytearray(array))

        # Create a PIL Image from our pixel array.
        im = Image.frombytes("RGB", (imageWidth, imageHeight), image_string)
        return CompressedImageMessage(np.asarray(im))

    def stop(self, *args):
        super(BaseNaoqiCameraSensor, self).stop(*args)
        print("Stopping NAOqi video service")
        self.video_service.shutdown()


##################
# Top Camera
##################

class TopNaoqiCameraSensor(BaseNaoqiCameraSensor):
    def __init__(self, *args, **kwargs):
        super(TopNaoqiCameraSensor, self).__init__(*args, **kwargs)

    @staticmethod
    def get_conf():
        return NaoqiCameraConf(cam_id=0, res_id=1)


class TopNaoqiCamera(SICConnector):
    component_class = TopNaoqiCameraSensor


##################
# Bottom Camera
##################

class BottomNaoqiCameraSensor(BaseNaoqiCameraSensor):
    def __init__(self, *args, **kwargs):
        super(BottomNaoqiCameraSensor, self).__init__(*args, **kwargs)

    @staticmethod
    def get_conf():
        return NaoqiCameraConf(cam_id=1, res_id=1)


class BottomNaoqiCamera(SICConnector):
    component_class = BottomNaoqiCameraSensor


##################
# Stereo Pepper Camera
##################

class StereoImageMessage(SICMessage):
    _compress_images = True

    def __init__(self, left, right):
        self.left_image = left
        self.right_image = right


class NaoStereoCameraConf(NaoqiCameraConf):
    def __init__(self, calib_params=None, naoqi_ip='127.0.0.1', port=9559, cam_id=0, res_id=2, color_id=11, fps=30,
                 convert_bw=True, use_calib=True):
        super(NaoStereoCameraConf, self).__init__(naoqi_ip, port, cam_id, res_id, color_id, fps)  # TODO: correct?

        if calib_params is None:
            calib_params = {}

        self.cameramtrx = calib_params.get('cameramtrx', None)
        self.K = calib_params.get('K', None)
        self.D = calib_params.get('D', None)
        self.H1 = calib_params.get('H1', None)
        self.H2 = calib_params.get('H2', None)
        self.convert_bw = convert_bw  # Convert images to b&w before sending
        self.use_calib = use_calib  # We don't want to rectify the images if we are calibrating


class StereoPepperCameraSensor(BaseNaoqiCameraSensor):
    def __init__(self, *args, **kwargs):
        super(StereoPepperCameraSensor, self).__init__(*args, **kwargs)

    @staticmethod
    def get_conf():
        # TODO: by default read calibration from disk
        return NaoStereoCameraConf(calib_params={'cameramtrx': None, 'K': None, 'D': None, 'H1': None, 'H2': None},
                                   cam_id=3, res_id=15, convert_bw=True, use_calib=True)

    def undistort(self, img):
        return cv2.undistort(img, self.params.K, self.params.D, None, self.params.cameramtrx)

    def warp(self, img, is_left):
        H_matrix = self.params.H1 if is_left else self.params.H2
        return cv2.warpPerspective(img, H_matrix, img.shape[::-1])

    def rectify(self, img, is_left):
        if len(img.shape) == 2:
            return self.warp(self.undistort(img), is_left)

        img = np.concatenate([self.rectify(img[..., i], is_left)[..., np.newaxis] for i in range(img.shape[-1])],
                             axis=2)
        return img

    def execute(self):
        # Get the regular stereo image
        img_message = super(StereoPepperCameraSensor, self).execute().image

        if self.params.convert_bw:
            img_message = cv2.cvtColor(img_message, cv2.COLOR_BGR2GRAY)

        # Split the stereo image into separate left and right images
        left, right = img_message[:, :img_message.shape[1] // 2, ...], img_message[:, img_message.shape[1] // 2:, ...]

        # Rectify the images to account for lens distortion and camera mis-alignment
        if self.params.use_calib:
            left = self.rectify(left, is_left=True)
            right = self.rectify(right, is_left=False)

        return StereoImageMessage(left, right)

    @staticmethod
    def get_output():
        return StereoImageMessage


class StereoPepperCamera(SICConnector):
    component_class = StereoPepperCameraSensor


##################
# Depth Pepper Camera
##################

class DepthPepperCameraSensor(BaseNaoqiCameraSensor):
    def __init__(self, *args, **kwargs):
        super(DepthPepperCameraSensor, self).__init__(*args, **kwargs)

    @staticmethod
    def get_conf():
        return NaoqiCameraConf(cam_id=2, res_id=10)


class DepthPepperCamera(SICConnector):
    component_class = DepthPepperCameraSensor


if __name__ == '__main__':
    SICComponentManager([TopNaoqiCameraSensor, BottomNaoqiCameraSensor, StereoPepperCameraSensor, DepthPepperCameraSensor])
