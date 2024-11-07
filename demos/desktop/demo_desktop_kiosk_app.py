import json
import queue
import threading
from os.path import abspath, join
from time import sleep
from subprocess import call

import cv2
import numpy as np
from sic_framework.core import utils_cv2
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage,
    CompressedImageMessage,
)
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.devices.desktop import Desktop
from sic_framework.services.face_detection.face_detection import FaceDetection

from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
    QueryResult,
    RecognitionResult,
)

""" 
This demo showcases how a kiosk robot could function. After detecting a face it will address a potential customer.

IMPORTANT

First, you need to obtain your own keyfile.json from Dialogflow, place it in conf/dialogflow, and point to it in the main 
How to get a key? See https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/2205155343/Getting+a+google+dialogflow+key for more information.

Second, you need to have intents for order_pizza, pizza_type (+entities), look_for_bathroom, and no fallback intents.
You can find the source for an example dialogflow agent in demos/desktop/SICv2Example_freeflow.zip.
If you can go to the settings of your dialogflow agent (on https://dialogflow.cloud.google.com/) and go to
import and export, you can restore the example dialogflow agent completely, or import the missing intents (don't forget
to remove the fallback intents) by uploading the example agent zip.

Third, you need to have espeak installed.
[Windows]
download and install espeak: http://espeak.sourceforge.net/
add eSpeak/command-line to PATH
[Linux]
`sudo apt-get install espeak libespeak-dev`
[MacOS]
brew install espeak

Fourth, the face-detection service and dialogflow service need to be running:

1. pip install --upgrade social-interaction-cloud[dialogflow]
2. in a new terminal: run-face-detection
2. in a new terminal: run-dialogflow

"""


class KioskApp:

    def __init__(self, dialogflow_keyfile_path, sample_rate_hertz=44100, language="en",
                 fx=1.0, fy=1.0, flip=1):
        self.imgs_buffer = queue.Queue(maxsize=1)
        self.faces_buffer = queue.Queue(maxsize=1)
        self.sees_face = False

        # Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image
        camera_conf = DesktopCameraConf(fx=fx, fy=fy, flip=flip)

        # Connect to the services
        self.desktop = Desktop(camera_conf=camera_conf)
        self.face_rec = FaceDetection()

        # Feed the camera images into the face recognition component
        self.face_rec.connect(self.desktop.camera)

        # Send back the outputs to this program
        self.desktop.camera.register_callback(self.on_image)
        self.face_rec.register_callback(self.on_faces)

        # set up the config for dialogflow
        dialogflow_conf = DialogflowConf(keyfile_json=json.load(open(dialogflow_keyfile_path)),
                              sample_rate_hertz=sample_rate_hertz, language=language)

        # initiate Dialogflow object
        self.dialogflow = Dialogflow(ip="localhost", conf=dialogflow_conf)

        # connect the output of DesktopMicrophone as the input of DialogflowComponent
        self.dialogflow.connect(self.desktop.mic)

        # register a callback function to act upon arrival of recognition_result
        self.dialogflow.register_callback(self.on_dialog)

        # flag to signal when the app should listen (i.e. transmit to dialogflow)
        self.can_listen = True

    def on_image(self, image_message: CompressedImageMessage):
        self.imgs_buffer.put(image_message.image)

    def on_faces(self, message: BoundingBoxesMessage):
        self.faces_buffer.put(message.bboxes)
        if message.bboxes:
            self.sees_face = True

    def on_dialog(self, message):
        if message.response:
            if message.response.recognition_result.is_final:
                print("Transcript:", message.response.recognition_result.transcript)

    def local_tts(self, text):
        call(["espeak", "-s140 -ven+18 -z", text])

    def run_facedetection(self):
        while True:
            img = self.imgs_buffer.get()
            faces = self.faces_buffer.get()

            for face in faces:
                utils_cv2.draw_bbox_on_image(face, img)

            cv2.imshow("", img)
            cv2.waitKey(1)

    def run_dialogflow(self):
        x = np.random.randint(10000)

        attempts = 1
        max_attempts = 3
        init = True
        while True:
            try:
                if self.sees_face and self.can_listen:
                    if init:
                        self.local_tts("Hi there! How may I help you?")
                        init = False

                    reply = self.dialogflow.request(GetIntentRequest(x))

                    print("The detected intent:", reply.intent)

                    if reply.intent:
                        if "order_pizza" in reply.intent:
                            attempts = 1
                            self.local_tts("What kind of pizza would you like?")
                        elif "pizza_type" in reply.intent:
                            pizza_type = ""
                            if reply.response.query_result.parameters and "pizza_type" in reply.response.query_result.parameters:
                                pizza_type = reply.response.query_result.parameters["pizza_type"]
                            self.local_tts(f'{pizza_type} coming right up')
                            self.can_listen = False
                        elif "look_for_bathroom" in reply.intent:
                            attempts = 1
                            self.local_tts("The bathroom is down that hallway. Second door on your left")
                            self.can_listen = False
                    else:
                        self.local_tts("Sorry, I did not understand")
                        attempts += 1
                        if attempts == max_attempts:
                            self.can_listen = False
                else:
                    sleep(0.1)
            except KeyboardInterrupt:
                print("Stop the dialogflow component.")
                self.dialogflow.stop()
                break

    def run(self):
        fd_thread = threading.Thread(target=self.run_facedetection)
        df_thread = threading.Thread(target=self.run_dialogflow)
        fd_thread.start()
        df_thread.start()


if __name__ == "__main__":
    kiosk_app = KioskApp(abspath(join('..', '..', 'conf', 'dialogflow', 'dialogflow-tutorial.json')))
    kiosk_app.run()













