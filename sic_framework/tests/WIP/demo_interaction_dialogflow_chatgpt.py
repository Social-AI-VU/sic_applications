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
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest
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

    # try:
    #     faces = faces_buffer.get_nowait()
    #     for face in faces:
    #         utils_cv2.draw_bbox_on_image(face, image)
    # except queue.Empty:
    #     pass

    cv2.imshow('TopCamera', image[:, :, ::-1])
    cv2.waitKey(1)


# def on_faces(message: BoundingBoxesMessage):
#     try:
#         faces_buffer.get_nowait()  # remove previous message if its still there
#     except queue.Empty:
#         pass
#     faces_buffer.put(message.bboxes)


robot_ip = '146.50.60.32'
conf = NaoqiCameraConf(cam_id=0, res_id=2)
robot = Pepper(robot_ip, top_camera_conf=conf)

robot.top_camera.register_callback(display)

with open("openai_key", "r") as f:
    openai_key = f.read().strip()  # remove new line character

# Please use the 0.28 version of openai, and not the recently updated >1.0 version as this file has not been updated yet.
# pip install openai==0.28.1
# Setup GPT
conf = GPTConf(openai_key=openai_key)
gpt = GPT(conf=conf)

# Connect to the services
# face_det = DNNFaceDetection()

# Feed the camera images into the face recognition component
# face_det.connect(robot.top_camera)

# Send back the outputs to this program
# face_det.register_callback(on_faces)

# Set up text to speech using whisper
conf = WhisperConf(openai_key=openai_key)
whisper = SICWhisper(conf=conf)
whisper.connect(robot.mic)


# visual question answering
credentials = Credentials.from_service_account_info(json.load(open("sicproject-vertex.json")))

# https://cloud.google.com/python/docs/reference/aiplatform/latest/vertexai
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
robot.autonomous.request(NaoBasicAwarenessRequest(False))
robot.autonomous.request(NaoBackgroundMovingRequest(False))
robot.autonomous.request(NaoWakeUpRequest())

# robot.motion.request(NaoPostureRequest("Stand"))

print(" -- Ready -- ")

x = np.random.randint(10000)

ROBOT = robot.__class__.__name__

world_state = {}

system_message = f"""
You are a robot called {ROBOT}. You can help people to do things, like help them find the coffee machine. 
Do not be overly helpful or robotic, and act as human as possible. Do not always end with "how can i help you" but act
natural in the environment. 

IMPORTANT:
Do not output anything beside a JSON response.

Some information about the world
You are in the Social AI robotics lab. Behind you is the door to the hall.
The coffee machine is in the hall next to the sink. In the hall you can also find the toilets.

You will be provided with a JSON string containing processed information about the world. The JSON string may have the following fields:
    transcript: A string containing the user's spoken query.
    visual_answer: A string containing the answer to the user's visual question.


Here is an example of a JSON string that you might receive:
{
'{"transcript":"Hey there, what lab is this?"}'
}

Use this sensor information to form a reply. This reply must also be in the form of a json string. 
Do not output anything beside the json. Here is an example of a JSON response that you could return:
{
'{"response":"Hello! I am Nao, the robot assistant.  This is the Social AI robotics lab. Can I help you with anything?", "action":{"wave": true}}'
}
or 
{
'{"response":"Ofcourse i can move around", "action": {"move":[0.2, 1.3]} }'
}



possible actions: 
{'"action":{"busy": true}'}  do not listen for a 
{'"action":{"wave": true}'}  perform a waving gesture
{'"action":{"sit": true}'}   sit down to a safe resting position
{'"action":{"stand": true}'}  stand up, necessary to walk and turn around
{'"action":{"rotate": r}'}   (radians, positive is turning to the right also known as clockwise, 1.57 is a quarter turn to the left)
{'"action":{"move": [x, y]}'}   (meters, x positive is forward, negative is backward , y positive is left, negative is right)

You can also use a visual question answer system to help you answer questions about the surroundings. 
If you are asked anything about what you can see or your surroundings, use this system.
If you are aksed to find objects, use this system to check if they are in front of you.
For example, to check if you are looking at a banana, output the following json:
{
'{"action":{"visual_question":"Is there a banana in the image?"}}'
}
or to find out what color the t-shirt the person in front of you is wearing
{
'{"action":{"visual_question":"What color is the shirt?"}}'
}
You will receive the same prompt as before, but augmented with a "visual_answer" field, like this:
{
'{"visual_answer":"The shirt is red"}'
}
Phrase the visual questions in a objective and descriptive way. Do not hesitate to use this system whenever needed.

If you are asked to perform a task, such as looking throughout the room for an object, please use the visual question 
answer system multiple time, rotating a quarter turn every time to scan the room. To fully scan the room, rotate and check four times. 
Here is an example to look for a green exit sign. 
{
'"action":{"busy": true, "visual_question":"Is there a green exit sign in the image?", "rotate": 2}'
}

Use it only when you want to perform multiple visual questions.
Only use the busy action in combination with a visual question.
Do not use the busy action if you want someone to respond to you. 


IMPORTANT:
Only reply with a valid JSON string.
Do not output anything else besides JSON.

"""


