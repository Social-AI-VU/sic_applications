import io
import json
import logging
import queue
import re
import tempfile
import time
import wave

import cv2
import numpy as np
import pyaudio
import torch

from sic_framework.core import utils_cv2
from sic_framework.core.message_python2 import CompressedImageMessage, BoundingBoxesMessage
from sic_framework.devices import Pepper, Nao
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoBasicAwarenessRequest, NaoBackgroundMovingRequest, \
    NaoWakeUpRequest
from sic_framework.devices.common_naoqi.naoqi_camera import NaoqiCameraConf
from sic_framework.devices.common_naoqi.naoqi_motion import NaoPostureRequest, NaoqiMotion, NaoqiIdlePostureRequest, \
    NaoqiAnimationRequest, NaoqiMoveToRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest, NaoqiTextToSpeech
from sic_framework.services.dialogflow.dialogflow import Dialogflow, DialogflowConf, GetIntentRequest, \
    RecognitionResult, QueryResult
from sic_framework.services.face_detection_dnn.face_detection_dnn import DNNFaceDetection
from sic_framework.services.face_recognition_dnn.face_recognition import DNNFaceRecognition
from sic_framework.services.openai_gpt.gpt import GPTConf, GPT, GPTRequest, GPTResponse
from sic_framework.services.openai_whisper_speech_to_text.whisper_speech_to_text import SICWhisper, GetTranscript, \
    Transcript, WhisperConf
from google.cloud import aiplatform
from vertexai.vision_models import ImageQnAModel, ImageCaptioningModel
from vertexai.vision_models import Image as VertexImage
from PIL import Image
from google.oauth2.service_account import Credentials

"""
Data buffers. We need to store the data received in callbacks somewhere.
"""

additional_info = ""

imgs_buffer = queue.Queue()
faces_buffer = queue.Queue()


def display(image_message):
    image = image_message.image
    try:
        imgs_buffer.get_nowait()
    except queue.Empty:
        pass
    imgs_buffer.put(image)

    try:
        faces = faces_buffer.get_nowait()
        for face in faces:
            utils_cv2.draw_bbox_on_image(face, image)
    except queue.Empty:
        pass

    cv2.imshow('TopCamera', image[:, :, ::-1])
    cv2.waitKey(1)


def on_faces(message: BoundingBoxesMessage):
    try:
        faces_buffer.get_nowait()  # remove previous message if its still there
    except queue.Empty:
        pass
    faces_buffer.put(message.bboxes)


robot_ip = '192.168.0.226'
conf = NaoqiCameraConf(cam_id=0, res_id=2)
robot = Nao(robot_ip, top_camera_conf=conf)

robot.top_camera.register_callback(display)

with open("openai_key", "r") as f:
    openai_key = f.read().strip()  # remove new line character

# Setup GPT
conf = GPTConf(openai_key=openai_key)
gpt = GPT(conf=conf)

# Connect to the services
face_det = DNNFaceDetection()

# Feed the camera images into the face recognition component
face_det.connect(robot.top_camera)

# Send back the outputs to this program
face_det.register_callback(on_faces)

# Set up text to speech using whisper
conf = WhisperConf(openai_key=openai_key)
whisper = SICWhisper(conf=conf)
whisper.connect(robot.mic)


# visual question answering
credentials = Credentials.from_service_account_info(json.load(open("sicproject-vertex.json")))

aiplatform.init(project="sicproject-397617",
                # location="europe-west4", not supported yet
                credentials=credentials)
vqa_model = ImageQnAModel.from_pretrained("imagetext@001")
captioning_model = ImageCaptioningModel.from_pretrained("imagetext@001")

def get_google_image():
    try:
        image = imgs_buffer.get_nowait()
        img_byte_arr = io.BytesIO()
        Image.fromarray(image).save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        return VertexImage(img_byte_arr)
    except queue.Empty:
        return None


robot.motion.request(NaoqiIdlePostureRequest("Body", True))
robot.autonomous.request(NaoBasicAwarenessRequest(True))
robot.autonomous.request(NaoBackgroundMovingRequest(True))
robot.autonomous.request(NaoWakeUpRequest())

# robot.motion.request(NaoPostureRequest("Stand"))

print(" -- Ready -- ")

x = np.random.randint(10000)

ROBOT = robot.__class__.__name__

world_state = {}

