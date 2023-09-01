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
from vertexai.language_models import ChatModel, InputOutputTextPair

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
from vertexai.vision_models import ImageQnAModel, ImageCaptioningModel, MultiModalEmbeddingModel
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
# vqa_model = ImageQnAModel.from_pretrained("imagetext@001")
# captioning_model = ImageCaptioningModel.from_pretrained("imagetext@001")

model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")



def get_google_image():
    image = imgs_buffer.get()
    img_byte_arr = io.BytesIO()
    Image.fromarray(image).save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return VertexImage(img_byte_arr)


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
Do not be overly helpful or robotic, and act as human as possible. Do not always end with "how can i help you" but act
natural in the environment. 

Some information about the world
You are in the Social AI robotics lab. Behind you is the door to the hall.
The coffee machine is in the hall next to the sink. In the hall you can also find the toilets.

You will be provided with a JSON string containing processed information about the world. The JSON string may have the following fields:
    scene_description: A string describing the scene.
    transcript: A string containing the user's spoken query.
    visual_answer: A string containing the answer to the user's visual question.


Here is an example of a JSON string that you might receive:
{
'{"scene_description": "a room with a lot of lights on the ceiling", "transcript":"Hey there, what lab is this?"}'
}

Use this sensor information to form a reply. This reply must also be in the form of a json string. 
Do not output anything beside the json. Here is an example of a JSON response that you could return:
{
'{"response":"Hello! I am Nao, the robot assistant.  This is the Social AI robotics lab. Can I help you with anything?", "action":{"wave":true}}'
}
or 
{
'{"response":"Ofcourse i can move around", "action": {"move":[0.2, 1.3]} }'
}



possible actions: 
"action":{'{"wave":true}'}  perform a waving gesture
"action":{'{"sit":true}'}   sit down to a safe resting position
"action":{'{"stand":true}'}  stand up, necessary to walk and turn around
"action": {'{"rotate": r}'}   (radians, positive is turning to the right also known as clockwise, 1.57 is a quarter turn to the left)
"action": {'{"move":[x, y]}'}   (meters, x positive is forward, negative is backward , y positive is left, negative is right)

You can also use a visual question answer system to help you answer questions about the surroundings. 
For example, to check if you are looking at a banana, output the following json:
{
'{"action":{"visual_question":"Is there a banana in the image?"}}'
}
or to find out what color the t-shirt the person in front of you is wearing
{
'{"action":{"visual_question":"What color is the shirt?"}}'
}
do not hesitate to use this system whenever needed.


You will receive the same prompt as before, but augmented with a "visual_answer" field. 
Do not output a response or other action when asking visual questions, they will not be processed.
Do not ask a visual question after a prompt with a visual answer.


Example:
{
'{"scene_description": "a man in a room looking out a window", "visual_answer":"The room has a window", "transcript":"Can you see a window?"}'
}

If the transcript is empty. You do not have to provide a response. You may use this time for reasoning or actions to move around the room and gather information.

Current goal:
When detecting someone for the first time, greet them and wave. Ask them if they need any help.

IMPORTANT:
Do not output anything beside a valid json response.
Only respond in english.

"""
chat_model = ChatModel.from_pretrained("chat-bison@001")

chat = chat_model.start_chat(
    context=system_message,
    examples=[
        # InputOutputTextPair(
        #     input_text='{"transcript":"Hey there, what lab is this?"}',
        #     output_text='{"response":"Hello! I am Nao, the robot assistant.  This is the Social AI robotics lab. Can I help you with anything?", "action":{"wave":true}}',
        # ),
        InputOutputTextPair(
            input_text="What do I like?",
            output_text='{"response":"Ofcourse i can move around", "action": {"move":[0.2, 1.3]} }',
        ),
    ],
    temperature=0.3,
)

chat.send_message("Do you know any cool events this weekend?")


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
        # robot.tts.request(NaoqiTextToSpeechRequest("Beep!"))
        print(" ----- Conversation turn", i)
        gpt_request = dict()

        time.sleep(.5)
        robot.leds.request(NaoFadeRGBRequest("FaceLeds", 0, 1, 0, 0), block=False)
        transcript_msg = whisper.request(GetTranscript())
        transcript = transcript_msg.transcript
        print("Whisper transcript:", transcript)
        robot.leds.request(NaoFadeRGBRequest("FaceLeds", 0, 0, 1, 0), block=False)




        google_image = get_google_image()
        try:
            embeddings = model.get_embeddings(
                image=google_image,
                contextual_text=transcript,
            )
            image_embedding = embeddings.image_embedding
            text_embedding = embeddings.text_embedding
            gpt_request["image_embedding"] = image_embedding
            gpt_request["text_embedding"] = text_embedding

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
                gpt_request["visual_answer"] = "Error getting visual answer"
                print("Google error", e)
            response = get_chatgpt_response(gpt_request)

        if 'response' in response:
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
                if "sit" in action:
                    robot.motion.request(NaoPostureRequest("Sit"))
                if "stand" in action:
                    robot.motion.request(NaoPostureRequest("Stand"))

        except Exception:
            robot.tts.request(NaoqiTextToSpeechRequest("Oops"))








except KeyboardInterrupt:
    robot.stop()

robot.tts.request(NaoqiTextToSpeechRequest("Nice talking to you!"))
