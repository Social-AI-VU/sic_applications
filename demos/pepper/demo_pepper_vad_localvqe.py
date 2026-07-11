# Import basic SIC framework modules
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s), service(s), and message(s) we will be using
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.devices import Pepper
from sic_framework.services.localvqe.localvqe_messages import (
    LocalVQEConf,
    RefAudioMessage,
)
from sic_framework.services.localvqe.localvqe_service import SICLocalVQE
from sic_framework.services.voice_detection.voice_detection import (
    VoiceDetection,
    VoiceDetectionConf,
    VoiceDetectionMessage,
)

# Import demo-specific modules
from os.path import abspath, dirname, join
import threading
import time
import wave

import numpy as np


class PepperVADLocalVQEDemo(SICApplication):
    """
    VAD-gated far-end playback through LocalVQE echo cancellation on Pepper.
    demo_audio.wav loops on the robot's speaker while the robot mic +
    reference feed LocalVQE; voice detection runs on the echo-cancelled
    output, so only near-end speech pauses the clip and silence resumes it.
    Runs until Ctrl+C.

    IMPORTANT:
    LocalVQE and VoiceDetection services need to be running:
    1. pip install --upgrade "social-interaction-cloud[localvqe]"
       and "social-interaction-cloud[voice-detection]" (quote the extras -
       zsh; the native build and model download need no extra steps)
    2. run-localvqe
    3. run-voice-detection

    NOTE: Make sure to set the correct Pepper robot IP address in the
    __init__ method. The clip is the echo LocalVQE cancels, which is why
    playback never pauses itself; only your voice does.
    """

    def __init__(self):
        super(PepperVADLocalVQEDemo, self).__init__()

        self.pepper_ip = "XXX"  # Replace with your Pepper robot's IP address
        app_root = dirname(dirname(dirname(__file__)))
        self.audio_file = abspath(
            join(app_root, "example_media", "audio", "demo_audio.wav")
        )
        self.sample_rate = 16000
        self.chunk_samples = 4000  # 250 ms chunks
        self.pepper = None
        self.localvqe = None
        self.voice_detection = None
        self.far_end = None
        self.paused = threading.Event()

        self.set_log_level(sic_logging.INFO)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file_path("/path/to/log/directory")

        self.load_env("../../conf/.env")

        self.setup()

    def on_voice_detection(self, message: VoiceDetectionMessage):
        """Speech on the enhanced audio pauses the far-end; silence resumes it."""
        if message.is_speaking and not self.paused.is_set():
            self.paused.set()
            self.logger.info(
                "Speech detected (proportion {:.2f}) - pausing far-end playback".format(
                    message.speech_proportion
                )
            )
        elif not message.is_speaking and self.paused.is_set():
            self.paused.clear()
            self.logger.info("Silence - resuming far-end playback")

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
        """Initialize the Pepper robot, the LocalVQE service, and VAD on its output."""
        self.logger.info(
            "Setting up LocalVQE echo cancellation with VAD gating on Pepper..."
        )

        self.far_end = self.load_far_end()

        self.pepper = Pepper(ip=self.pepper_ip)

        self.localvqe = SICLocalVQE(
            input_source=self.pepper.mic, conf=LocalVQEConf(use_ref=True)
        )

        # VAD listens to the enhanced output, not the raw mic (which hears the
        # clip itself); resume only after 0.8 s of silence to avoid stutter.
        self.voice_detection = VoiceDetection(
            input_source=self.localvqe,
            conf=VoiceDetectionConf(min_silence_duration_ms=800),
        )

        self.voice_detection.register_callback(self.on_voice_detection)

    def stream_far_end(self):
        """
        Loop the clip in paced chunks to the robot speaker and, identically, to
        the reference. While paused the reference carries the silence the
        speaker plays (both streams must keep flowing); the position is held.
        """
        chunk_bytes = self.chunk_samples * 2
        chunk_seconds = self.chunk_samples / float(self.sample_rate)
        silence = b"\x00" * chunk_bytes
        pos = 0
        next_deadline = time.time()
        while not self.shutdown_event.is_set():
            if self.paused.is_set():
                self.localvqe.send_message(
                    RefAudioMessage(silence, self.sample_rate, is_stream=True)
                )
            else:
                end = pos + chunk_bytes
                chunk = self.far_end[pos:end]
                if end >= len(self.far_end):  # loop the clip at end-of-file
                    chunk += self.far_end[: end - len(self.far_end)]
                    pos = end - len(self.far_end)
                else:
                    pos = end
                self.pepper.speaker.request(
                    AudioRequest(
                        self.to_stereo(chunk), self.sample_rate, is_stream=True
                    )
                )
                self.localvqe.send_message(
                    RefAudioMessage(chunk, self.sample_rate, is_stream=True)
                )
            next_deadline += chunk_seconds
            delay = next_deadline - time.time()
            if delay > 0:
                time.sleep(delay)
            elif delay < -1.0:  # after a long stall, re-anchor instead of bursting
                next_deadline = time.time()

    def run(self):
        """Main application loop."""
        self.logger.info("Starting Pepper VAD-gated LocalVQE Demo")
        self.logger.info("The clip loops on the robot; speak to pause it.")
        self.logger.info("Press Ctrl+C to stop.")

        try:
            worker = threading.Thread(target=self.stream_far_end, daemon=True)
            worker.start()
            while not self.shutdown_event.is_set():
                time.sleep(0.1)  # Keep the main thread alive
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = PepperVADLocalVQEDemo()
    demo.run()
