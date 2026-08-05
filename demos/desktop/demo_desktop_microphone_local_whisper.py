"""
Real-time local Whisper speech-to-text demo.

Three latency levers, from highest to lowest impact:
  1. model_size  — "base" transcribes a 3-second phrase in ~0.3-0.8 s on CPU.
                   "small" is more accurate but 2-3x slower. "large-v3-turbo" is
                   the default service model but far too slow for real-time CPU use.
  2. beam_size=1 — greedy decoding, ~20-30 % faster than beam_size=5 with minimal
                   accuracy loss for short conversational phrases.
  3. pause_threshold — seconds of silence that close a phrase. 0.5 s cuts
                   end-of-speech detection latency almost in half vs. the 0.8 s
                   default, with only a small risk of cutting off slow speakers.

Architecture: a background thread runs the blocking GetTranscript request loop
(VAD → transcribe → return), and the main thread prints results the moment they
arrive.  This keeps the UI responsive and avoids the impression of a frozen
terminal while Whisper is working.

IMPORTANT — before running this demo:
  1. (Windows) pip install --upgrade "social-interaction-cloud[local-whisper-stt]"
  (Mac) pip install --upgrade "social-interaction-cloud[local-whisper-stt-mac]"
  2. run-local-whisper          (keep this running in a separate terminal)

The first run with a new model_size will download the model weights (~150 MB for
"base"). Subsequent runs load from cache and start in a few seconds.
"""

import queue
import threading

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.devices.desktop import Desktop
from sic_framework.services.local_whisper_stt import (
    GetTranscript,
    LocalWhisper,
    LocalWhisperConf,
)

# ── Tune these for your hardware ──────────────────────────────────────────────
MODEL_SIZE = "base"  # "tiny" < "base" < "small" < "medium" < "large-v3-turbo"
BEAM_SIZE = 1  # 1 = greedy (fastest); 5 = default (most accurate)
PAUSE_THRESHOLD = 0.8  # seconds of silence to close a phrase (default 0.8)
# Lower = less end-latency but risks cutting mid-sentence pauses.
LANGUAGE = "en"  # set to None for auto-detect (slightly slower)
SPEECH_TIMEOUT = 3  # seconds to wait for speech to start before retrying
PHRASE_TIME_LIMIT = 15  # max seconds per phrase
# ──────────────────────────────────────────────────────────────────────────────


class RealTimeWhisperDemo(SICApplication):
    def __init__(self):
        super().__init__()
        # Suppress framework INFO chatter so transcripts are easy to read.
        self.set_log_level(sic_logging.WARNING)
        self.load_env("../../conf/.env")
        self._result_queue = queue.Queue()
        self._setup()

    def _setup(self):
        self.desktop = Desktop()

        conf = LocalWhisperConf(
            language=LANGUAGE,
            model_size=MODEL_SIZE,
            beam_size=BEAM_SIZE,
            pause_threshold=PAUSE_THRESHOLD,
        )
        self.whisper = LocalWhisper(input_source=self.desktop.mic, conf=conf)

    def _transcription_loop(self):
        """
        Runs in a background thread.  Continuously sends GetTranscript requests;
        non-empty transcripts are pushed onto the result queue for the main thread
        to display.  A short speech_timeout keeps the loop snappy when nobody is
        speaking — it simply retries immediately instead of blocking for 10+ seconds.
        """
        while not self.shutdown_event.is_set():
            try:
                result = self.whisper.request(
                    GetTranscript(
                        timeout=SPEECH_TIMEOUT,
                        phrase_time_limit=PHRASE_TIME_LIMIT,
                    ),
                    timeout=SPEECH_TIMEOUT + PHRASE_TIME_LIMIT + 10,
                )
                text = result.transcript.strip() if result else ""
                if text:
                    self._result_queue.put(text)
            except Exception:
                # WaitTimeoutError (no speech) or transient errors — just retry.
                pass

    def run(self):
        worker = threading.Thread(target=self._transcription_loop, daemon=True)
        worker.start()

        print(
            "Model: {}  |  beam_size: {}  |  pause: {}s".format(
                MODEL_SIZE, BEAM_SIZE, PAUSE_THRESHOLD
            )
        )
        print("Speak now (Ctrl+C to stop):\n")

        try:
            while not self.shutdown_event.is_set():
                try:
                    text = self._result_queue.get(timeout=0.2)
                    print("> " + text)
                except queue.Empty:
                    continue
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()


if __name__ == "__main__":
    RealTimeWhisperDemo().run()
