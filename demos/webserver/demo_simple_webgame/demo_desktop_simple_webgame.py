import os
import threading
import time
import webbrowser

from sic_framework.core.sic_application import SICApplication
from sic_framework.services.webserver.webserver_service import WebserverConf, Webserver


class WebserverDemo(SICApplication):
    def __init__(self):
        super(WebserverDemo, self).__init__()
        self.webserver = None
        self.setup()

    def setup(self):
        # Get the absolute path to the webfiles directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        webfiles_dir = os.path.join(current_dir, "webfiles")

        # Configure the webserver
        conf = WebserverConf(
            host="0.0.0.0",
            port=8080,
            templates_dir=webfiles_dir,
            static_dir=webfiles_dir
        )

        # Initialize the Webserver connector
        # This will start the component (locally or remotely depending on config, default local)
        self.webserver = Webserver(conf=conf)

        # Open the default browser automatically (small delay so server is ready).
        url = f"http://localhost:{conf.port}"
        threading.Timer(0.75, lambda: webbrowser.open(url, new=2)).start()
        
        print(f"Starting webserver serving files from: {webfiles_dir}")
        print(f"Open your browser at: {url}")

    def run(self):
        try:
            # The webserver runs in a background thread in the component.
            # We just need to keep the main application alive.
            while not self.shutdown_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
            self.shutdown()


if __name__ == "__main__":
    demo = WebserverDemo()
    demo.run()
