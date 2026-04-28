# Import basic SIC framework modules
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s), service(s), and message(s) we will be using
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.devices.desktop import Desktop
from sic_framework.services.elevenlabs_tts.elevenlabs_tts import (
    ElevenLabsTTS, 
    ElevenLabsTTSConf, 
    GetElevenLabsSpeechRequest
    )
from sic_framework.services.llm import GPT, GPTConf, GPTRequest

# import demo-specific modules
from os.path import abspath, dirname, join
from dotenv import load_dotenv
from os import environ
import threading
import queue
import os
import re

# Matches whitespace following a sentence-ending punctuation mark
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

SAMPLE_RATE = 22050


class GPTElevenLabsStreamingDemo(SICApplication):
    """
    Streaming demo: GPT token stream -> ElevenLabs TTS -> Desktop speakers.

    As GPT streams tokens, complete sentences are detected and sent to
    ElevenLabs immediately for synthesis, so audio playback starts before
    GPT has finished generating the full response.

    Requirements:
    1. ElevenLabs TTS service must be installed and running
    2. OpenAI GPT service must be running: run-gpt
    3. OPENAI_API_KEY and ELEVENLABS_API_KEY must be set (env or .env file)
    """

    def __init__(self, api_key=None, env_path=None):
        super(GPTElevenLabsStreamingDemo, self).__init__()

        self.env_path = env_path
        self._provided_api_key = api_key

        self.gpt = None
        self.tts = None
        self.desktop = None

        self._text_buffer = ""
        self._sentence_queue = queue.Queue()
        self._gpt_done = threading.Event()

        self.set_log_level(sic_logging.INFO)

        # Log files will only be written if set_log_file_path is called. Must be a valid full path to a directory.
        # self.set_log_file_path("/path/to/log/directory")

        # Load environment variables
        self.load_env("../../conf/.env")

        self.setup()

    def setup(self):
        if self.env_path:
            load_dotenv(self.env_path)

        self.api_key = (
            self._provided_api_key or os.getenv("ELEVENLABS_API_KEY")
        )

        if not self.api_key:
            raise ValueError(
                "No ElevenLabs API key found. Set ELEVENLABS_API_KEY."
            )

        self.desktop = Desktop(
            speakers_conf=SpeakersConf(sample_rate=SAMPLE_RATE)
        )

        tts_conf = ElevenLabsTTSConf(
            api_key=self.api_key,
            default_mode="ws",
            sample_rate=SAMPLE_RATE,
        )
        self.tts = ElevenLabsTTS(conf=tts_conf)

        conf = GPTConf(
            openai_key=environ["OPENAI_API_KEY"],
            system_message=(
                "You are a helpful assistant. Keep responses concise."
            ),
            model="gpt-4o-mini",
            max_tokens=300,
        )
        self.gpt = GPT(conf=conf)
        self.gpt.register_callback(self._on_stream_chunk)

    def _on_stream_chunk(self, message):
        """
        Fires for every GPT response event.

        Intermediate chunks (is_stream_chunk=True) are buffered and split
        on sentence boundaries. The final event flushes any remaining text.
        """
        if not hasattr(message, "response"):
            return

        is_chunk = getattr(message, "is_stream_chunk", False)

        if is_chunk:
            print(message.response, end="", flush=True)
            self._text_buffer += message.response

            # Split on sentence boundaries; keep trailing incomplete fragment
            parts = _SENTENCE_BOUNDARY.split(self._text_buffer)
            for sentence in parts[:-1]:
                sentence = sentence.strip()
                if sentence:
                    self._sentence_queue.put(sentence)
            self._text_buffer = parts[-1]
        else:
            # Stream finished — flush whatever is left in the buffer
            remainder = self._text_buffer.strip()
            if remainder:
                self._sentence_queue.put(remainder)
            self._text_buffer = ""
            print()
            self._gpt_done.set()

    def _speak_sentences(self):
        """Worker thread: synthesize and play each queued sentence in order."""
        while True:
            try:
                sentence = self._sentence_queue.get(timeout=0.1)
            except queue.Empty:
                if self._gpt_done.is_set() and self._sentence_queue.empty():
                    break
                continue

            self.logger.info("Speaking: {}".format(sentence))
            try:
                reply = self.tts.request(
                    GetElevenLabsSpeechRequest(text=sentence, mode="batch")
                )
                self.logger.info(
                    "Got {} bytes, playing audio...".format(
                        len(reply.waveform)
                    )
                )
                self.desktop.speakers.request(
                    AudioRequest(reply.waveform, reply.sample_rate)
                )
                self.logger.info("Playback done.")
            except Exception as e:
                self.logger.error("TTS error: {}".format(e))

    def run(self):
        self.logger.info(
            "GPT + ElevenLabs Streaming Demo. Type 'quit' to exit."
        )

        try:
            while not self.shutdown_event.is_set():
                user_input = input("You: ").strip()
                if user_input.lower() in {"quit", "exit", "q"}:
                    break
                if not user_input:
                    continue

                # Reset per-turn state
                self._text_buffer = ""
                self._gpt_done.clear()
                while not self._sentence_queue.empty():
                    try:
                        self._sentence_queue.get_nowait()
                    except queue.Empty:
                        break

                # Audio thread starts immediately, consumes queued sentences
                audio_thread = threading.Thread(
                    target=self._speak_sentences, daemon=True
                )
                audio_thread.start()

                print("AI: ", end="", flush=True)
                self.gpt.request(GPTRequest(prompt=user_input, stream=True))

                # Wait for all audio to finish before next turn
                audio_thread.join()

        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = GPTElevenLabsStreamingDemo(
        env_path=abspath(join(dirname(__file__), "..", "..", "conf", ".env"))
    )
    demo.run()
