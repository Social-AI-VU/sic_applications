"""
TODO explain dialogflow
bi-directional stream
a response is sent per audio chunk, but sending a long audio chunk might generate multiple responses.

https://github.com/googleapis/python-dialogflow/blob/main/samples/snippets/detect_intent_stream.py
"""
import threading
import time

import google
from google.cloud import dialogflow
from google.oauth2.service_account import Credentials
from sic_framework import SICComponentManager
from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import AudioMessage, SICConfMessage, SICMessage, SICRequest, SICStopRequest, SICIgnoreRequestMessage
from sic_framework.core.utils import is_sic_instance
from six.moves import queue


class GetIntentRequest(SICRequest):
    def __init__(self, session_id=0):
        """
        Every dialogflow conversation must use a (semi) unique conversation id to keep track
        of the conversation. The conversation is forgotten after 20 minutes.
        :param session_id: a (randomly generated) id, but the same one for the whole conversation
        """
        super().__init__()
        self.session_id = session_id

    

class StopListeningMessage(SICMessage):
    def __init__(self, session_id=0):
        """
        Stop the conversation and determine a last intent. Dialogflow automatically stops listening when it thinks the
        user is done talking, but this can be used to force intent detection as well.
        :param session_id: a (randomly generated) id, but the same one for the whole conversation
        """
        super().__init__()
        self.session_id = session_id

class RecognitionResult(SICMessage):
    def __init__(self, response):
        """
        Dialogflow's understanding of the conversation up to that point. Is streamed during the execution of the request
        to provide interim results.
        Python code example:

        message = RecognitionResult()
        text = message.response.recognition_result.transcript


        Example:

        recognition_result {
          message_type: TRANSCRIPT
          transcript: "hey how are you"
          is_final: true
          confidence: 0.948654055595398
          speech_end_offset {
            seconds: 1
            nanos: 770000000
          }
          language_code: "en-us"
        }


        """
        self.response = response


class QueryResult(SICMessage):
    def __init__(self, response):
        """
        The Dialogflow agent's response.
        Python code example:

        message = QueryResult()
        text = message.response.query_result.fulfillment_text
        intent_name = message.response.query_result.intent.display_name


        Example data:

        response_id: "3bd4cd13-78a0-411c-afaf-6facf23a4649-18dedd3b"
        query_result {
          query_text: "hey how are you"
          action: "input.welcome"
          parameters {
          }
          all_required_params_present: true
          fulfillment_text: "Greetings! How can I assist?"
          fulfillment_messages {
            text {
              text: "Greetings! How can I assist?"
            }
          }
          intent {
            name: "projects/dialogflow-test-project-376814/agent/intents/6f3dc378-8b67-4e85-86c0-4c02f818abef"
            display_name: "Default Welcome Intent"
          }
          intent_detection_confidence: 0.4754425585269928
          language_code: "en"
        }
        webhook_status {
        }


        """
        # the raw dialogflow response
        self.response = response

        # some helper variables that extract useful data
        self.intent = None
        if "query_result" in response and response.query_result.intent:
            self.intent = response.query_result.intent.display_name

        self.fulfillment_message = None
        if "query_result" in response and len(response.query_result.fulfillment_messages):
            self.fulfillment_message = str(response.query_result.fulfillment_messages[0].text.text[0])


class DialogflowConf(SICConfMessage):
    def __init__(self, keyfile_json:dict, sample_rate_hertz: int = 44100,
                 audio_encoding=dialogflow.AudioEncoding.AUDIO_ENCODING_LINEAR_16, language: str = 'en-US'):
        """
        :param keyfile_json         Dict of google service account json key file, which has access to your dialogflow
                                    agent. Example `keyfile_json = json.load(open("my-dialogflow-project.json"))`
        :param sample_rate_hertz    44100Hz by default. Use 16000 for a Nao/Pepper robot.
        :param audio_encoding       encoding for the audio
        :param language             the language of the Dialogflow agent
        """
        SICConfMessage.__init__(self)

        # init Dialogflow variables
        self.language_code = language
        self.project_id = keyfile_json["project_id"]
        self.keyfile_json = keyfile_json
        self.sample_rate_hertz = sample_rate_hertz
        self.audio_encoding = audio_encoding


