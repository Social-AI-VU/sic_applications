import json
import numpy as np
import re
import random
import time

from sic_framework.core.message_python2 import AudioMessage
from sic_framework.core.utils import is_sic_instance
from sic_framework.services.dialogflow.dialogflow_service import DialogflowConf, \
    GetIntentRequest, RecognitionResult, QueryResult, Dialogflow
from sic_framework.services.webserver.webserver_pepper_tablet import Webserver, HtmlMessage, WebserverConf, TranscriptMessage, ButtonClicked
from sic_framework.devices.common_naoqi.pepper_tablet import NaoqiTablet, UrlMessage
from sic_framework.devices.common_naoqi.naoqi_microphone import NaoqiMicrophone
from sic_framework.devices.desktop.desktop_microphone import DesktopMicrophone
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest, NaoqiTextToSpeech




def on_dialog(message):
    """
    Callback function to handle dialogflow responses.
    """
    if is_sic_instance(message, RecognitionResult):
        # print("TranscriptMessage:", message.response.recognition_result.transcript)
        # if message.response.recognition_result.is_final:
            # web_server.send_message(TranscriptMessage(message.response.recognition_result.transcript + "/" + str(message.ip)))
            web_server.send_message(TranscriptMessage(message.response.recognition_result.transcript))
            # extract_and_compare_number(message.response.recognition_result.transcript, rand_int)

def extract_and_compare_number(script, x):
    """
    Extracts numbers from the dialogflow script and compares them with the a random number 'x'.
    """
    global last_number, number, response_flag
    if "number" not in globals():
        print("initializing number")
        number = None
    if "response_flag" not in globals():
        print("initializing response flag")
        response_flag = False
    # pattern to match numbers in script in case they're not represented in digits
    pattern = r'\b(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\b'
    numbers_found = re.findall(pattern, script)
    last_number = number

    # convert number words to digits
    for num in numbers_found:
        if num.isdigit():
            number = int(num)
        else:
            number_mapping = {
                "one": 1,
                "two": 2,
                "three": 3,
                "four": 4,
                "five": 5,
                "six": 6,
                "seven": 7,
                "eight": 8,
                "nine": 9,
                "ten": 10
            }
            number = number_mapping[num]

    # if a new number is given (guessed), reset the flag to false
    if last_number != number:
        print("setting response flag")
        response_flag = False

    if numbers_found and response_flag is False:
        if number > x:
            # pepper say
            text = f"The number {number} is higher than {x}, guess lower."
            print(text)
            # nao_tts.request(NaoqiTextToSpeechRequest(text))
            response_flag = True

        elif number < x:
            text = f"The number {number} is lower than {x}, guess higher."
            print(text)
            # nao_tts.request(NaoqiTextToSpeechRequest(text))

            response_flag = True


        elif number == x:
            text ="you got the right number"
            print(text)
            # nao_tts.request(NaoqiTextToSpeechRequest(text))
            response_flag = True

    elif number == x:
        text ="you already got the right number!!"
        print(text)
        # nao_tts.request(NaoqiTextToSpeechRequest(text))

    elif numbers_found:
        text = f"The number {number} is the same you guessed previously."
        print(text)
        # nao_tts.request(NaoqiTextToSpeechRequest(text))

    else:
        print("No number found in the script.")



def on_button_click(message):
    """
    Callback function for button click event from a web client.
    """
    if is_sic_instance(message, ButtonClicked):
        if message.button:
            print("start listening")
            # nao_tts.request(NaoqiTextToSpeechRequest("Guess a number from 1 to 10"))
            time.sleep(2.0)
            x = np.random.randint(10000)
            for i in range(25):
                print(" ----- Conversation turn", i)
                reply = dialogflow.request(GetIntentRequest(x))
                if reply.response.query_result.query_text:
                        print("pepper-------------------")
                        print(reply.response.query_result.query_text)
                        extract_and_compare_number(reply.response.query_result.query_text, rand_int)




port = 8080
machine_ip = '10.15.3.116'
robot_ip = '192.168.0.165'
# the HTML file to be rendered
html_file = "demo_pepper_guess_number.html"
web_url = f'https://{machine_ip}:{port}/'
# the random number that an user should guess
rand_int = random.randint(1, 10)


# Microphone device setup
# local
microphone = DesktopMicrophone(ip='localhost')
# pepper
# microphone = NaoqiMicrophone(ip=robot_ip)

# NaoqiTextToSpeech setup
# nao_tts = NaoqiTextToSpeech(ip=robot_ip)


# NaoqiTablet setup
# pepper_tablet = NaoqiTablet(ip=robot_ip)
# pepper_tablet.send_message(UrlMessage(web_url))

# webserver setup
web_conf = WebserverConf(host="0.0.0.0", port=port)
web_server = Webserver(ip='localhost', conf=web_conf)
# connect the output of webserver by registering it as a callback.
# the output is a flag to determine if the button has been clicked or not
web_server.register_callback(on_button_click)


# dialogflow setup
keyfile_json = json.load(open("test-free-version.json"))
# local microphone
sample_rate_hertz = 44100
# pepper's micriphone
# sample_rate_hertz = 16000

conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=sample_rate_hertz)
dialogflow = Dialogflow(ip='localhost', conf=conf)
dialogflow.register_callback(on_dialog)
dialogflow.connect(microphone)

# send html to Webserver
with open(html_file) as file:
    data = file.read()
    print("sending-------------")
    web_server.send_message(HtmlMessage(data))
