import pyaudio

from sic_framework import SICActuator, SICComponentManager
from sic_framework.core.connector import SICConnector
from sic_framework.core.message import SICMessage
from sic_framework.core.message_python2 import SICConfMessage, AudioMessage, TextRequest, TextMessage

"""
Linux installation instructions:
sudo apt-get install espeak libespeak-dev
pip install python-espeak
"""



class TextToSpeechConf(SICConfMessage):
    """
    Parameters for espeak go here.
    """
    def __init__(self, capitals= 0, pitch= 50, punctuation= "none", range= 50, rate= 175, volume= 100, wordgap= 0):
        self.capitals = capitals
        self.pitch = pitch
        self.punctuation = punctuation
        self.range = range
        self.rate = rate
        self.volume = volume
        self.wordgap = wordgap



class DesktopTextToSpeechActuator(SICActuator):

    def __init__(self, *args, **kwargs):
        super(DesktopTextToSpeechActuator, self).__init__(*args, **kwargs)

        import espeak
        espeak.init()
        self.speaker = espeak.Espeak()


        # Set configuration
        self.speaker.capitals = self.params.capitals
        self.speaker.pitch = self.params.pitch
        self.speaker.punctuation = self.params.punctuation
        self.speaker.range = self.params.range
        self.speaker.rate = self.params.rate
        self.speaker.volume = self.params.volume
        self.speaker.wordgap = self.params.wordgap





    @staticmethod
    def get_conf():
        return TextToSpeechConf()

    @staticmethod
    def get_inputs():
        return [TextMessage, TextRequest]

    @staticmethod
    def get_output():
        return SICMessage

    def on_request(self, request):
        print("Saying: " + request.text)
        self.speaker.say(request.text)
        return SICMessage()

    def on_message(self, message):
        self.speaker.say(message.text)



class DesktopTextToSpeech(SICConnector):
    component_class = DesktopTextToSpeechActuator


if __name__ == '__main__':
    SICComponentManager([DesktopTextToSpeechActuator])
