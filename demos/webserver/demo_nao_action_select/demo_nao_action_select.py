import os
import threading
import time

from sic_framework.core.sic_application import SICApplication
from sic_framework.core.utils import is_sic_instance
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoRestRequest
from sic_framework.devices.common_naoqi.naoqi_motion import (
    NaoPostureRequest,
    NaoqiAnimationRequest,
)
from sic_framework.services.webserver.webserver_service import (
    ButtonClicked,
    Webserver,
    WebserverConf,
)


class NaoActionSelectDemo(SICApplication):
    def __init__(self):
        super(NaoActionSelectDemo, self).__init__()
        self.nao_ip = "XXX"
        self.port = 8080

        self.nao = None
        self.webserver = None

        self._motion_lock = threading.Lock()

        self.setup()

    def setup(self):
        self.nao = Nao(ip=self.nao_ip)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        webfiles_dir = os.path.join(current_dir, "webfiles")

        conf = WebserverConf(
            host="0.0.0.0",
            port=self.port,
            templates_dir=webfiles_dir,
            static_dir=webfiles_dir,
        )
        self.webserver = Webserver(conf=conf)
        self.webserver.register_callback(self.on_web_event)

        print(f"Open your browser at: http://localhost:{self.port}")

    def on_web_event(self, message):
        if not is_sic_instance(message, ButtonClicked):
            return

        raw = message.button
        if isinstance(raw, dict):
            raw = raw.get("action", "")
        if raw is None:
            raw = ""
        action = str(raw).strip().lower()
        threading.Thread(
            target=self._handle_action,
            args=(action,),
            daemon=True,
        ).start()

    def _handle_action(self, action: str):
        with self._motion_lock:
            try:
                if action == "stand":
                    self.nao.motion.request(NaoPostureRequest("Stand", 0.5))
                elif action == "sit":
                    self.nao.motion.request(NaoPostureRequest("Sit", 0.5))
                elif action == "dance":
                    self.nao.motion.request(NaoPostureRequest("Stand", 0.5))
                    time.sleep(0.5)
                    self._try_dance_animation()
                elif action == "rest":
                    self.nao.autonomous.request(NaoRestRequest())
                else:
                    print(f"Unknown action from web: {action!r}")
            except Exception as e:
                print(f"Error handling action {action!r}: {e}")

    def _try_dance_animation(self):
        # Different NAOqi versions/behavior sets can vary; try a few common candidates.
        candidates = [
            "animations/Stand/Gestures/Dance_1",
            "animations/Stand/Gestures/Dance_2",
            "animations/Stand/Gestures/Enthusiastic_4",
            "Enthusiastic_4",
        ]
        last_error = None
        for anim in candidates:
            try:
                self.nao.motion.request(NaoqiAnimationRequest(anim))
                return
            except Exception as e:
                last_error = e
                continue
        if last_error is not None:
            print(f"Could not play a dance animation (last error: {last_error})")

    def run(self):
        try:
            while not self.shutdown_event.is_set():
                time.sleep(0.25)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = NaoActionSelectDemo()
    demo.run()
