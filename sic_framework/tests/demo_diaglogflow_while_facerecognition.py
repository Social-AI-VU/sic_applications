import json
import numpy as np
import cv2
import threading
import queue
from sic_framework.devices import Nao
from sic_framework.devices.nao import NaoqiTextToSpeechRequest
from sic_framework.devices.common_naoqi.naoqi_camera import NaoqiCameraConf
from sic_framework.devices.common_naoqi.naoqi_motion import NaoPostureRequest
from sic_framework.core.message_python2 import BoundingBoxesMessage, CompressedImageMessage
from sic_framework.core.utils_cv2 import draw_bbox_on_image
from sic_framework.services.dialogflow.dialogflow import DialogflowConf, GetIntentRequest, RecognitionResult, QueryResult, Dialogflow
from sic_framework.services.face_recognition_dnn.face_recognition import DNNFaceRecognition


"""
This demo demonstrates how Nao interacts with you using Dialogflow
while simultaneously performing face recognition using DNNFaceRecognition

The Dialogflow and DNNFaceRecognition should be running. You can start them with:
[services/dialogflow] python dialogflow.py
[services/face_recognition_dnn] python face_recognition.py

"""

imgs_buffer = queue.Queue(maxsize=1)
faces_buffer = queue.Queue(maxsize=1)
# set to store detected face IDs
detected_faces = set()

def on_image(image_message: CompressedImageMessage):
    imgs_buffer.put(image_message.image)

def on_faces(message: BoundingBoxesMessage):
    faces_buffer.put(message.bboxes)
    for bbox in message.bboxes:
        if bbox.identifier not in detected_faces:
            detected_faces.add(bbox.identifier)
            # Set block to False for a non-blocking request,
            # allowing immediate execution of the next instruction
            nao.motion.request(NaoPostureRequest("StandZero", .5), block=False)
            nao.tts.request(NaoqiTextToSpeechRequest("I see a new face " + str(bbox.identifier)))

# callback function for Dialogflow responses
def on_dialog(message):
    if message.response:
        if message.response.recognition_result.is_final:
            print("Transcript:", message.response.recognition_result.transcript)

# setting up Nao and camera conf to flip the image vertically
conf = NaoqiCameraConf(vflip=1)
nao = Nao(ip='192.168.0.148', top_camera_conf=conf)
nao.top_camera.register_callback(on_image)

# setting up Dialogflow
keyfile_json = json.load(open("dialogflow-tutorial.json"))
conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=16000)
dialogflow = Dialogflow(ip='localhost', conf=conf)
dialogflow.connect(nao.mic)
dialogflow.register_callback(on_dialog)

# setting up DNNFaceRecognition
face_rec = DNNFaceRecognition()
face_rec.connect(nao.top_camera)
face_rec.register_callback(on_faces)

# target function1 to run in thread
def speech_recognition():
    x = np.random.randint(10000)
    for i in range(25):
        print(" ----- Conversation turn", i)
        reply = dialogflow.request(GetIntentRequest(x))
        if reply.fulfillment_message:
            text = reply.fulfillment_message
            print("Reply:", text)
            nao.tts.request(NaoqiTextToSpeechRequest(text))

# target function2 to run in thread
def face_detection():
    while True:
        img = imgs_buffer.get()
        faces = faces_buffer.get()
        for face in faces:
            draw_bbox_on_image(face, img)
        cv2.imshow('', img)
        cv2.waitKey(1)

# Demo starts
nao.tts.request(NaoqiTextToSpeechRequest("Hello, what can I do for you?"))
thread = threading.Thread(target=speech_recognition)
thread_2 = threading.Thread(target=face_detection)
thread.start()
thread_2.start()
