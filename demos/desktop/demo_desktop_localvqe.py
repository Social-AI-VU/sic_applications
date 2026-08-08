# Import basic SIC framework modules
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s), service(s), and message(s) we will be using
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.devices.common_desktop.desktop_microphone import MicrophoneConf
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.devices.desktop import Desktop
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


class DesktopLocalVQEDemo(SICApplication):
    """
    LocalVQE acoustic echo cancellation demo.
    Plays demo_audio.wav on the speakers (the far-end) while you talk; the
    clip doubles as LocalVQE's reference, the speaker echo is cancelled, and
    the enhanced near-end audio is written to enhanced_localvqe.wav.

    IMPORTANT:
    LocalVQE service needs to be running:
    1. pip install --upgrade "social-interaction-cloud[localvqe]"
        Note: quote the extra (zsh). The native build runs during the
        install; the default model downloads on first service start.
    2. run-localvqe

    NOTE: open speakers are required - they produce the echo being cancelled.
    The enhanced signal goes to a file, not the speakers: no feedback loop.
    """

    def __init__(self):
        super(DesktopLocalVQEDemo, self).__init__()

        app_root = dirname(dirname(dirname(__file__)))
        self.audio_file = abspath(
            join(app_root, "example_media", "audio", "demo_audio.wav")
        )
        self.output_file = abspath(join(dirname(__file__), "enhanced_localvqe.wav"))
        self.sample_rate = 16000
        self.chunk_samples = 4000  # 250 ms reference chunks, the mic's cadence
        self.desktop = None
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

    def setup(self):
        """Initialize the desktop mic/speakers and the LocalVQE service."""
        self.logger.info("Setting up LocalVQE echo cancellation...")

        self.far_end = self.load_far_end()

        self.desktop = Desktop(
            mic_conf=MicrophoneConf(sample_rate=self.sample_rate),
            speakers_conf=SpeakersConf(sample_rate=self.sample_rate),
        )

        self.localvqe = SICLocalVQE(
            input_source=self.desktop.mic, conf=LocalVQEConf(use_ref=True)
        )

        self.localvqe.register_callback(self.on_enhanced)

    def run(self):
        """Main application loop."""
        self.logger.info("Starting LocalVQE AEC Demo")

        try:
            duration = len(self.far_end) / 2.0 / self.sample_rate
            self.logger.info(
                "Playing {:.1f}s of far-end audio on the speakers - talk over it!".format(
                    duration
                )
            )
            # block=False: pace the reference alongside the playback
            self.desktop.speakers.request(
                AudioRequest(waveform=self.far_end, sample_rate=self.sample_rate),
                block=False,
            )

            # publish the clip as the reference at its real-time rate
            chunk_bytes = self.chunk_samples * 2
            chunk_seconds = self.chunk_samples / float(self.sample_rate)
            start = time.time()
            for i, offset in enumerate(range(0, len(self.far_end), chunk_bytes)):
                self.localvqe.send_message(
                    RefAudioMessage(
                        self.far_end[offset:offset + chunk_bytes],
                        self.sample_rate,
                        is_stream=True,
                    )
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
    demo = DesktopLocalVQEDemo()
    demo.run()
