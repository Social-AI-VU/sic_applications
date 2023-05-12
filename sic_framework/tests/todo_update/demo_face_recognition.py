import cv2
import numpy as np
import tqdm
from sic_framework import SICApplication
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoCameraSensor, NaoqiCameraConf
from sic_framework.devices.common_naoqi.naoqi_speakers import NaoqiTextToSpeechActuator, NaoqiTextToSpeechRequest
from sic_framework.services.face_recognition_dnn.face_recognition_service import DNNFaceRecognitionService, \
    Face, RecognizedFacesMessage

""" 
This demo tests face recognition
"""


class FaceRecognitionApp(SICApplication):

    def run(self) -> None:

        self.seen_faces = set()

        cam_conf = NaoqiCameraConf(cam_id=0, res_id=2)
        cam = self.start_service(TopNaoCameraSensor, device_id='nao', conf=cam_conf)
        self.nao_tts = self.start_service(NaoqiTextToSpeechActuator, device_id='nao', inputs_to_service=[self])

        face = self.start_service(DNNFaceRecognitionService, device_id='xps15', inputs_to_service=[cam])

        self.faces = []

        face.register_callback(self.on_detected_faces)
        cam.register_callback(self.on_image)

    def on_detected_faces(self, faces_message):
        self.faces = faces_message.bboxes
        for face in self.faces:
            if face.id not in self.seen_faces:
                self.seen_faces.add(face.identifier)
                self.nao_tts.request(NaoqiTextToSpeechRequest("Hi, person {}".format(face.identifier)))
                print("HI ", face.identifier)

    def on_image(self, image_message: CompressedImageMessage):
        image = image_message.image[:, :, ::-1]

        for face in self.faces:
            face.draw_on_image(image)

        cv2.imshow('', image)
        cv2.waitKey(1)


if __name__ == '__main__':
    test_app = FaceRecognitionApp()

    test_app.run()

"""
Robot exports

export DB_PASS=changemeplease
export DB_SSL_SELFSIGNED=1
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~/v3/libtubojpeg_robot/lib32/
export DB_IP=192.168.0.FOO
"""
