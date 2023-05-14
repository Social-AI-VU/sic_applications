from sic_framework.core.actuator_python2 import SICActuator
from sic_framework.core.message_python2 import SICConfMessage, SICMessage, SICRequest, SICStopRequest, AudioMessage
from sic_framework import SICComponentManager
from google.cloud import texttospeech as tts
from google.oauth2.service_account import Credentials

import io
import wave


class Text2SpeechConf(SICConfMessage):
    def __init__(self, keyfile: str, language_code: str = 'en-US', ssml_gender: int = tts.SsmlVoiceGender.NEUTRAL, voice_name: str = ''):
        """
        Configuration message for Text2Speech SICAction.
        Options for language_code, voice_name, and ssml_gender can be found at https://cloud.google.com/text-to-speech/docs/voices
        :param keyfile: Path to a google service account json key file, which has access to your dialogflow agent.
        :param language_code: code to determine the language, as per Google's docs
        :param ssml_gender: code to determine the voice's gender, per Google's docs
        :param voice_name: string that corresponds to one of Google's voice options
        """
        super(Text2SpeechConf, self).__init__()

        self.keyfile = keyfile
        self.language_code = language_code
        self.ssml_gender = ssml_gender
        self.voice_name = voice_name


class GetSpeechRequest(SICRequest):
    """
    SICRequest to send to Text2Speech SICAction.
    The request embeds the text to synthesize and optionally Google voice parameters.
    """
    def __init__(self, text: str, language_code=None, voice_name=None, ssml_gender=None):
        """
        :param text: the text to synthesize
        :param language_code: see Text2SpeechConf
        :param voice_name: see Text2SpeechConf
        :param ssml_gender: see Text2SpeechConf
        """
        super(GetSpeechRequest, self).__init__()

        self.text = text
        self.language_code = language_code
        self.voice_name = voice_name
        self.ssml_gender = ssml_gender


class SpeechResult(AudioMessage):
    """
    The SICMessage that will be returned by the Text2Speech SICAction.
    This message contains the synthesized audio using AudioMessage's format.
    """
    def __init__(self, wav_audio):
        """
        :param wav_audio: synthesized audio
        """
        self.wav_audio = wav_audio

        # Convert the audio
        audio = wave.open(io.BytesIO(wav_audio))
        sample_rate = audio.getframerate()
        audio_bytes = audio.readframes(audio.getnframes())

        super(SpeechResult, self).__init__(waveform=audio_bytes, sample_rate=sample_rate)




class Text2Speech(SICActuator):
    """
    SIC implementation of the Google Text-to-Speech API (https://cloud.google.com/text-to-speech/).
    This SICAction responds to GetSpeechRequest requests and returns a SpeechResult.
    The parameters can be set using Text2SpeechConf.
    """
    def __init__(self, *args, **kwargs):
        super(Text2Speech, self).__init__(*args, **kwargs)

        # Instantiates a client
        credentials = Credentials.from_service_account_file(self.params.keyfile)
        self.client = tts.TextToSpeechClient(credentials=credentials)

        # Select the type of audio file you want returned
        self.audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)

    @staticmethod
    def get_inputs():
        return [GetSpeechRequest]

    @staticmethod
    def get_output():
        return SpeechResult

    @staticmethod
    def get_conf():
        return Text2SpeechConf()

    def execute(self, request):
        """
        Main function of the SICAction. Builds the voice request, calls Google's API and returns audio in MP3 format.
        NOTE: if the GetSpeechRequest does not set a voice parameters, the SICAction's default parameters will be used.
        :param request: GetSpeechRequest, the request with the text to synthesize and optionally voice paramters
        :return: SpeechResult, the response with the synthesized text as audio (MP3 format)
        """
        # Set the text input to be synthesized
        synthesis_input = tts.SynthesisInput(text=request.text)

        # Build the voice request based on request parameters, fall back on service config parameters
        lang_code = request.language_code if request.language_code else self.params.language_code
        voice_name = request.voice_name if request.voice_name else self.params.voice_name
        ssml_gender = request.ssml_gender if request.ssml_gender else self.params.ssml_gender

        voice = tts.VoiceSelectionParams(language_code=lang_code, name=voice_name, ssml_gender=ssml_gender)

        # Perform the text-to-speech request
        response = self.client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=self.audio_config)

        return SpeechResult(wav_audio=response.audio_content)


if __name__ == '__main__':
    # Request the service to start using the SICServiceManager on this device (id: local)
    SICComponentManager([Text2Speech], "local")
