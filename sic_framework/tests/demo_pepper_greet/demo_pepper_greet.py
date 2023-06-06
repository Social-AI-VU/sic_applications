import io
import json
import logging
import time

import cv2
import numpy as np
import pyaudio
from sic_framework.core.connector import SICApplication
from sic_framework.devices.common_naoqi.nao_motion import NaoPostureRequest, NaoRestRequest, NaoWakeUpRequest
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoqiCameraSensor, NaoqiCameraConf
from sic_framework.devices.common_naoqi.naoqi_microphone import NaoqiMicrophoneSensor
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest
from sic_framework.devices.desktop.desktop_microphone import DesktopMicrophone
from sic_framework.devices.nao import Nao

from sic_framework.services.dialogflow.dialogflow_service import DialogflowService, DialogflowConf, GetIntentRequest, \
    RecognitionResult, QueryResult
from sic_framework.services.face_recognition_dnn.face_recognition_service import DNNFaceRecognitionService, \
    RecognizedFacesMessage, Face

""" 
This is a demo using multiple services at the same time.
Pepper should:
1. Detect people at a distance
2. Say "Hi" to unseen people when they approach
3. Recognize seen people.
4. 

https://github.com/derronqi/yolov7-face

keywords:
re-identification and multi-object tracking

https://arxiv.org/pdf/1905.00953.pdf

Maybe for now:
Do tracking with the thresholded detections (which will obviously miss some)

How to:
Detected face location + embeddings



"""

class Person:
    def __init__(self, identifier=None, name=None, position=None, distance=None):
        self.identifier = identifier
        self.name = name
        self.position = position
        self.distance = distance


def on_dialog(message):
    if message.response:
        if message.response.recognition_result.is_final:
            print("Transcript:", message.response.recognition_result.transcript)


class DemoDialogflow(SICApplication):

    def display(self, image_message):
        image = image_message.image[:, :, ::-1]

        for face in self.faces:
            face.draw_on_image(image)

        cv2.imshow('TopCamera', image)
        cv2.waitKey(1)

    def on_face_rec(self, message):
        self.faces = message.bboxes

        
        for face in message.bboxes:
            self.last_seen_face_id = face.identifier
            print("Detected person ", face.identifier)

    def run(self) -> None:

        #
        # Service connections
        #

        self.nao = Nao(device_id='nao', application=self)
        self.nao.set_config(TopNaoqiCameraSensor, NaoqiCameraConf(res_id=3))
        self.nao.top_camera.register_callback(self.display)

        keyfile_json = json.load(open("dialogflow-test-project-wiggers.json"))

        conf = DialogflowConf(keyfile_json=keyfile_json,
                              project_id='dialogflow-test-project-376814', sample_rate_hertz=16000,)
        dialogflow = self.start_service(DialogflowService, device_id='local', inputs_to_service=[self.nao.mic, self],
                                        log_level=logging.INFO, conf=conf)
        dialogflow.register_callback(on_dialog)

        face_rec = self.start_service(DNNFaceRecognitionService, device_id='local', inputs_to_service=[self.nao.top_camera],
                                      log_level=logging.INFO)
        face_rec.register_callback(self.on_face_rec)


        #
        # Main recognition loop
        #

        time.sleep(1000)



if __name__ == '__main__':
    test_app = DemoDialogflow()

    test_app.run()
    # test_app.stop()

"""

export GOOGLE_APPLICATION_CREDENTIALS=/home/thomas/vu/SAIL/docker/sic/sic_framework/services/dialogflow/test-hync.json
"""
