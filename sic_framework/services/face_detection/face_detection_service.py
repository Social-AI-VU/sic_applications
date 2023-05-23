import cv2
import numpy as np

from numpy import array

from sic_framework.core import sic_logging
from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import CompressedImageMessage, SICMessage, BoundingBox, BoundingBoxesMessage
from sic_framework.core.service_python2 import SICService


class FaceDetectionService(SICService):
    def __init__(self, *args, **kwargs):
        super(FaceDetectionService, self).__init__(*args, **kwargs)
        cascadePath = "haarcascade_frontalface_default.xml"
        self.faceCascade = cv2.CascadeClassifier(cascadePath)

        # Define min window size to be recognized as a face_img
        self.minW = 150
        self.minH = 150


    @staticmethod
    def get_inputs():
        return [CompressedImageMessage]

    @staticmethod
    def get_output():
        return BoundingBoxesMessage

    def execute(self, inputs):
        image = inputs.get(CompressedImageMessage).image

        img = array(image).astype(np.uint8)

        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        faces = self.faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(self.minW), int(self.minH)),
        )

        faces = [BoundingBox(x, y, w, h) for (x, y, w, h) in faces]

        return BoundingBoxesMessage(faces)

class FaceDetection(SICConnector):
    component_class = FaceDetectionService

if __name__ == '__main__':
    c = FaceDetectionService()
    c._start()