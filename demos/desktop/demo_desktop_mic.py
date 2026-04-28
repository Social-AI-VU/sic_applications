import time
import wave
from datetime import datetime

import pyaudio

from sic_framework.core.sic_application import SICApplication
from sic_framework.devices.common_desktop.desktop_microphone import MicrophoneConf


class DesktopMicRecordingDemo(SICApplication):
    def __init__(self):
        super(DesktopMicRecordingDemo, self).__init__()
        self.record_seconds = 5
        self.mic_conf = MicrophoneConf(sample_rate=44100)
        self.output_path = "desktop_mic_{stamp}.wav".format(
            stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        self.audio_chunks = bytearray()
        self.pa = None
        self.stream = None

        self.setup()

    def setup(self):
        self.pa = pyaudio.PyAudio()
        device_index = self.mic_conf.device_index
        if device_index is None:
            device_index = self.pa.get_default_input_device_info()["index"]

        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=self.mic_conf.channels,
            rate=self.mic_conf.sample_rate,
            input=True,
            output=False,
            input_device_index=device_index,
            frames_per_buffer=int(self.mic_conf.sample_rate // 4),
        )
        self.logger.info(
            "Using input device index {} at {} Hz".format(
                device_index, self.mic_conf.sample_rate
            )
        )

    def run(self):
        try:
            self.logger.info("Recording for {} seconds...".format(self.record_seconds))
            end_time = time.time() + self.record_seconds
            chunk_frames = int(self.mic_conf.sample_rate // 4)
            while time.time() < end_time:
                chunk = self.stream.read(chunk_frames, exception_on_overflow=False)
                self.audio_chunks.extend(chunk)
            self.logger.info("Finished recording, saving to {} ...".format(self.output_path))

            with wave.open(self.output_path, "wb") as wav_file:
                wav_file.setnchannels(self.mic_conf.channels)
                wav_file.setsampwidth(2)  # 16-bit PCM
                wav_file.setframerate(self.mic_conf.sample_rate)
                wav_file.writeframes(bytes(self.audio_chunks))

            self.logger.info("Saved {}".format(self.output_path))
        finally:
            self.shutdown()

    def shutdown(self):
        if self.stream is not None:
            try:
                self.stream.close()
            except Exception:
                pass

        if self.pa is not None:
            try:
                self.pa.terminate()
            except Exception:
                pass

        super(DesktopMicRecordingDemo, self).shutdown()

if __name__ == "__main__":
    demo = DesktopMicRecordingDemo()
    demo.run()
