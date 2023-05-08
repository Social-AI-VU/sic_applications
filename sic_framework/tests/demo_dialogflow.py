import io
import json
import logging
import time

import numpy as np
import pyaudio
from sic_framework.core.connector import SICApplication
from sic_framework.devices.common_naoqi.nao_motion import NaoPostureRequest, NaoRestRequest
from sic_framework.devices.common_naoqi.naoqi_microphone import NaoqiMicrophoneSensor
from sic_framework.devices.common_naoqi.naoqi_speakers import NaoqiTextToSpeechRequest
from sic_framework.devices.desktop.desktop_microphone import DesktopMicrophone
from sic_framework.devices.nao import Nao

from sic_framework.services.dialogflow.dialogflow_service import DialogflowService, DialogflowConf, GetIntentRequest, \
    RecognitionResult, QueryResult

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100



def on_dialog(message):
    if message.response:
        # print(message.response.recognition_result.transcript)
        if message.response.recognition_result.is_final:
            print("Transcript:", message.response.recognition_result.transcript)


class DemoDialogflow(SICApplication):

    def run(self) -> None:
        nao = Nao(device_id='nao', application=self)

        # conf = DialogflowConf(sample_rate_hertz=44100, project_id='dialogflow-test-project-376814')
        keyfile_json = json.load(open("dialogflow-test-project-wiggers.json"))

        conf = DialogflowConf(keyfile_json=keyfile_json,
                              project_id='dialogflow-test-project-376814', sample_rate_hertz=16000, )

        dialogflow = self.start_service(DialogflowService, device_id='local', inputs_to_service=[nao.mic],
                                        log_level=logging.INFO, conf=conf)
        dialogflow.register_callback(on_dialog)

        nao.tts.request(NaoqiTextToSpeechRequest("Hello!"))

        print(" -- Ready -- ")

        x = np.random.randint(10000)

        for i in range(25):
            print(" ----- Conversation turn", i)
            reply = dialogflow.request(GetIntentRequest(x))

            print(reply.intent)

            if reply.fulfillment_message:
                text = reply.fulfillment_message
                print("Reply:", )
                nao.tts.request(NaoqiTextToSpeechRequest(text))

            if reply.intent:
                print("Intent:", reply.intent)

                name = reply.response.query_result.intent.display_name
                if name == "get_up":
                    nao.motion.request(NaoPostureRequest("Stand"))
                if name == "sit_down":
                    nao.motion.request(NaoRestRequest())

            # if reply.response.output_audio:
            #     print("reply.response.output_audio", reply.response.output_audio)
            #     audio = reply.response.output_audio
            #     song = AudioSegment.from_wav(io.BytesIO(audio))
            #     play(song)


if __name__ == '__main__':
    test_app = DemoDialogflow()

    test_app.run()
    # test_app.stop()

"""

export GOOGLE_APPLICATION_CREDENTIALS=/home/thomas/vu/SAIL/docker/sic/sic_framework/services/dialogflow/test-hync.json
"""
