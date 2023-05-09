import cv2

from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import CompressedImageMessage, SICConfMessage
from sic_framework.core.sensor_python2 import SICSensor


class DesktopCameraSensor(SICSensor):
    def __init__(self, *args, **kwargs):
        super(DesktopCameraSensor, self).__init__(*args, **kwargs)
        self.cam = cv2.VideoCapture(0)

    @staticmethod
    def get_conf():
        return SICConfMessage()

    @staticmethod
    def get_inputs():
        return []

    @staticmethod
    def get_output():
        return CompressedImageMessage

    def execute(self):
        ret, frame = self.cam.read()
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
