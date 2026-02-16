import json
import os
import threading
import time
import urllib.request
import webbrowser
from dataclasses import dataclass
from os.path import abspath, join
from typing import Dict, Optional

import numpy as np
from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.core.utils import is_sic_instance
from sic_framework.devices.desktop import Desktop
from sic_framework.services.dialogflow_cx.dialogflow_cx import (
    DetectIntentRequest,
    DialogflowCX,
    DialogflowCXConf,
)
from sic_framework.services.webserver.webserver_service import (
    ButtonClicked,
    WebInfoMessage,
    Webserver,
    WebserverConf,
)


@dataclass
class UserSessionState:
    socket_id: str
    session_id: int
    agent: DialogflowCX
    stop_event: threading.Event
    worker_thread: threading.Thread


class DialogflowCXMultiUserWebDemo(SICApplication):
    """
    Multi-user Dialogflow CX web demo.

    Each browser socket that connects gets its own Dialogflow CX session ID.
    The frontend receives only the transcript/response labels for its own socket ID.
    """

    def __init__(self):
        super(DialogflowCXMultiUserWebDemo, self).__init__()

        self.desktop = None
        self.desktop_mic = None
        self.webserver = None
        self.web_port = 8080

        self._users_lock = threading.Lock()
        self._users: Dict[str, UserSessionState] = {}

        self.agent_id = "27cdbb58-604e-4da9-bb34-91bb7bc62883"  # Replace if needed
        self.location = "europe-west4"  # Replace if needed
        self.keyfile_json = None

        self.set_log_level(sic_logging.DEBUG)
        self.setup()

    def setup(self):
        self.logger.info("Initializing Desktop microphone")
        self.desktop = Desktop()
        self.desktop_mic = self.desktop.mic

        current_dir = os.path.dirname(os.path.abspath(__file__))
        webfiles_dir = os.path.join(current_dir, "webfiles")

        web_conf = WebserverConf(
            host="0.0.0.0",
            port=self.web_port,
            templates_dir=webfiles_dir,
            ephemeral=True,
        )
        self.webserver = Webserver(conf=web_conf)
        self.webserver.register_callback(self.on_web_event)

        presenter_url = f"http://localhost:{self.web_port}"
        threading.Thread(target=lambda: self._open_when_ready(presenter_url), daemon=True).start()
        self.logger.info(f"Web UI: {presenter_url}")

        with open(abspath(join("..", "..", "..", "conf", "google", "google-key.json"))) as f:
            self.keyfile_json = json.load(f)

        self.logger.info("Ready for multi-user Dialogflow sessions")

    def _open_when_ready(self, url: str) -> None:
        ready_url = url.rstrip("/") + "/readyz"
        deadline = time.time() + 10.0
        while time.time() < deadline and not self.shutdown_event.is_set():
            try:
                with urllib.request.urlopen(ready_url, timeout=0.5) as resp:
                    if resp.status == 200:
                        webbrowser.open(url, new=2)
                        return
            except Exception:
                pass
            time.sleep(0.1)
        webbrowser.open(url, new=2)

    def _new_session_id(self) -> int:
        while True:
            candidate = int(np.random.randint(1, 1_000_000_000))
            with self._users_lock:
                in_use = any(state.session_id == candidate for state in self._users.values())
            if not in_use:
                return candidate

    def _web_label(self, key: str, socket_id: str) -> str:
        return f"{key}::{socket_id}"

    def _publish_to_user(self, socket_id: str, transcript: Optional[str] = None, agent_response: Optional[str] = None):
        if not self.webserver:
            return
        try:
            if transcript is not None:
                self.webserver.send_message(
                    WebInfoMessage(self._web_label("user_transcript", socket_id), transcript)
                )
            if agent_response is not None:
                self.webserver.send_message(
                    WebInfoMessage(self._web_label("agent_response", socket_id), agent_response)
                )
        except Exception as e:
            self.logger.warning(f"Failed to publish update for socket {socket_id}: {e}")

    def _create_user_agent(self) -> DialogflowCX:
        ca_conf = DialogflowCXConf(
            keyfile_json=self.keyfile_json,
            agent_id=self.agent_id,
            location=self.location,
            sample_rate_hertz=44100,
            language="en-US",
        )
        return DialogflowCX(conf=ca_conf, input_source=self.desktop_mic)

    def _start_user_session(self, socket_id: str) -> None:
        with self._users_lock:
            if socket_id in self._users:
                return

        session_id = self._new_session_id()
        self.logger.info(f"Starting Dialogflow session {session_id} for socket {socket_id}")

        try:
            agent = self._create_user_agent()
        except Exception as e:
            self.logger.error(f"Failed to create Dialogflow connector for {socket_id}: {e}")
            self._publish_to_user(socket_id, agent_response=f"(failed to initialize Dialogflow connector: {e})")
            return

        stop_event = threading.Event()
        worker = threading.Thread(
            target=self._user_loop,
            args=(socket_id, session_id, agent, stop_event),
            daemon=True,
        )
        state = UserSessionState(
            socket_id=socket_id,
            session_id=session_id,
            agent=agent,
            stop_event=stop_event,
            worker_thread=worker,
        )

        with self._users_lock:
            self._users[socket_id] = state

        self._publish_to_user(socket_id, transcript="—", agent_response="(listening...)")
        worker.start()

    def _stop_user_session(self, socket_id: str) -> None:
        with self._users_lock:
            state = self._users.pop(socket_id, None)

        if state is None:
            return

        self.logger.info(f"Stopping Dialogflow session {state.session_id} for socket {socket_id}")
        state.stop_event.set()
        try:
            state.agent.stop_component()
        except Exception:
            pass

    def _stop_all_user_sessions(self) -> None:
        with self._users_lock:
            socket_ids = list(self._users.keys())
        for socket_id in socket_ids:
            self._stop_user_session(socket_id)

    def _user_loop(self, socket_id: str, session_id: int, agent: DialogflowCX, stop_event: threading.Event) -> None:
        try:
            while not self.shutdown_event.is_set() and not stop_event.is_set():
                self.logger.info(f"[{socket_id}] Conversation turn (session {session_id})")
                try:
                    reply = agent.request(DetectIntentRequest(session_id))
                except Exception as e:
                    self.logger.error(f"[{socket_id}] Dialogflow request failed: {e}")
                    self._publish_to_user(socket_id, agent_response=f"(error: {e})")
                    time.sleep(0.5)
                    continue

                if stop_event.is_set() or self.shutdown_event.is_set():
                    break

                transcript = reply.transcript if reply and reply.transcript else ""
                response = (
                    reply.fulfillment_message
                    if reply and reply.fulfillment_message
                    else "(no fulfillment message)"
                )

                self.logger.info(f"[{socket_id}] Transcript: {transcript}")
                self.logger.info(f"[{socket_id}] Agent reply: {response}")
                self._publish_to_user(socket_id, transcript=transcript, agent_response=response)
        finally:
            try:
                agent.stop_component()
            except Exception:
                pass

    def on_web_event(self, message):
        if not is_sic_instance(message, ButtonClicked):
            return

        data = message.button
        if not isinstance(data, dict):
            return

        event_type = str(data.get("type", "")).strip().lower()
        socket_id = str(data.get("socket_id", "")).strip()
        if not socket_id:
            return

        if event_type == "register_user":
            self._start_user_session(socket_id)
        elif event_type == "unregister_user":
            self._stop_user_session(socket_id)

    def run(self):
        self.logger.info(" -- Starting Multi-user Conversational Agents Demo -- ")
        try:
            while not self.shutdown_event.is_set():
                time.sleep(0.25)
        except KeyboardInterrupt:
            self.logger.info("Demo interrupted by user")
        finally:
            self._stop_all_user_sessions()
            self.shutdown()


if __name__ == "__main__":
    demo = DialogflowCXMultiUserWebDemo()
    demo.run()
