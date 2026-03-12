from __future__ import annotations

import argparse
from typing import Optional, Tuple

from mcp.server.fastmcp import FastMCP

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest


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
            "Make sure the server was started with a valid --nao-ip."
        )
    return APP


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
    app = _require_app()

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
    app = _require_app()
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

    The NAO IP address is provided via the `--nao-ip` command-line argument.
    When the server starts, it initializes a `NaoLedApplication` (a
    `SICApplication` subclass) with the given IP. When the server is about
    to exit, it calls `shutdown()` on the application so all SIC resources
    and connectors are cleaned up.
    """
    parser = argparse.ArgumentParser(
        description="MCP server exposing tools to control NAO eye LEDs via SIC."
    )
    parser.add_argument(
        "--nao-ip",
        type=str,
        required=True,
        help="IP address of the NAO robot.",
    )
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="MCP transport to use (default: stdio).",
    )
    args = parser.parse_args()

    global APP
    APP = NaoLedApplication(nao_ip=args.nao_ip)

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