class DialogflowService(SICComponent):
    """
    Notes:
        This service listens to both AudioMessages and GetIntentRequests.
        As soon as an intent is received, it will start streaming the audio to dialogflow, and while it is listening
        send out intermediate results as RecognitionResult messages. This all occurs on the same channel.

        Requires audio to be no more than 250ms chunks as interim results are given a few times a second, and we block
        reading a request until a new audio message is available.

        The buffer length is 1 such that it discards audio before we request it to listen. The buffer is updated as
        new audio becomes available by the register_message_handler. This queue enables the generator to wait for new
        audio messages, and yield them to dialogflow. The request generator SHOULD be quite fast, fast enough
        that it won't drop messages due to the queue size of 1.
    """

    def __init__(self, *args, **kwargs):
        self.responses = None
        super().__init__(*args, **kwargs)

        self.dialogflow_is_init = False
        self.init_dialogflow()

    def init_dialogflow(self):
        # Setup session client
        credentials = Credentials.from_service_account_info(self.params.keyfile_json)
        self.session_client = dialogflow.SessionsClient(credentials=credentials)

        # Set default audio parameters
        self.dialogflow_audio_config = dialogflow.InputAudioConfig(
            audio_encoding=self.params.audio_encoding,
            language_code=self.params.language_code,
            sample_rate_hertz=self.params.sample_rate_hertz,
        )

        # TODO for text to speech, add this to the first StreamingDetectIntentRequest call
        synt_conf = dialogflow.SynthesizeSpeechConfig(
            effects_profile_id="en-US-Neural2-F"
        )
        self.output_audio_config = dialogflow.OutputAudioConfig(
            audio_encoding=dialogflow.OutputAudioEncoding.OUTPUT_AUDIO_ENCODING_MP3,
            sample_rate_hertz=44100,
            synthesize_speech_config=synt_conf,
        )

        self.query_input = dialogflow.QueryInput(audio_config=self.dialogflow_audio_config)
        self.message_was_final = threading.Event()
        self.audio_buffer = queue.Queue(maxsize=1)

        self.dialogflow_is_init = True

    def on_message(self, message):
        if is_sic_instance(message, AudioMessage):
            self.logger.debug_framework_verbose("Received audio message")
            # update the audio message in the queue
            try:
                self.audio_buffer.put_nowait(message.waveform)
            except queue.Full:
                self.audio_buffer.get_nowait()
                self.audio_buffer.put_nowait(message.waveform)

        if is_sic_instance(message, StopListeningMessage):
            # force the request generator to break, which indicates to dialogflow we want an intent for the
            # audio sent so far.
            self.message_was_final.set()
            # time.sleep(1)
            del self.session_client
            self.dialogflow_is_init = False

    def on_request(self, request):
        if not self.dialogflow_is_init:
            self.init_dialogflow()

        if is_sic_instance(request, GetIntentRequest):
            reply = self.get_intent(request)
            return reply

        raise NotImplementedError("Unknown request type {}".format(type(request)))

    def request_generator(self, session_path):
        try:
            # first request to Dialogflow needs to be a setup request with the session parameters
            # optional: output_audio_config=self.output_audio_config
            yield dialogflow.StreamingDetectIntentRequest(session=session_path,
                                                          query_input=self.query_input)

            start_time = time.time()

            while not self.message_was_final.is_set():
                chunk = self.audio_buffer.get()
                yield dialogflow.StreamingDetectIntentRequest(input_audio=chunk)

            # unset flag for next loop
            self.message_was_final.clear()
        except Exception as e:
            # log the message instead of gRPC hiding the error, but do crash
            self.logger.exception("Exception in request iterator")
            raise e

    @staticmethod
    def get_conf():
        return DialogflowConf()

    @staticmethod
    def get_inputs():
        return [GetIntentRequest, StopListeningMessage, AudioMessage]

    @staticmethod
    def get_output():
        return QueryResult

    def get_intent(self, input):
        self.message_was_final.clear()  # unset final message flag

        session_path = self.session_client.session_path(self.params.project_id, input.session_id)
        self.logger.debug("Executing dialogflow request with session id {}".format(input.session_id))

        requests = self.request_generator(session_path)  # get bi-directional request iterator

        # responses is a bidirectional iterator object, providing after
        # consuming each yielded request in the requests generator
        try:
            responses = self.session_client.streaming_detect_intent(requests)
        except google.api_core.exceptions.InvalidArgument as e:
            return QueryResult(dict())

        for response in responses:
            if response.recognition_result:
                print("\r recognition_result:", response.recognition_result.transcript, end="")
                self._redis.send_message(self._output_channel, RecognitionResult(response))
            if response.query_result:
                print("query_result:", response.query_result)
                return QueryResult(response)
            if response.recognition_result.is_final:
                print("----- FINAL -----")
                # Stop sending audio to dialogflow as it detected the person stopped speaking, but continue this loop
                # to receive the query result
                self.message_was_final.set()

        return QueryResult(dict())


class Dialogflow(SICConnector):
    component_class = DialogflowService


if __name__ == '__main__':
    SICComponentManager([DialogflowService])
