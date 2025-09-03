import json
from os import environ
from os.path import abspath, join

import numpy as np

from sic_framework.devices.franka import Franka
from sic_framework.devices.common_franka.franka_motion_recorder import (
    GoHomeRequest,
    PandaJointsRecording,
    PlayRecordingRequest,
)
from sic_framework.devices.desktop import Desktop
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
)

"""
This demo allows you to control the Franka robot and execute prerecorded motions using voice commands via Dialogflow.
To run this demo, you need to install the correct version of the panda-python dependency. A version mismatch will cause problems.
See Installation point 3 for instructions on installing the correct version: https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/2412675074/Getting+started+with+Franka+Emika+Research+3#Installation%3A
"""

def on_dialog(message):
    if message.response:
        if message.response.recognition_result.is_final:
            print("Transcript:", message.response.recognition_result.transcript)

desktop = Desktop()
desktop_mic = desktop.mic
franka = Franka()
motion_file = "wave.motion"

try:
    # load the key json file
    with open(abspath(join("..", "..", "conf", "dialogflow", "dialogflow-key.json"))) as f:
        keyfile_json = json.load(f)
except FileNotFoundError:
    print("no keyfile found, using None")
    keyfile_json = None  # or you could create a default dict if needed

dialogflow_conf = DialogflowConf(keyfile_json=keyfile_json, sample_rate_hertz=44100, language="en")

dialogflow = Dialogflow(conf=dialogflow_conf, input_source=desktop_mic)

print("Initialized dialogflow... registering callback function")
# register a callback function to act upon arrival of recognition_result
dialogflow.register_callback(callback=on_dialog)

# Demo starts
print(" -- Starting Demo -- ")
x = np.random.randint(10000)

try:
    for i in range(25):
        print(" ----- Conversation turn", i)
        # create context_name-lifespan pairs. If lifespan is set to 0, the context expires immediately
        contexts_dict = {"name": 1}
        reply = dialogflow.request(GetIntentRequest(x, contexts_dict))

        query_text = reply.response.query_result.query_text
        print("Query text:", query_text)
        if "home" in query_text.lower():
            print("Going home!")
            franka.motion_recorder.request(GoHomeRequest())
        if "wave" in query_text.lower() or "waving" in query_text.lower():
            print("Waving!")
            loaded_joints = PandaJointsRecording.load(motion_file)
            print("--------second replay by loading the motion file we just recorded--------")
            franka.motion_recorder.request(PlayRecordingRequest(loaded_joints, frequency))

except KeyboardInterrupt:
    print("Stopping dialogflow component.")
    dialogflow.stop()
