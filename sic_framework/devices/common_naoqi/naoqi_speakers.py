import argparse

from sic_framework import utils
from sic_framework.core.actuator_python2 import SICActuator
from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import SICRequest, SICConfMessage, SICMessage

if utils.PYTHON_VERSION_IS_2:
    import qi

# @dataclass
class NaoqiTextToSpeechRequest(SICRequest):
    def __init__(self, text):
        super(NaoqiTextToSpeechRequest, self).__init__()
        self.text = text


# @dataclass
class NaoqiTextToSpeechConf(SICConfMessage):
    def __init__(self, lang=None, pitch_shift=None):
        """ params can be found at http://doc.aldebaran.com/2-8/naoqi/audio/altexttospeech-api.html#ALTextToSpeechProxy::setParameter__ssCR.floatCR
        """
        SICConfMessage.__init__(self)
        self.lang = lang
        self.pitch_shift = pitch_shift
        # TODO: see if we need to add the rest of the speech params


class NaoqiTextToSpeechActuator(SICActuator):
    def __init__(self, *args, **kwargs):
        super(NaoqiTextToSpeechActuator, self).__init__(*args, **kwargs)

        self.session = qi.Session()
        self.session.connect('tcp://{}:{}'.format('127.0.0.1', 9559))

        self.tts = self.session.service('ALTextToSpeech')
        self.atts = self.session.service('ALAnimatedSpeech')
        self.language = self.session.service('ALDialog')
        self.audio_player = self.session.service('ALAudioPlayer')

    @staticmethod
    def get_conf():
        return NaoqiTextToSpeechConf()

    @staticmethod
    def get_inputs():
        return [NaoqiTextToSpeechRequest]

    @staticmethod
    def get_output():
        return SICMessage

    def execute(self, message):
        self.tts.say(message.text)

        return SICMessage()


class NaoqiTextToSpeech(SICConnector):
    component_class = NaoqiTextToSpeechActuator


if __name__ == '__main__':
    SICComponentManager([NaoqiTextToSpeechActuator])