def get_chatgpt_response(gpt_request):
    gpt_request = json.dumps(gpt_request)
    for i in range(2):
        try:
            print("Request:", gpt_request)
            text = gpt.request(GPTRequest(gpt_request, context_messages=chat_history, system_messages=system_message))
            print("Reply:", text.response)
            response = json.loads(text.response)
            chat_history.append(gpt_request + text.response)
            return response
        except json.decoder.JSONDecodeError:
            robot.tts.request(NaoqiTextToSpeechRequest("hmm"))
    else:
        robot.tts.request(NaoqiTextToSpeechRequest("Im sorry i could not formulate a response"))
    return dict()

chat_history = []

try:
    robot.tts.request(NaoqiTextToSpeechRequest("Beep!"))
    prev_req_is_busy = False
    for i in range(100):
        print(" ----- Conversation turn", i)
        gpt_request = dict()

        if not prev_req_is_busy:

            time.sleep(.5)
            robot.leds.request(NaoFadeRGBRequest("FaceLeds", 0, 1, 0, 0), block=False)
            transcript_msg = whisper.request(GetTranscript())
            transcript = transcript_msg.transcript
            print("Whisper transcript:", transcript)
            gpt_request["transcript"] = transcript
            robot.leds.request(NaoFadeRGBRequest("FaceLeds", 0, 0, 1, 0), block=False)
        prev_req_is_busy = False


        # add face detection information
        # if faces_buffer.qsize():
        #     # peek the item
        #     faces = faces_buffer.get_nowait()
        #     faces_buffer.put_nowait(faces)
        #
        #     # = 100 is roughtly 1m
        #     # 20 is roughly 5m
        #     def rough_distance_formula(face_height):
        #         return -0.05 * face_height + 6
        #     face_detection_llm_info = {i: {"distance": rough_distance_formula(x.h)} for i, x in enumerate(faces)}
        #
        #     gpt_request["face_detection"] = face_detection_llm_info

        google_image= get_google_image()
        # if google_image:
        #     try:

        #     except Exception as e:
        #         print("Google error", e)


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

                # add visual information
                captions = captioning_model.get_captions(
                    image=google_image,
                    # Optional:
                    number_of_results=1,
                    language="en",
                )
                gpt_request["scene_description"] = captions[0]
            except Exception as e:
                gpt_request["visual_answer"] = "Error getting visual answer"
                print("Google error", e)
            response.update(get_chatgpt_response(gpt_request))
            # try:
            #     del response['action']['busy']
            # except KeyError:
            #     pass

        if 'response' in response:
            if isinstance(response["response"], str):
                robot.tts.request(NaoqiTextToSpeechRequest(response["response"]))

        try:
            if 'action' in response:
                action = response['action']
                if "move" in action:
                    x, y = action["move"]
                    robot.motion.request(NaoqiMoveToRequest(x, y, 0), block=True)
                if "rotate" in action:
                    r = action["rotate"]
                    robot.motion.request(NaoqiMoveToRequest(0, 0, r), block=True)
                if "wave" in action:
                    robot.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Hey_3"), block=True)
                    time.sleep(1)
                if "sit" in action:
                    robot.motion.request(NaoPostureRequest("Crouch"))
                if "stand" in action:
                    robot.motion.request(NaoPostureRequest("Stand"))
                if 'busy' in action:
                    print("Busy, skipping next audio input")
                    prev_req_is_busy = True
        except Exception:
            robot.tts.request(NaoqiTextToSpeechRequest("Oops"))








except KeyboardInterrupt:
    robot.stop()

robot.tts.request(NaoqiTextToSpeechRequest("Nice talking to you!"))
