# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging
from sic_framework.core import utils_cv2

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop

# Import the service(s) we will be using
from sic_framework.services.face_detection.face_detection import FaceDetection
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
    QueryResult,
    RecognitionResult,
)

# Import configuration(s) for the components
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf

# Import the message type(s) we're using
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage,
    CompressedImageMessage,
)

# Import libraries necessary for the demo
import json
import queue
import threading
from os.path import abspath, join
from time import sleep
from subprocess import call
import cv2
import numpy as np


class KioskApp(SICApplication):
    """
    Kiosk application demo.
    Showcases how a kiosk robot could function. After detecting a face it will address a potential customer.

    IMPORTANT:
    First, you need to obtain your own keyfile.json from Dialogflow, place it in conf/dialogflow, and point to it in the main 
    How to get a key? See https://social-ai-vu.github.io/social-interaction-cloud/tutorials/6_google_cloud.html

    Second, you need to have intents for order_pizza, pizza_type (+entities), look_for_bathroom, and no fallback intents.
    You can find the source for an example dialogflow agent in demos/desktop/SICv2Example_freeflow.zip.

    Third, you need to have espeak installed.
    [Windows] download and install espeak: http://espeak.sourceforge.net/, add eSpeak/command-line to PATH
    [Linux] `sudo apt-get install espeak libespeak-dev`
    [MacOS] brew install espeak

    Fourth, the face-detection service and dialogflow service need to be running:
    1. pip install --upgrade social-interaction-cloud[dialogflow]
    2. in a new terminal: run-face-detection
    2. in a new terminal: run-dialogflow
    """

    def __init__(self, dialogflow_keyfile_path, sample_rate_hertz=44100, language="en",
                 fx=1.0, fy=1.0, flip=1, log_level=sic_logging.INFO):
        # Call parent constructor (handles singleton initialization)
        super(KioskApp, self).__init__(log_level=log_level)
        
        # Demo-specific initialization
        self.dialogflow_keyfile_path = dialogflow_keyfile_path
        self.sample_rate_hertz = sample_rate_hertz
        self.language = language
        self.fx = fx
        self.fy = fy
        self.flip = flip
        self.imgs_buffer = queue.Queue(maxsize=1)
        self.faces_buffer = queue.Queue(maxsize=1)
        self.sees_face = False
        self.desktop = None
        self.face_rec = None
        self.dialogflow = None
        self.can_listen = True
        self.session_id = np.random.randint(10000)
        
        self.setup()

    def setup(self):
        """Initialize and configure Desktop, face detection, and Dialogflow."""
        self.logger.info("Setting up Kiosk App...")
        
        # Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image
        camera_conf = DesktopCameraConf(fx=self.fx, fy=self.fy, flip=self.flip)

        # Connect to the services
        self.desktop = Desktop(camera_conf=camera_conf)
        self.face_rec = FaceDetection(input_source=self.desktop.camera)

        # Send back the outputs to this program
        self.desktop.camera.register_callback(self.on_image)
        self.face_rec.register_callback(self.on_faces)

        # set up the config for dialogflow
        dialogflow_conf = DialogflowConf(
            keyfile_json=json.load(open(self.dialogflow_keyfile_path)),
            sample_rate_hertz=self.sample_rate_hertz,
            language=self.language
        )

        # initiate Dialogflow object
        self.dialogflow = Dialogflow(ip="localhost", conf=dialogflow_conf, input_source=self.desktop.mic)

        # register a callback function to act upon arrival of recognition_result
        self.dialogflow.register_callback(self.on_dialog)

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
        attempts = 1
        max_attempts = 3
        init = True
        while True:
            try:
                if self.sees_face and self.can_listen:
                    if init:
                        self.local_tts("Hi there! How may I help you?")
                        init = False

                    reply = self.dialogflow.request(GetIntentRequest(self.session_id))

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