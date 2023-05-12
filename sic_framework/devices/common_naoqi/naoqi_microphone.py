import threading
from sic_framework import SICComponentManager, utils
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import AudioMessage, SICConfMessage
from sic_framework.core.sensor_python2 import SICSensor

if utils.PYTHON_VERSION_IS_2:
    from naoqi import ALProxy
    import qi


class NaoqiMicrophoneConf(SICConfMessage):
    def __init__(self):
        self.channel_index = 3  # front microphone
        self.no_channels = 1
        self.sample_rate = 16000
        self.index = -1


class NaoqiMicrophoneSensor(SICSensor):
    def __init__(self, *args, **kwargs):
        super(NaoqiMicrophoneSensor, self).__init__(*args, **kwargs)

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        self.audio_service = self.session.service('ALAudioDevice')

        self.module_name = "SICMicrophoneService"

        try:
            self.session_id = self.session.registerService(self.module_name, self)
        except RuntimeError:
            # possbile solution: do not catch runtime error, the registering is already done so
            # the self.audio_service.subscribe(self.module_name) should work
            raise RuntimeError(
                "Naoqi error, restart robot. Cannot re-register ALAudioDevice service, this service is a singleton. ")

        self.audio_service.setClientPreferences(self.module_name, self.params.sample_rate,
                                                self.params.channel_index, 0)
        self.audio_service.subscribe(self.module_name)

        self.new_sound_data_available = threading.Event()

    @staticmethod
    def get_conf():
        return NaoqiMicrophoneConf()

    @staticmethod
    def get_inputs():
        return []

    @staticmethod
    def get_output():
        return AudioMessage

    def execute(self):

        self.new_sound_data_available.wait()
        self.new_sound_data_available.clear()

        return AudioMessage(self.audio_buffer, sample_rate=self.params.sample_rate)

    def stop(self, *args):
        self.audio_service.unsubscribe(self.module_name)
        self.session.unregisterService(self.session_id)
        self.session.close()
        super(NaoqiMicrophoneSensor, self).stop(*args)

    def processRemote(self, nbOfChannels, nbOfSamplesByChannel, timeStamp, inputBuffer):
        """
        This function is registered by the self.session.registerService(self) call.
        :param nbOfChannels:
        :param nbOfSamplesByChannel:
        :param timeStamp:
        :param inputBuffer:
        """
        self.audio_buffer = inputBuffer
        self.naoqi_timestamp = timeStamp
        self.new_sound_data_available.set()


class NaoqiMicrophone(SICConnector):
    component_class = NaoqiMicrophoneSensor


if __name__ == '__main__':
    SICComponentManager([NaoqiMicrophoneSensor])
