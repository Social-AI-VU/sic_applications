import io
import json
import logging
import queue
import time

import cv2
import numpy as np
import pyaudio

from sic_framework.core import utils_cv2
from sic_framework.core.message_python2 import CompressedImageMessage, BoundingBoxesMessage
from sic_framework.devices import Pepper
from sic_framework.devices.common_naoqi.naoqi_motion import NaoPostureRequest, NaoqiMotion
from sic_framework.devices.common_naoqi.naoqi_camera import NaoqiTopCamera
from sic_framework.devices.common_naoqi.naoqi_microphone import NaoqiMicrophone
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest, NaoqiTextToSpeech
from sic_framework.services.dialogflow.dialogflow import Dialogflow, DialogflowConf, GetIntentRequest
from sic_framework.services.face_recognition_dnn.face_recognition import DNNFaceRecognition


"""
Data buffers. We need to store the data received in callbacks somewhere.
"""

last_seen_face_id = None
face_name_memory = {}
imgs_buffer = queue.Queue()
faces_buffer = queue.Queue()



def display(image_message):
    global last_seen_face_id

    image = image_message.image

    try:
        faces = faces_buffer.get_nowait()
        for face in faces:
            utils_cv2.draw_bbox_on_image(face, image)
            last_seen_face_id = face.identifier
    except queue.Empty:
        pass


    cv2.imshow('TopCamera', image)
    cv2.waitKey(1)

def on_dialog(message):
    if message.response:
        # print(message.response.recognition_result.transcript)
        if message.response.recognition_result.is_final:
            print("Transcript:", message.response.recognition_result.transcript)



def on_faces(message: BoundingBoxesMessage):
    try:
        faces_buffer.get_nowait()  # remove previous message if its still there
    except queue.Empty:
        pass
    faces_buffer.put(message.bboxes)




robot_ip = '192.168.0.165'

robot = Pepper(robot_ip)

robot.top_camera.register_callback(display)

with open("openai_key", "r") as f:
    openai_key = f.read().strip() #  remove new line character



keyfile_json = json.load(open("dialogflow-test-project-wiggers.json"))
conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=16000,)

dialogflow = Dialogflow(ip='localhost', conf=conf)
dialogflow.register_callback(on_dialog)
dialogflow.connect(robot.mic)



face_rec = DNNFaceRecognition(ip='localhost')
face_rec.connect(robot.top_camera)


print(" -- Ready -- ")

x = np.random.randint(10000)

for i in range(1000):
    print(" ----- Conversation turn", i)
    reply = dialogflow.request(GetIntentRequest(x))

    if reply.response.query_result.fulfillment_messages:
        text = str(reply.response.query_result.fulfillment_messages[0].text.text[0])

        print("REPLY", text)

        robot.tts.request(NaoqiTextToSpeechRequest(text))



robot.tts.request(NaoqiTextToSpeechRequest("Nice talking to you!"))

