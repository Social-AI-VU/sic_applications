import json
import random
import re
import time
from os.path import abspath, join

import numpy as np
from sic_framework.core.utils import is_sic_instance
from sic_framework.devices.desktop import Desktop
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
    QueryResult,
    RecognitionResult,
)
from sic_framework.services.webserver.webserver_component import (
    ButtonClicked,
    HtmlMessage,
    TranscriptMessage,
    Webserver,
    WebserverConf,
)

"""
This demo shows you how to interact with a browser to play a “guess the number” game

The Dialogflow and Webserver should be running. You can start them with:
1. pip install social-interaction-cloud[dialogflow, webserver]
2. run-dialogflow && run-webserver
"""


def on_dialog(message):
    """
    Callback function to handle dialogflow responses.
    """
    if is_sic_instance(message, RecognitionResult):
        web_server.send_message(
            TranscriptMessage(message.response.recognition_result.transcript)
        )


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
    pattern = r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\b"
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
                "ten": 10,
            }
            number = number_mapping[num]

    # if a new number is given (guessed), reset the flag to false
    if last_number != number:
        print("setting response flag")
        response_flag = False

    if numbers_found and response_flag is False:
        if number > x:
            text = f"The number {number} is higher than {x}, guess lower."
            print(text)
            response_flag = True

        elif number < x:
            text = f"The number {number} is lower than {x}, guess higher."
            print(text)

            response_flag = True

        elif number == x:
            text = "you got the right number"
            print(text)
            response_flag = True

    elif number == x:
        text = "you already got the right number!!"
        print(text)

    elif numbers_found:
        text = f"The number {number} is the same you guessed previously."
        print(text)

    else:
        print("No number found in the script.")


def on_button_click(message):
    """
    Callback function for button click event from a web client.
    """
    if is_sic_instance(message, ButtonClicked):
        if message.button:
            print("start listening")
            print("Guess a number from 1 to 10")
            time.sleep(2.0)
            x = np.random.randint(10000)
            for i in range(25):
                print(" ----- Conversation turn", i)
                reply = dialogflow.request(GetIntentRequest(x))
                if reply.response.query_result.query_text:
                    print(reply.response.query_result.query_text)
                    extract_and_compare_number(
                        reply.response.query_result.query_text, rand_int
                    )


port = 8080
your_ip = "192.168.178.123"
# the HTML file to be rendered
html_file = "demo_guess_number.html"
web_url = f"http://{your_ip}:{port}/"
# the random number that an user should guess
rand_int = random.randint(1, 10)

# local desktop setup
desktop = Desktop()

# webserver setup
web_conf = WebserverConf(host="0.0.0.0", port=port)
web_server = Webserver(ip="localhost", conf=web_conf)
# connect the output of webserver by registering it as a callback.
# the output is a flag to determine if the button has been clicked or not
web_server.register_callback(on_button_click)
time.sleep(5)

# dialogflow setup
keyfile_json = json.load(
    open(
        abspath(
            join("..", "..", "..", "conf", "dialogflow", "dialogflow-tutorial.json")
        )
    )
)
# local microphone
sample_rate_hertz = 44100

conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=sample_rate_hertz)
dialogflow = Dialogflow(ip="localhost", conf=conf)
dialogflow.register_callback(on_dialog)
dialogflow.connect(desktop.mic)

time.sleep(1)
# send html to Webserver
with open(html_file) as file:
    data = file.read()
    print("sending html content-------------")
    web_server.send_message(HtmlMessage(text=data))
    print("now you can open the web page at", web_url)
