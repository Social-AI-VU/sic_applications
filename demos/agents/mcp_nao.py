from __future__ import annotations

import argparse
import os
import wave
from typing import Optional, Tuple

from mcp.server.fastmcp import FastMCP

from sic_framework.core import sic_logging
from sic_framework.core.message_python2 import AudioRequest
from sic_framework.core.sic_application import SICApplication
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import (
    NaoqiTextToSpeechRequest,
)


class NaoLedApplication(SICApplication):
    """
    Minimal SIC application that connects to a NAO robot and exposes LED control.

    This class owns the `Nao` device instance and lets the MCP tools send
    LED commands without having to manage the full SIC lifecycle themselves.
    """

    def __init__(self, nao_ip: str):
        super(NaoLedApplication, self).__init__()

        self.nao_ip: str = nao_ip
        self.nao: Optional[Nao] = None

        self.set_log_level(sic_logging.DEBUG)
        self.setup()

    def setup(self) -> None:
        """Initialize the NAO device for LED control."""
        self.logger.info("Initializing NAO robot at %s for LED control...", self.nao_ip)
        # Use dev_test=True so we don't interfere with production devices by default.
        self.nao = Nao(ip=self.nao_ip, dev_test=True)
        self.logger.info("NAO LED application setup complete.")


# Global application instance used by MCP tools.
APP: Optional[NaoLedApplication] = None


mcp = FastMCP("Nao LED MCP Server", json_response=True)


def _require_app() -> NaoLedApplication:
    """Internal helper to ensure the global APP is available."""
    if APP is None or APP.nao is None:
        raise RuntimeError(
            "NAO LED application is not initialized. "
            "Set NAO_IP (or call 'connect') so the server can connect."
        )
    return APP


def _resolve_nao_ip(nao_ip: Optional[str]) -> str:
    if nao_ip and nao_ip.strip():
        return nao_ip.strip()
    env_ip = os.getenv("NAO_IP", "").strip()
    if env_ip:
        return env_ip
    raise RuntimeError(
        "No NAO IP provided. Pass nao_ip to the 'connect' tool or set NAO_IP."
    )


def _ensure_connected(nao_ip: Optional[str] = None) -> NaoLedApplication:
    """
    Ensure the global NAO application is connected.

    - If already connected, returns the existing app.
    - If `nao_ip` is provided, it is stored in `NAO_IP` and used.
    - Otherwise, `NAO_IP` must already be set.
    """
    global APP

    if APP is not None and APP.nao is not None:
        return APP

    if nao_ip is not None and nao_ip.strip():
        os.environ["NAO_IP"] = nao_ip.strip()

    ip = _resolve_nao_ip(None)
    APP = NaoLedApplication(nao_ip=ip)
    return APP


@mcp.tool()
def connect(nao_ip: Optional[str] = None) -> str:
    """
    One-time connection setup to the NAO robot.

    If `nao_ip` is omitted, the environment variable `NAO_IP` is used.
    """
    app = _ensure_connected(nao_ip=nao_ip)
    return f"Connected to NAO at {app.nao_ip}."


def _color_name_to_rgb(name: str) -> Tuple[float, float, float]:
    """
    Map a simple color name to RGB triplet in [0, 1].
    Defaults to white if the name is unknown.
    """
    table = {
        "red": (1.0, 0.0, 0.0),
        "green": (0.0, 1.0, 0.0),
        "blue": (0.0, 0.0, 1.0),
        "yellow": (1.0, 1.0, 0.0),
        "cyan": (0.0, 1.0, 1.0),
        "magenta": (1.0, 0.0, 1.0),
        "white": (1.0, 1.0, 1.0),
        "orange": (1.0, 0.5, 0.0),
        "purple": (0.5, 0.0, 0.5),
        "pink": (1.0, 0.75, 0.8),
        "off": (0.0, 0.0, 0.0),
    }
    return table.get(name.strip().lower(), (1.0, 1.0, 1.0))


@mcp.tool()
def set_eye_color_rgb(
    r: float,
    g: float,
    b: float,
    duration: float = 0.0,
    led_group: str = "FaceLeds",
) -> str:
    """
    Set the NAO eye LEDs to a specific RGB color.

    - `r`, `g`, `b` should be floats between 0.0 and 1.0.
    - `duration` is the fade duration in seconds (0 for instant change).
    - `led_group` defaults to "FaceLeds" which controls both eyes.
    """
    app = _ensure_connected()

    try:
        app.nao.leds.request(
            NaoFadeRGBRequest(name=led_group, r=r, g=g, b=b, duration=duration)
        )
        app.logger.info(
            "Set %s to RGB=(%.3f, %.3f, %.3f) over %.2fs",
            led_group,
            r,
            g,
            b,
            duration,
        )
        return f"Set {led_group} to RGB ({r:.3f}, {g:.3f}, {b:.3f}) over {duration:.2f}s."
    except Exception as exc:
        app.logger.error("Failed to set eye color via RGB: %r", exc)
        return f"ERROR: Failed to set eye color: {exc!r}"


