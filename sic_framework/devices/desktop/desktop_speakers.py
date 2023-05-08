import io

import pyaudio

from sic_framework import SICActuator
from sic_framework.core.message_python2 import SICConfMessage, AudioMessage


class SpeakersConf(SICConfMessage):
    """
    Parameters for speakers go here.
    """
    def __init__(self):
        self.sample_rate = 44100
        self.channels = 1


class DesktopSpeakers(SICActuator):

    def __init__(self, *args, **kwargs):
        super(DesktopSpeakers, self).__init__(*args, **kwargs)

        self.device = pyaudio.PyAudio()

        # open stream using callback (3)
        self.stream = self.device.open(format=pyaudio.paInt16,
                                       channels=self.params.channels,
                                       rate=self.params.sample_rate,
                                       input=False,
                                       output=True)

    @staticmethod
    def get_conf():
        return SpeakersConf()

    @staticmethod
    def get_inputs():
        return [AudioMessage]

    @staticmethod
    def get_output():
        return None

    def on_request(self, request):
        self.stream.write(request.waveform)

    def on_message(self, message):
        self.stream.write(message.waveform)

    def stop(self, *args):
        super(DesktopSpeakers, self).stop(*args)
        self.logger.info("Stopped speakers")

        self.stream.close()
        self.device.terminate()
