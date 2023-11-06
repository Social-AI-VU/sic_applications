import io
import threading
import wave
import socket

from sic_framework import SICComponentManager, utils, SICActuator
from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import AudioMessage, SICConfMessage, SICMessage
from sic_framework.core.sensor_python2 import SICSensor

import numpy as np

if utils.PYTHON_VERSION_IS_2:
    from naoqi import ALProxy
    import qi


class NaoqiSpeakersConf(SICConfMessage):
    def __init__(self):
        self.no_channels = 1
        self.sample_rate = 16000
        self.index = -1


class NaoqiSpeakerComponent(SICComponent):
    def __init__(self, *args, **kwargs):
        super(NaoqiSpeakerComponent, self).__init__(*args, **kwargs)

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        self.audio_service = self.session.service('ALAudioDevice')
        self.audio_player_service = self.session.service('ALAudioPlayer')

        # self.module_name = "SICSpeakersService"
        #
        # try:
        #     self.session_id = self.session.registerService(self.module_name, self)
        # except RuntimeError:
        #     # possbile solution: do not catch runtime error, the registering is already done so
        #     # the self.audio_service.subscribe(self.module_name) should work
        #     raise RuntimeError(
        #         "Naoqi error, restart robot. Cannot re-register ALAudioDevice service, this service is a singleton. ")
        #
        # self.audio_service.setClientPreferences(self.module_name, self.params.sample_rate,
        #                                         3, 0)
        # self.audio_service.subscribe(self.module_name)

        # host = "127.0.0.1"
        # port = 8123
        #
        # self.wavstream = "http://" + str(host) + ":" + str(port) + "/wavstream"
        #
        #
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # # now connect to the web server on port 80
        # # - the normal http port
        # s.connect(("www.mcmillan-inc.com", 80))
        #
        # self.wavstream =
        # self.audio_player_service.playWebStream(wavstream, 1, 0)

        self.i = 0

    @staticmethod
    def get_conf():
        return NaoqiSpeakersConf()

    @staticmethod
    def get_inputs():
        return []

    @staticmethod
    def get_output():
        return SICMessage

    def on_message(self, message):
        self.play_sound(message)

    def on_request(self, request):
        self.play_sound(request)
        return SICMessage()

    def play_sound(self, message):
        # sound = bytearray(message.waveform)
        # frame_count = len(sound) // 2
        #
        # self.audio_service.muteAudioOut(False)
        # self.audio_service.setOutputVolume(50)
        #
        # self.logger.warn("Playing sound with length: {}".format(len(sound)))
        #
        # # broken
        # self.audio_service.sendLocalBufferToOutput(frame_count, id(sound))
        #
        # # broken
        # self.audio_service.sendRemoteBufferToOutput(frame_count, id(sound))
        #
        # # broken
        # self.audio_service.playSine(200, 1, 0, 1)
        #
        # self.audio_service.flushAudioOutputs()  # according to doc:  close the audio device for capture
        bytestream = message.waveform
        frame_rate = message.sample_rate

        # self.logger.warn(bytestream)

        # Set the parameters for the WAV file
        channels = 1  # 1 for mono audio
        sample_width = 2  # 2 bytes for 16-bit audio
        num_frames = len(bytestream) // (channels * sample_width)

        # Create a WAV file in memory
        tmp_file = "/tmp/tmp{}.wav".format(self.i)

        wav_file = wave.open(tmp_file, 'wb')
        self.i += 1
        wav_file.setparams((channels, sample_width, frame_rate, num_frames, 'NONE', 'not compressed'))
        # Write the bytestream to the WAV file
        wav_file.writeframes(bytestream)
        # Launchs the playing of a file
        self.audio_player_service.playFile(tmp_file)


class NaoqiSpeaker(SICConnector):
    component_class = NaoqiSpeakerComponent


if __name__ == '__main__':
    SICComponentManager([NaoqiSpeakerComponent])
