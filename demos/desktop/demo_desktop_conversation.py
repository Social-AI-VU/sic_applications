# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging
from sic_framework.core import utils_cv2

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop

# Import configuration(s) for the components
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf

# Import the message type(s) we're using
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage,
    CompressedImageMessage,
)
from sic_framework.core.message_python2 import AudioRequest

# Import the service(s) we will be using
from sic_framework.services.face_detection.face_detection import FaceDetection
from sic_framework.services.google_tts.google_tts import (
    GetSpeechRequest,
    Text2Speech,
    Text2SpeechConf,
)
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
)
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest

# Import libraries necessary for the demo
from time import sleep
import json
from os import environ
import queue
import threading
from os.path import abspath, join
from subprocess import call
from dotenv import load_dotenv
import cv2
import numpy as np


class ConversationApp(SICApplication):
    """

    This demo shows how to use the dialogflow to get a transcript and an OpenAI GPT model to get responses to user input,
    and a secret API key is required to run it


    IMPORTANT

    First, you need to obtain your own google-key.json from Google, place it in conf/google, and point to it in the main.
    You need to have dialogflow and Google Text-to-Speech services enabled and set the correct permissions.
    See https://social-ai-vu.github.io/social-interaction-cloud/external_apis/google_cloud.html#google-cloud-platform-guide

    If you want to run kiosk demo, your dialogflow agent needs to have the correct intents and entities. After you
    created your dialogflow agent in the Google Cloud environment you can import Dialogflow_agent_for_SIC_demo.zip
    to import the required intents and entities.

    (Optionally) if you want to use a local TTS (set local_tts=True) instead of Google TTS, you need to have espeak installed.
    [Windows]
    download and install espeak: http://espeak.sourceforge.net/
    add eSpeak/command-line to PATH
    [Linux]
    `sudo apt-get install espeak libespeak-dev`
    [macOS]
    brew install espeak

    Second, you need an openAI key:
    Generate your personal env api key here: https://platform.openai.com/api-keys
    Either add your env key to your systems variables (and comment the next line out) or
    create a .env file in the conf/env folder and add your key there like this:
    OPENAI_API_KEY="your key"

    Third, Face Recognition, Dialogflow, GoogleTTS and OpenAI GPT service need to be running:

    1. pip install --upgrade social-interaction-cloud[dialogflow,google-tts,openai-gpt]
        Note: on macOS you might need use quotes pip install --upgrade "social-interaction-cloud[...]"
    2. each in a new terminal: run-face-detection
    3. run-dialogflow
    4. run-google-tts
    5. run-gpt
    """

    def __init__(self, google_keyfile_path, env_path=None, local_tts=False):
        # Call parent constructor (handles singleton initialization)
        super(ConversationApp, self).__init__()
        
        # Demo-specific initialization
        self.google_keyfile_path = google_keyfile_path
        self.env_path = env_path
        self.sample_rate_hertz = 44100
        self.language = "en"
        self.fx = 1.0
        self.fy = 1.0
        self.flip = 1
        self.imgs_buffer = queue.Queue(maxsize=1)
        self.faces_buffer = queue.Queue(maxsize=1)
        self.sees_face = False
        self.desktop = None
        self.face_rec = None
        self.gpt = None
        self.dialogflow = None
        self.can_listen = True
        self.session_id = np.random.randint(10000)
        self.local_tts = local_tts
        self.tts = None
        
        # Configure logging
        self.set_log_level(sic_logging.INFO)

        # set log file path if needed
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")
        
        self.setup()

    def setup(self):
        """Initialize and configure Desktop, GPT, and Dialogflow."""
        self.logger.info("Setting up Conversation App...")
        
        # Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image
        camera_conf = DesktopCameraConf(fx=self.fx, fy=self.fy, flip=self.flip)

        # Connect Desktop
        self.desktop = (
            Desktop(camera_conf=camera_conf)
            if self.local_tts
            else Desktop(speakers_conf=SpeakersConf(sample_rate=24000))
        )

        # connect to services
        if not self.local_tts: # If Google TTS is used, initiate it.
            tts_conf = Text2SpeechConf(
                keyfile_json=json.load(open(self.google_keyfile_path))
            )
            self.tts = Text2Speech(conf=tts_conf)
        self.face_rec = FaceDetection(input_source=self.desktop.camera)

        # Send back the outputs to this program
        self.desktop.camera.register_callback(self._on_image)
        self.face_rec.register_callback(self._on_faces)

        # Setup GPT client
        # Generate your personal env api key here: https://platform.openai.com/api-keys
        # Either add your env key to your systems variables (and do not provide an env_path) or
        # create a .env file in the conf/ folder and add your key there like this:
        # OPENAI_API_KEY="your key"
        if self.env_path:
            load_dotenv(self.env_path)
        conf = GPTConf(openai_key=environ["OPENAI_API_KEY"])
        self.gpt = GPT(conf=conf)

        # set up the config for dialogflow
        dialogflow_conf = DialogflowConf(
            keyfile_json=json.load(open(self.google_keyfile_path)),
            sample_rate_hertz=self.sample_rate_hertz,
            language=self.language
        )

        # initiate Dialogflow object
        self.dialogflow = Dialogflow(ip="localhost", conf=dialogflow_conf, input_source=self.desktop.mic)

        # register a callback function to act upon arrival of recognition_result
        self.dialogflow.register_callback(self._on_dialog)

    def _on_image(self, image_message: CompressedImageMessage):
        self.imgs_buffer.put(image_message.image)

    def _on_faces(self, message: BoundingBoxesMessage):
        self.faces_buffer.put(message.bboxes)
        if message.bboxes:
            self.sees_face = True

    def _on_dialog(self, message):
        """
        Callback function for Dialogflow recognition results.
        
        Args:
            message: The Dialogflow recognition result message.
        
        Returns:
            None
        """
        if message.response:
            if message.response.recognition_result.is_final:
                print("Transcript:", message.response.recognition_result.transcript)

    def speak(self, text):
        if self.local_tts:
            call(["espeak", "-s140 -ven+18 -z", text])
        else:
            # Request speech synthesis from Google TTS
            reply = self.tts.request(
                GetSpeechRequest(text=text, voice_name="en-US-Standard-C")
            )
            self.desktop.speakers.request(AudioRequest(reply.waveform, reply.sample_rate))

    def _kiosk_run_facedetection(self):
        while True:
            img = self.imgs_buffer.get()
            faces = self.faces_buffer.get()

            for face in faces:
                utils_cv2.draw_bbox_on_image(face, img)

            cv2.imshow("", img)
            cv2.waitKey(1)

    def _kiosk_run_dialogflow(self):
        attempts = 1
        max_attempts = 3
        init = True
        while not self.shutdown_event.is_set():
            try:
                if self.sees_face and self.can_listen:
                    if init:
                        self.speak("Hi there! How may I help you?")
                        init = False

                    reply = self.dialogflow.request(GetIntentRequest(self.session_id))

                    print("The detected intent:", reply.intent)

                    if reply.intent:
                        if "order_pizza" in reply.intent:
                            attempts = 1
                            self.speak("What kind of pizza would you like?")
                        elif "pizza_type" in reply.intent:
                            pizza_type = ""
                            if reply.response.query_result.parameters and "pizza_type" in reply.response.query_result.parameters:
                                pizza_type = reply.response.query_result.parameters["pizza_type"]
                            self.speak(f'{pizza_type} coming right up')
                            self.can_listen = False
                        elif "look_for_bathroom" in reply.intent:
                            attempts = 1
                            self.speak("The bathroom is down that hallway. Second door on your left")
                            self.can_listen = False
                    else:
                        self.speak("Sorry, I did not understand")
                        attempts += 1
                        if attempts == max_attempts:
                            self.can_listen = False
                else:
                    sleep(0.1)
            except KeyboardInterrupt:
                print("Stop the dialogflow component.")
                self.dialogflow.stop()
                break

    def run_kiosk_conversation(self):
        fd_thread = threading.Thread(target=self._kiosk_run_facedetection)
        df_thread = threading.Thread(target=self._kiosk_run_dialogflow)
        fd_thread.start()
        df_thread.start()

    def run_llm_conversation(self):
        """Main application logic."""
        self.logger.info("Starting Chat App")
        
        try:
            self.speak("What is your favorite hobby?")
            reply = self.dialogflow.request(GetIntentRequest(self.session_id))
            if reply.response.query_result.query_text:
                gpt_response = self.gpt.request(GPTRequest(
                    f'You are a chat bot. The bot just asked about a hobby of the user make a brief '
                    f'positive comment about the hobby and ask a '
                    f'follow up question expanding the conversation.'
                    f'This was the input by the user: "{reply.response.query_result.query_text}"'
                ))
                self.speak(gpt_response.response)
            
            self.logger.info("Chat completed")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    conversation_app = ConversationApp(
        google_keyfile_path=abspath(join('..', '..', 'conf', 'google', 'google-key.json')),
        env_path=abspath(join("..", "..", "conf", ".env")))
    conversation_app.run_llm_conversation()
    # or
    # conversation_app.run_kiosk_conversation()
