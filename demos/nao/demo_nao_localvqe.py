# Import basic SIC framework modules
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s), service(s), and message(s) we will be using
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.devices import Nao
from sic_framework.services.localvqe.localvqe_messages import (
    LocalVQEConf,
    RefAudioMessage,
)
from sic_framework.services.localvqe.localvqe_service import SICLocalVQE

# Import demo-specific modules
from os.path import abspath, dirname, join
import time
import wave

import numpy as np


class NaoLocalVQEDemo(SICApplication):
    """
    LocalVQE acoustic echo cancellation demo on NAO.
    Plays demo_audio.wav on the robot's speaker (the far-end) while you talk
    to the robot; the clip doubles as LocalVQE's reference, the speaker echo
    is cancelled from the robot mic, and the enhanced near-end audio is
    written to enhanced_localvqe.wav next to this script.

    IMPORTANT:
    LocalVQE service needs to be running:
    1. pip install --upgrade "social-interaction-cloud[localvqe]"
        Note: quote the extra (zsh). The native build runs during the
        install; the default model downloads on first service start.
    2. run-localvqe

    NOTE: Make sure to set the correct NAO robot IP address in the __init__
    method. The NAO mic streams 16 kHz mono, which is what LocalVQE needs.
    """

    def __init__(self):
        super(NaoLocalVQEDemo, self).__init__()

        self.nao_ip = "XXX"  # Replace with your NAO robot's IP address
        app_root = dirname(dirname(dirname(__file__)))
        self.audio_file = abspath(
            join(app_root, "example_media", "audio", "demo_audio.wav")
        )
        self.output_file = abspath(join(dirname(__file__), "enhanced_localvqe.wav"))
        self.sample_rate = 16000
        self.chunk_samples = 4000  # 250 ms chunks
        self.nao = None
        self.localvqe = None
        self.far_end = None
        self.enhanced = bytearray()

        self.set_log_level(sic_logging.INFO)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file_path("/path/to/log/directory")

        self.load_env("../../conf/.env")

        self.setup()

    def on_enhanced(self, message):
        self.enhanced.extend(message.waveform)

    def load_far_end(self):
        """Load demo_audio.wav as 16 kHz mono int16 bytes, resampling if needed."""
        with wave.open(self.audio_file, "rb") as w:
            assert w.getsampwidth() == 2, "demo_audio.wav must be 16-bit PCM"
            rate = w.getframerate()
            samples = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
            if w.getnchannels() > 1:
                samples = samples.reshape(-1, w.getnchannels()).mean(axis=1)
        if rate != self.sample_rate:
            self.logger.info(
                "Resampling far-end audio from {} Hz to {} Hz".format(
                    rate, self.sample_rate
                )
            )
            n_out = int(len(samples) * self.sample_rate / rate)
            positions = np.linspace(0, len(samples) - 1, n_out)
            samples = np.interp(positions, np.arange(len(samples)), samples)
        return np.round(samples).astype("<i2").tobytes()

    def to_stereo(self, mono_bytes):
        # The Naoqi speaker streaming path plays interleaved stereo frames.
        return np.repeat(np.frombuffer(mono_bytes, dtype="<i2"), 2).tobytes()

    def setup(self):
        """Initialize the NAO robot and the LocalVQE service."""
        self.logger.info("Setting up LocalVQE echo cancellation on NAO...")

        self.far_end = self.load_far_end()

        self.nao = Nao(ip=self.nao_ip)

        self.localvqe = SICLocalVQE(
            input_source=self.nao.mic, conf=LocalVQEConf(use_ref=True)
        )

        self.localvqe.register_callback(self.on_enhanced)

    def run(self):
        """Main application loop."""
        self.logger.info("Starting NAO LocalVQE AEC Demo")

        try:
            duration = len(self.far_end) / 2.0 / self.sample_rate
            self.logger.info(
                "Playing {:.1f}s of far-end audio on the robot - talk to it!".format(
                    duration
                )
            )
            # chunked streaming requests keep playback app-paced, so the
            # reference tracks exactly what the speaker plays
            chunk_bytes = self.chunk_samples * 2
            chunk_seconds = self.chunk_samples / float(self.sample_rate)
            start = time.time()
            for i, offset in enumerate(range(0, len(self.far_end), chunk_bytes)):
                chunk = self.far_end[offset:offset + chunk_bytes]
                self.nao.speaker.request(
                    AudioRequest(
                        self.to_stereo(chunk), self.sample_rate, is_stream=True
                    )
                )
                self.localvqe.send_message(
                    RefAudioMessage(chunk, self.sample_rate, is_stream=True)
                )
                delay = start + (i + 1) * chunk_seconds - time.time()
                if delay > 0:
                    time.sleep(delay)

            time.sleep(1.0)  # let the last hops come back

            with wave.open(self.output_file, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(self.sample_rate)
                w.writeframes(bytes(self.enhanced))
            self.logger.info(
                "Wrote {:.1f}s of enhanced near-end audio to {}".format(
                    len(self.enhanced) / 2.0 / self.sample_rate, self.output_file
                )
            )
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = NaoLocalVQEDemo()
    demo.run()
