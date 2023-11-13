import io
import json

import google
from google.cloud import aiplatform
from vertexai.vision_models import ImageQnAModel
from vertexai.vision_models import Image as VertexImage
from PIL import Image
from google.oauth2.service_account import Credentials

import queue
import cv2
from vertexai.vision_models import ImageQnAModel
from vertexai.vision_models import Image as VertexImage

from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices import Nao, Pepper

imgs = queue.Queue()
def on_image(image_message: CompressedImageMessage):

    try:
        imgs.get_nowait()
    except queue.Empty:
        pass

    imgs.put(image_message.image)


robot = Nao(ip="192.168.0.226")
robot.top_camera.register_callback(on_image)


credentials = Credentials.from_service_account_info(json.load(open("sicproject-vertex.json")))

aiplatform.init(project="sicproject-397617",
                # location="europe-west4", not supported yet
                credentials=credentials)
model = ImageQnAModel.from_pretrained("imagetext@001")



for i in range(100):
    img = imgs.get()
    print(img.shape, img.dtype, img.max())


    img_byte_arr = io.BytesIO()
    Image.fromarray(img).save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    answers = model.ask_question(
        image=VertexImage(img_byte_arr),
        question="Do you see a window?",
        # Optional:
        number_of_results=1,
    )

    print(answers)

    cv2.imshow('', img)
    cv2.waitKey(1)


