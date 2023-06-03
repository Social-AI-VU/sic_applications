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
    def __init__(self, text, language=None, animated=False):
        """
        Request the nao to say something
        :param text: object
        :param language: "English" or "Dutch" or see http://doc.aldebaran.com/2-8/family/nao_technical/languages_naov6.html#language-codes-naov6
        :param animated: Use animated text to speech, e.g. perform some gestures while talking
        """
        super(NaoqiTextToSpeechRequest, self).__init__()
        self.text = text
        self.language = language
        self.animated = animated


# @dataclass
class NaoqiTextToSpeechConf(SICConfMessage):
    def __init__(self, language="English", volume=None, speed=None, pitch=None, pitch_shift=None, ):
        """
        Set the parameters for the text to speech engine. If None, the default NAOqi values are used.
        :param language: see http://doc.aldebaran.com/2-8/family/nao_technical/languages_naov6.html#language-codes-naov6
        :param volume: Sets the current gain applied to the signal synthesized by the text to speech engine if not None.
        :type volume: float
        :param pitch: Applies a pitch shift to the voice. Range is [1.0 - 4.0]. 0 disables the effect.
        :type pitch: int [50 - 100]
        :param pitch_shift: Applies a pitch shift to the voice. Range is [1.0 - 4.0]. 0 disables the effect.
        :type pitch_shift: float
        :param speed: sets the current voice speed. The default value is 100.
        :type speed: int [50 - 400]
        """
        SICConfMessage.__init__(self)

        self.pitch = pitch
        self.speed = speed
        self.pitch_shift = pitch_shift
        self.volume = volume
        self.language = language


class NaoqiTextToSpeechActuator(SICActuator):
    def __init__(self, *args, **kwargs):
        super(NaoqiTextToSpeechActuator, self).__init__(*args, **kwargs)

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        self.tts = self.session.service('ALTextToSpeech')
        self.atts = self.session.service('ALAnimatedSpeech')

        if self.params.volume is not None:
            self.tts.setVolume(self.params.volume)

        if self.params.speed is not None:
            self.tts.setParameter(self.params.speed)

        if self.params.pitch is not None:
            self.tts.setParameter(self.params.pitch)

        if self.params.pitch_shift is not None:
            self.tts.setParameter(self.params.pitch_shift)



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
        if message.animated:
            self.atts.say(message.text, message.language)
        else:
            self.tts.say(message.text)
        return SICMessage()


class NaoqiTextToSpeech(SICConnector):
    component_class = NaoqiTextToSpeechActuator


if __name__ == '__main__':
    SICComponentManager([NaoqiTextToSpeechActuator])
