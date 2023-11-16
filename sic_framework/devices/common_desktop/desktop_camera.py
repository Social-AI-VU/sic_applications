import platform

import cv2

from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import CompressedImageMessage, SICConfMessage
from sic_framework.core.sensor_python2 import SICSensor


class DesktopCameraConf(SICConfMessage):
    def __init__(self, fx=1.0, fy=1.0, flip=None):
        """
        Sets desktop camera configuration parameters.

        See https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html#ga47a974309e9102f5f08231edc7e7529d
        :param fx: rescaling factor along x-axis (float)
        :param fy: rescaling factor along y-axis (float)

        See https://docs.opencv.org/3.4/d2/de8/group__core__array.html#gaca7be533e3dac7feb70fc60635adf441
        :param flip: flip code for vertical (0), horizontal (>0), or both (<0) flipping. Default is None (no flipping)
        """
        SICConfMessage.__init__(self)

        self.fx = fx
        self.fy = fy
        self.flip = flip


class DesktopCameraSensor(SICSensor):
    def __init__(self, *args, **kwargs):
        super(DesktopCameraSensor, self).__init__(*args, **kwargs)

        if platform.system() == "Windows":
            self.cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            self.cam = cv2.VideoCapture(0)

    @staticmethod
    def get_conf():
        return DesktopCameraConf()

    @staticmethod
    def get_inputs():
        return []

    @staticmethod
    def get_output():
        return CompressedImageMessage

    def execute(self):
        ret, frame = self.cam.read()
        frame = cv2.resize(frame, (0, 0), fx=self.params.fx, fy=self.params.fy)

        # Optionally flip image
        if self.params.flip is not None:
            frame = cv2.flip(frame, self.params.flip)

        if not ret:
            self.logger.warning("Failed to grab frame from video device")

        return CompressedImageMessage(frame)

    def stop(self, *args):
        super(DesktopCameraSensor, self).stop(*args)
        self.cam.release()


class DesktopCamera(SICConnector):
    component_class = DesktopCameraSensor


if __name__ == '__main__':
    SICComponentManager([DesktopCameraSensor])
