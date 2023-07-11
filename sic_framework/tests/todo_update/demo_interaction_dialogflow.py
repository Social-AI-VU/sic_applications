import io
import json
import logging
import time

import cv2
import numpy as np
import pyaudio
from sic_framework.core.connector import SICApplication
from sic_framework.devices.common_naoqi.naoqi_motion import NaoPostureRequest, NaoRestRequest, NaoWakeUpRequest
from sic_framework.devices.common_naoqi.naoqi_camera import NaoqiTopCameraSensor, NaoqiCameraConf
from sic_framework.devices.common_naoqi.naoqi_microphone import NaoqiMicrophoneSensor
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest
from sic_framework.devices.desktop.desktop_microphone import DesktopMicrophone
from sic_framework.devices.nao import Nao

from sic_framework.services.dialogflow.dialogflow import DialogflowComponent, DialogflowConf, GetIntentRequest, \
    RecognitionResult, QueryResult
from sic_framework.services.face_recognition_dnn.face_recognition import DNNFaceRecognitionComponent
""" This demo should display a camera image
"""

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

from pydub import AudioSegment
from pydub.playback import play
import io


def on_dialog(message):
    if message.response:
        # print(message.response.recognition_result.transcript)
        if message.response.recognition_result.is_final:
            print("Transcript:", message.response.recognition_result.transcript)


class DemoDialogflow(SICApplication):

    def display(self, image_message):
        image = image_message.image[:, :, ::-1]

        for face in self.faces:
            face.draw_bbox_on_image(image)

        cv2.imshow('TopCamera', image)
        cv2.waitKey(1)

    def on_face_rec(self, message):
        self.faces = message.bboxes
        for face in message.bboxes:
            self.last_seen_face_id = face.identifier
            print("Detected person ", face.identifier)

    def run(self) -> None:
        self.faces = []
        self.last_seen_face_id = None
        self.face_name_memory = {}

        self.nao = Nao(device_id='nao', application=self)
        self.nao.set_config(NaoqiTopCameraSensor, NaoqiCameraConf(res_id=3))

        keyfile_json = json.load(open("dialogflow-test-project-wiggers.json"))

        conf = DialogflowConf(keyfile_json=keyfile_json, project_id='dialogflow-test-project-376814', sample_rate_hertz=16000,)

        dialogflow = self.start_service(DialogflowComponent, device_id='local', inputs_to_service=[self.nao.mic, self],
                                        log_level=logging.INFO, conf=conf)
        dialogflow.register_callback(on_dialog)

        face_rec = self.start_service(DNNFaceRecognitionComponent, device_id='local', inputs_to_service=[self.nao.top_camera],
                                      log_level=logging.INFO)
        face_rec.register_callback(self.on_face_rec)
        self.nao.top_camera.register_callback(self.display)

        print(" -- Ready -- ")

        x = np.random.randint(10000)

        for i in range(1000):
            print(" ----- Conversation turn", i)
            reply = dialogflow.request(GetIntentRequest(x))

            if reply.response.query_result.fulfillment_messages:
                text = str(reply.response.query_result.fulfillment_messages[0].text.text[0])

                print("REPLY", text)

                self.nao.tts.request(NaoqiTextToSpeechRequest(text))

            if reply.response.query_result.intent:
                intent_name = reply.response.query_result.intent.display_name
                print(f"INTENT '{intent_name}'")

                if intent_name == "get_up":
                    self.nao.motion.request(NaoPostureRequest("Stand"))
                    self.nao.motion.request(NaoWakeUpRequest())
                if intent_name == "sit_down":
                    self.nao.motion.request(NaoRestRequest())

                if intent_name == "remember_name":
                    name = reply.response.query_result.parameters["given-name"]

                    if self.last_seen_face_id is not None:
                        print(self.last_seen_face_id, "=", name)
                        self.face_name_memory[self.last_seen_face_id] = name
                    else:
                        self.nao.tts.request(NaoqiTextToSpeechRequest("Sorry, i cant see you"))

                if intent_name == "greet":
                    if self.last_seen_face_id in self.face_name_memory:
                        text = f"Hi there {self.face_name_memory[self.last_seen_face_id]}"
                    elif self.last_seen_face_id is not None:
                        text = f"I dont know your name, but you are person {self.last_seen_face_id}"
                    else:
                        self.nao.tts.request(NaoqiTextToSpeechRequest("Sorry, i cant see you"))
                    self.nao.tts.request(NaoqiTextToSpeechRequest(text))

                if intent_name == "count_people":
                    self.nao.tts.request(NaoqiTextToSpeechRequest(f"I think {len(self.face_name_memory)}"))

        self.nao.tts.request(NaoqiTextToSpeechRequest("Nice talking to you!"))


#
#
#  get_up
# greet
# remember_name
# sit_down
#
# nao-test-2"


if __name__ == '__main__':
    test_app = DemoDialogflow()

    test_app.run()
    # test_app.stop()

"""

export GOOGLE_APPLICATION_CREDENTIALS=/home/thomas/vu/SAIL/docker/sic/sic_framework/services/dialogflow/test-hync.json
"""
