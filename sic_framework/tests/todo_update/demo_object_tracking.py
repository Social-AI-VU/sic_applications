import cv2
import numpy as np
import tqdm
from sic_framework import SICApplication
from sic_framework.core.message_python2 import CompressedImageMessage, BoundingBoxesMessage, BoundingBox
from sic_framework.devices.common_naoqi.naoqi_camera import NaoqiTopCameraSensor, NaoqiCameraConf
from sic_framework.services.face_detection.face_detection_service import FaceDetectionService
from sic_framework.services.object_tracking.object_tracking_service import ObjectTrackingService

""" 
This demo tests face recognition
"""


class FaceDetectionApp(SICApplication):

    def run(self) -> None:
        cam_conf = NaoqiCameraConf(cam_id=0, res_id=2)
        cam = self.start_service(NaoqiTopCameraSensor, device_id='nao', conf=cam_conf)

        face = self.start_service(FaceDetectionService, device_id='local', inputs_to_service=[cam])

        face_tracked = self.start_service(ObjectTrackingService, device_id='local', inputs_to_service=[face])

        self.faces = []
        self.faces_tracked = []

        face.register_callback(self.on_detected_faces)
        face_tracked.register_callback(self.on_detected_faces_tracked)
        cam.register_callback(self.on_image)

    def on_detected_faces(self, boundingboxes):
        self.faces = boundingboxes.bboxes

    def on_detected_faces_tracked(self, boundingboxes):
        self.faces_tracked = boundingboxes.bboxes

    def on_image(self, image_message: CompressedImageMessage):
        image = image_message.image

        for face in self.faces:
            face.draw_bbox_on_image(image)

        for face in self.faces_tracked:
            face.x += 1
            face.y += 1
            face.w -= 2
            face.h -= 2
            face.draw_bbox_on_image(image, color=(255, 0, 0))

        cv2.imshow('', image[:, :, ::-1])
        cv2.waitKey(1)


if __name__ == '__main__':
    test_app = FaceDetectionApp()

    test_app.run()

"""
Robot exports

export DB_PASS=changemeplease
export DB_IP=192.168.0.FOO


"""