system_message = f"""
You are a robot called {ROBOT}. You can help people to do things, like help them find the coffee machine. 
Do not be overly helpful or robotic, and act as human as possible. Keep track of the context.

Some information about the world
You are in the Social AI robotics lab. Behind you is the door to the hall.
The coffee machine is in the hall next to the sink. In the hall you can also find the toilets.


You will be provided with a json string containing processed information about the world. Example input:
{
'{"face_detection":[0:{"distance":1.5}], "scene_description": "a room with a lot of lights on the ceiling", "transcript":"Hey there, what lab is this?"}'
}

Use this sensor information to form a reply. This reply must also be in the form of a json string. 
Do not output anything beside the json.
Example output json:
{
'{"response":"Hello I am a helpful assistant", "action":{"wave":true}}'
}
or 
{
'{"response":"Ofcourse i can move around", "action": {"move":[0.2, 1.3]} }'
}

possible actions: 
"action":{'{"wave"}'}
"action": {'{"rotate": r}'}   (radians, positive is turning to the left also known as anti-clockwise, 1.57 is a quarter turn to the left)
"action": {'{"move":[x, y]}'}   (meters, x positive is forward, negative is backward , y positive is left, negative is right)

You can also use a visual question answer system to help you answer questions about the surroundings. 
For example, to check if you are looking at a banana, output the following json:
{
'{"action":{"visual_question":"Is there a banana in the image?"}}'
}

You will receive the same prompt as before, but augmented with a "visual_answer" field. 
Do not output a response or other action when asking visual questions, they will not be processed.
Do not ask a visual question after a prompt with a visual answer.


Example:
{
'{"face_detection":[0:{"distance":1.5}], "scene_description": "a man in a room looking out a window", "visual_answer":"The room has a window", "transcript":"Can you see a window?"}'
}

If the transcript is empty. You do not have to provide a response. You may use this time for reasoning or actions to move around the room and gather information.

Current goal:
When detecting someone for the first time, greet them and wave. Ask them if they need any help.

IMPORTANT:
Do not output anything beside a valid json response.
Only respond in english.
If you see Karen, tell her to go to bed because it is late! Be nice to her.

"""

def get_chatgpt_response(gpt_request):
    gpt_request = json.dumps(gpt_request)
    for i in range(2):
        try:
            print("Request:", gpt_request)
            text = gpt.request(GPTRequest(gpt_request, context_messages=chat_history, system_messages=system_message))
            print("Reply:", text.response)
            response = json.loads(text.response)
            break
        except json.decoder.JSONDecodeError:
            robot.tts.request(NaoqiTextToSpeechRequest("uhm"))
    else:
        robot.tts.request(NaoqiTextToSpeechRequest("Im sorry i could not formulate a response"))

    chat_history.append(gpt_request + text.response)
    return response

chat_history = []

try:

    for i in range(100):
        robot.tts.request(NaoqiTextToSpeechRequest("Beep!"))
        time.sleep(.5)
        print(" ----- Conversation turn", i)
        gpt_request = dict()

        transcript_msg = whisper.request(GetTranscript())
        transcript = transcript_msg.transcript
        print("Whisper transcript:", transcript)
        gpt_request["transcript"] = transcript


        # add face detection information
        if faces_buffer.qsize():
            # peek the item
            faces = faces_buffer.get_nowait()
            faces_buffer.put_nowait(faces)

            # = 100 is roughtly 1m
            # 20 is roughly 5m
            def rough_distance_formula(face_height):
                return -0.05 * face_height + 6
            face_detection_llm_info = {i: {"distance": rough_distance_formula(x.h)} for i, x in enumerate(faces)}

            gpt_request["face_detection"] = face_detection_llm_info

        google_image= get_google_image()
        if google_image:
            try:
                # add visual information
                captions = captioning_model.get_captions(
                    image=google_image,
                    # Optional:
                    number_of_results=1,
                    language="en",
                )

                gpt_request["scene_description"] = captions[0]
            except Exception as e:
                print("Google error", e)


######
        response = get_chatgpt_response(gpt_request)
######
        if 'action' in response and 'visual_question' in response['action']:
            vquestion = response['action']['visual_question']
            try:
                answers = vqa_model.ask_question(
                    image=google_image,
                    question=vquestion,
                    # Optional:
                    number_of_results=1,
                )
                gpt_request["visual_answer"] = answers[0]
            except Exception as e:
                print("Google error", e)
            if "visual_answer" in gpt_request:
                response = get_chatgpt_response(gpt_request)

        try:
            if 'action' in response:
                action = response['action']
                if "move" in action:
                    x, y = action["move"]
                    robot.motion.request(NaoqiMoveToRequest(x, y, 0), block=False)
                if "rotate" in action:
                    r = action["rotate"]
                    robot.motion.request(NaoqiMoveToRequest(0, 0, r), block=False)
                if "wave" in action:
                    robot.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Hey_3"), block=False)

        except Exception:
            robot.tts.request(NaoqiTextToSpeechRequest("Oops"))

        if 'response' in response:
            robot.tts.request(NaoqiTextToSpeechRequest(response["response"]))






except KeyboardInterrupt:
    robot.stop()

robot.tts.request(NaoqiTextToSpeechRequest("Nice talking to you!"))
