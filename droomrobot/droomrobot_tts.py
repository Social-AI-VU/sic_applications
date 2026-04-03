import asyncio
import base64
import logging
import os
import hashlib
import string
import wave
from json import dumps, loads, load, dump
from pathlib import Path

import websockets

from enum import Enum


class TTSService(Enum):
    GOOGLE = 1
    ELEVENLABS = 2


class TTSConf:

    def __init__(self, speaking_rate):
        self.speaking_rate = speaking_rate


class GoogleTTSConf(TTSConf):

    def __init__(self, speaking_rate=1.0, google_tts_voice_name="nl-NL-Standard-D", google_tts_voice_gender="FEMALE"):
        super().__init__(speaking_rate)
        self.google_tts_voice_name = google_tts_voice_name
        self.google_tts_voice_gender = google_tts_voice_gender


class ElevenLabsTTSConf(TTSConf):
    def __init__(self, speaking_rate=None, voice_id='yO6w2xlECAQRFP6pX7Hw', model_id='eleven_flash_v2_5'):
        super().__init__(None if speaking_rate == 1.0 else speaking_rate)
        self.voice_id = voice_id
        self.model_id = model_id


class ElevenLabsTTS:
    def __init__(self, elevenlabs_key, voice_id, model_id, sample_rate=22050, speaking_rate=None):
        self.elevenlabs_key = elevenlabs_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.sample_rate = sample_rate
        self.websocket = None
        self.speaking_rate = max(0.7, min(speaking_rate, 1.2)) if speaking_rate else speaking_rate
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger("droomrobot")

    def _voice_settings(self):
        vs = {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "use_speaker_boost": False,
            "chunk_length_schedule": [120, 160, 250, 290],
        }
        if self.speaking_rate is not None:
            vs["speed"] = self.speaking_rate
        return vs

    def _ws_uri(self):
        return (
            f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input"
            f"?model_id={self.model_id}"
            f"&output_format=pcm_{self.sample_rate}"
            f"&inactivity_timeout=180"
            f"&auto_mode=false"
        )

    async def connect(self):
        """Open a WebSocket and send the init space (without flush) to register voice settings."""
        self.websocket = await asyncio.wait_for(websockets.connect(self._ws_uri()), timeout=8.0)
        await self.websocket.send(dumps({
            "text": " ",
            "voice_settings": self._voice_settings(),
            "xi_api_key": self.elevenlabs_key,
        }))

    async def disconnect(self):
        if self.websocket:
            try:
                await self.websocket.send(dumps({"text": ""}))
                await self.websocket.close()
            except Exception as e:
                self.logger.error(f"[TTS] Error while closing websocket: {e}")
            finally:
                self.websocket = None

    async def _open_and_speak(self, text):
        """Open a fresh connection and speak text in one round trip.

        Combines voice settings + text + flush into the first message so there
        is no separate init→speak handshake. Used when we know we need a fresh
        connection (e.g. previous connection closed after a flush).
        """
        self.websocket = await asyncio.wait_for(websockets.connect(self._ws_uri()), timeout=8.0)
        await self.websocket.send(dumps({
            "text": text,
            "voice_settings": self._voice_settings(),
            "xi_api_key": self.elevenlabs_key,
            "flush": True,
        }))
        return await self._collect_audio()

    async def _collect_audio(self):
        """Collect audio chunks until isFinal or inter-chunk timeout. Returns (bytes, success)."""
        audio_chunks = []
        timeout = 5.0  # 5s for first chunk; 0.5s between subsequent chunks
        try:
            while True:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
                    data = loads(message)
                    if data.get("audio"):
                        audio_chunks.append(base64.b64decode(data["audio"]))
                        timeout = 0.5
                    if data.get("isFinal"):
                        break
                except asyncio.TimeoutError:
                    if audio_chunks:
                        break  # Inter-chunk gap — response is complete
                    self.logger.error('[TTS] No audio received from Elevenlabs')
                    self.websocket = None
                    return None, False
        except (websockets.exceptions.ConnectionClosedOK,
                websockets.exceptions.ConnectionClosedError,
                Exception) as e:
            self.logger.warning(f"[TTS] Connection closed during receive: {e}")
            self.websocket = None
            return b''.join(audio_chunks) if audio_chunks else None, bool(audio_chunks)

        # Connection may have closed server-side after the flush response.
        # Mark it None so next speak() opens fresh without the overhead of ping.
        self.websocket = None
        return b''.join(audio_chunks) if audio_chunks else None, True

    async def speak(self, text):
        async with self.lock:
            # Every speak() opens a fresh connection and sends voice settings +
            # text in a single message. This avoids the separate init round trip
            # and the ping check, since connections reliably close after each flush.
            audio, success = await self._open_and_speak(text)

            if not success:
                self.logger.warning("[TTS] Speak failed, retrying once.")
                audio, _ = await self._open_and_speak(text)

            return audio


class TTSCacher:

    def __init__(self, tts_cache_dir='tts_cache', tts_cache_map_file_name='tts_cache_map.json', subfolder_depth=2):
        root = Path(__file__).parent.resolve()
        self.tts_cache_dir = root / tts_cache_dir
        self.tts_cache_map_file = self.tts_cache_dir / tts_cache_map_file_name
        self.subfolder_depth = subfolder_depth

        self.tts_cache = self._load_cache()

    @staticmethod
    def normalize_text(text: str) -> str:
        """Lowercase, strip, remove punctuation for consistent caching"""
        text = text.strip().lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        return text

    def make_tts_key(self, text: str, voice_conf: TTSConf) -> str:
        """Generate a hash key based on text + TTS parameters"""
        if isinstance(voice_conf, GoogleTTSConf):
            payload = {
                "text": self.normalize_text(text),
                'tts_service': "GOOGLE",
                "speaking_rate": voice_conf.speaking_rate,
                "setting_1": voice_conf.google_tts_voice_name,
                "setting_2": voice_conf.google_tts_voice_gender,
            }
        elif isinstance(voice_conf, ElevenLabsTTSConf):
            payload = {
                "text": self.normalize_text(text),
                'tts_service': "ELEVENLABS",
                "speaking_rate": voice_conf.speaking_rate,
                "setting_1": voice_conf.model_id,
                "setting_2": voice_conf.voice_id,
            }
        else:
            raise ValueError(f'Voice Conf {voice_conf} is not supported.')

        # Sort keys to ensure deterministic JSON
        canonical = dumps(payload, sort_keys=True)
        return hashlib.md5(canonical.encode("utf-8")).hexdigest()

    def save_audio_file(self, tts_key: str, audio_bytes: bytes, sample_rate: int, sample_width: int = 2, channels: int = 1):
        subfolder = self.tts_cache_dir / tts_key[:self.subfolder_depth]
        os.makedirs(subfolder, exist_ok=True)
        filename = os.path.join(subfolder, f"{tts_key}.wav")

        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)  # 2 bytes = 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_bytes)

        self.tts_cache[tts_key] = filename
        self._save_cache()

    def load_audio_file(self, tts_key):
        if tts_key in self.tts_cache:
            # Cached audio exists, play it
            audio_file = self.tts_cache[tts_key]
            if os.path.exists(audio_file):
                return audio_file
            else:
                del self.tts_cache[tts_key]
        return None

    def _load_cache(self) -> dict:
        if os.path.exists(self.tts_cache_map_file):
            with open(self.tts_cache_map_file, "r") as f:
                return load(f)
        return {}

    def _save_cache(self):
        with open(self.tts_cache_map_file, "w") as f:
            dump(self.tts_cache, f, indent=2)