@mcp.tool()
def set_eye_color_name(
    color_name: str,
    duration: float = 0.0,
    led_group: str = "FaceLeds",
) -> str:
    """
    Set the NAO eye LEDs to a named color.

    Supported colors include: red, green, blue, yellow, cyan, magenta,
    white, orange, purple, pink, and off. Unknown names default to white.
    """
    app = _ensure_connected()
    r, g, b = _color_name_to_rgb(color_name)

    try:
        app.nao.leds.request(
            NaoFadeRGBRequest(name=led_group, r=r, g=g, b=b, duration=duration)
        )
        app.logger.info(
            "Set %s to color '%s' -> RGB=(%.3f, %.3f, %.3f) over %.2fs",
            led_group,
            color_name,
            r,
            g,
            b,
            duration,
        )
        return (
            f"Set {led_group} to '{color_name}' "
            f"(RGB {r:.3f}, {g:.3f}, {b:.3f}) over {duration:.2f}s."
        )
    except Exception as exc:
        app.logger.error("Failed to set eye color via name '%s': %r", color_name, exc)
        return f"ERROR: Failed to set eye color '{color_name}': {exc!r}"


@mcp.tool()
def play_audio(wav_path: str) -> str:
    """
    Play a local WAV file through the NAO's speakers.

    The file is read by the MCP server process and sent as an AudioRequest to SIC.
    """
    app = _ensure_connected()

    if not wav_path or not isinstance(wav_path, str):
        return "ERROR: wav_path must be a non-empty string."

    path = os.path.expanduser(wav_path)
    if not os.path.isfile(path):
        return f"ERROR: WAV file not found: {path}"

    try:
        with wave.open(path, "rb") as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            sample_rate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())

        if channels != 1:
            return f"ERROR: WAV must be mono (1 channel). Got {channels} channels."
        if sample_width != 2:
            return f"ERROR: WAV must be 16-bit PCM (sample width 2). Got {sample_width}."

        app.nao.speaker.request(AudioRequest(sample_rate=sample_rate, waveform=frames))
        app.logger.info("Played WAV '%s' at %d Hz (%d bytes).", path, sample_rate, len(frames))
        return f"Playing '{os.path.basename(path)}' at {sample_rate} Hz."
    except Exception as exc:
        app.logger.error("Failed to play WAV '%s': %r", path, exc)
        return f"ERROR: Failed to play WAV: {exc!r}"


@mcp.tool()
def say_text(text: str, animated: bool = False) -> str:
    """
    Make the NAO robot say the given text using its onboard TTS.

    - `text`: What the robot should say.
    - `animated`: If True, use animated speech (gestures, etc.) when available.
    """
    app = _ensure_connected()

    if not text or not isinstance(text, str):
        return "ERROR: text must be a non-empty string."

    try:
        app.nao.tts.request(NaoqiTextToSpeechRequest(text, animated=animated))
        app.logger.info("NAO TTS said (animated=%s): %s", animated, text)
        return f"NAO said: {text}"
    except Exception as exc:
        app.logger.error("Failed to say text via TTS: %r", exc)
        return f"ERROR: Failed to say text: {exc!r}"


@mcp.tool()
def shutdown_nao() -> str:
    """
    Explicitly shut down the SIC application and disconnect from the NAO.

    This is typically not required because the server will call shutdown
    automatically when it exits, but it can be useful for manual cleanup.
    """
    global APP
    if APP is None:
        return "NAO LED application is not running."

    try:
        APP.shutdown()
    except SystemExit:
        # SICApplication.shutdown() ultimately calls sys.exit(0); swallow it
        # here so the MCP server process can remain alive if desired.
        pass

    APP = None
    return "NAO LED application has been shut down."


def main() -> None:
    """
    Entry point for running this module as an MCP server.

    The server can start without connecting to a robot. To connect, call the
    `connect` tool with an explicit `nao_ip` or set the `NAO_IP` environment
    variable and then call `connect`.
    """
    parser = argparse.ArgumentParser(
        description="MCP server exposing tools to control NAO eye LEDs via SIC."
    )
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="MCP transport to use (default: stdio).",
    )
    args = parser.parse_args()

    try:
        mcp.run(transport=args.transport)
    finally:
        # Ensure SICApplication shutdown is always invoked when the MCP server
        # stops, so that all devices and connectors are cleaned up.
        if APP is not None:
            try:
                APP.shutdown()
            except SystemExit:
                # SICApplication.exit_handler will call sys.exit(0); ignore it
                # here so that normal process teardown can continue.
                pass


if __name__ == "__main__":
    main()

