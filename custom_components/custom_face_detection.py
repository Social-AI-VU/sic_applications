# Import the original component + SICComponentManager + SICConnector
from sic_framework.services.face_detection.face_detection import FaceDetectionComponent
from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.core.connector import SICConnector
# Import the modules necessary for custom functionality
from sic_framework.core.message_python2 import (
    BoundingBox,
    BoundingBoxesMessage,
)
from numpy import array
import numpy as np
import cv2

class CustomFaceDetectionComponent(FaceDetectionComponent):
    """
    Custom FaceDetectionComponent. Makes 'scaleFactor' and 'minNeighbors' instance variables
    """
    def __init__(self, *args, **kwargs):
        super(CustomFaceDetectionComponent, self).__init__(*args, **kwargs)
        self.scaleFactor = 1.2
        self.minNeighbors = 3

    def detect(self, image):
        # Override the detect function with custom behavior
        img = array(image).astype(np.uint8)

        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Custom face detection logic can go here
        faces = self.faceCascade.detectMultiScale(
            gray,
            scaleFactor=self.scaleFactor,  # Example of different scale factor
            minNeighbors=self.minNeighbors,    # Example of different minNeighbors
            minSize=(int(self.params.minW), int(self.params.minH)),
        )

        faces = [BoundingBox(x, y, w, h) for (x, y, w, h) in faces]

        return BoundingBoxesMessage(faces)

class CustomFaceDetection(SICConnector):
    # every component needs a connector
    component_class = CustomFaceDetectionComponent

def main():
    # Register the custom component in the component manager
    SICComponentManager([CustomFaceDetectionComponent])

if __name__ == "__main__":
    main()