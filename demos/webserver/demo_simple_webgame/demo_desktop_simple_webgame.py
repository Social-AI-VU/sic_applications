import os
import threading
import time
import webbrowser
import urllib.request

from sic_framework.core.sic_application import SICApplication
from sic_framework.services.webserver.webserver_service import WebserverConf, Webserver
from pathlib import Path
from dotenv import load_dotenv


class WebserverDemo(SICApplication):
    """
    Minimal example that serves a static HTML/JS game using the SIC webserver.

    The game logic lives entirely in `webfiles/index.html`; this Python wrapper
    just:
      1. starts the `Webserver` component pointed at that folder, and
      2. opens the default desktop browser once the server is ready.
    """

    def __init__(self):
        super(WebserverDemo, self).__init__()
        self.webserver = None

        # Load environment variables
        env_path = Path(__file__).parent.parent.parent / "conf" / ".env"
        load_dotenv(env_path)
        
        self.setup()

    def setup(self):
        """
        Configure and start the webserver that serves the simple web game.

        The same folder is used for both templates and static files so that the
        game can reference its assets via relative paths.
        """
        # Get the absolute path to the webfiles directory.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        webfiles_dir = os.path.join(current_dir, "webfiles")

        # Configure the webserver to listen on all interfaces at port 8080.
        conf = WebserverConf(
            host="0.0.0.0",
            port=8080,
            templates_dir=webfiles_dir,
            static_dir=webfiles_dir,
        )

        # Initialize the Webserver connector.
        # This will start the component (locally or remotely depending on config, default local).
        self.webserver = Webserver(conf=conf)

        # Open the default browser automatically once the server is ready.
        url = f"http://localhost:{conf.port}"
        threading.Thread(target=lambda: self._open_when_ready(url), daemon=True).start()

        print(f"Starting webserver serving files from: {webfiles_dir}")
        print(f"Open your browser at: {url}")

    def _open_when_ready(self, url: str) -> None:
        """
        Poll the server's `/readyz` endpoint; open the browser once it's healthy.

        If readiness cannot be confirmed within a small window, the browser is
        opened anyway to aid debugging (e.g. to inspect network errors).
        """
        ready_url = url.rstrip("/") + "/readyz"
        deadline = time.time() + 10.0
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(ready_url, timeout=0.5) as resp:
                    if resp.status == 200:
                        webbrowser.open(url, new=2)
                        return
            except Exception:
                pass
            time.sleep(0.1)
        # Fall back to opening anyway (useful for debugging failures).
        webbrowser.open(url, new=2)

    def run(self):
        """
        Keep the main application process alive while the webserver runs in the
        background. Press Ctrl+C to trigger shutdown.
        """
        try:
            # The webserver runs in a background thread in the component.
            # We just need to keep the main application alive.
            while not self.shutdown_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = WebserverDemo()
    demo.run()
