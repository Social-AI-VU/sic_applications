import pyaudio

from sic_framework import SICComponentManager
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import AudioMessage, SICConfMessage
from sic_framework.core.sensor_python2 import SICSensor


class MicrophoneConf(SICConfMessage):
    def __init__(self):
        self.no_channels = 1
        self.sample_rate = 44100


class DesktopMicrophoneSensor(SICSensor):
    def __init__(self, *args, **kwargs):
        super(DesktopMicrophoneSensor, self).__init__(*args, **kwargs)

        self.audio_buffer = None

        self.device = pyaudio.PyAudio()

        # open stream using callback (3)
        self.stream = self.device.open(format=pyaudio.paInt16,
                                       channels=1,
                                       rate=self.params.sample_rate,
                                       input=True,
                                       output=False)


    @staticmethod
    def get_conf():
        return MicrophoneConf()

    @staticmethod
    def get_inputs():
        return []

    @staticmethod
    def get_output():
        return AudioMessage

    def execute(self):
        self.logger.debug("Reading audio")
        # read 250ms chunks
        data = self.stream.read(int(self.params.sample_rate // 4))
        return AudioMessage(data, sample_rate=self.params.sample_rate)

    def stop(self, *args):
        super(DesktopMicrophoneSensor, self).stop(*args)
        self.logger.info("Stopped microphone")
        self.stream.close()


class DesktopMicrophone(SICConnector):
    component_class = DesktopMicrophoneSensor


if __name__ == '__main__':
    SICComponentManager([DesktopMicrophoneSensor])
