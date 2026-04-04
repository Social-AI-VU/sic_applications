import json
import os
import socket
import threading
import time
import urllib.request
import webbrowser
from dataclasses import dataclass
from os.path import abspath, join
from typing import Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

import numpy as np
from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.core.utils import is_sic_instance
from sic_framework.core.message_python2 import AudioMessage
from sic_framework.services.dialogflow_cx.dialogflow_cx import (
    DetectIntentRequest,
    DialogflowCX,
    DialogflowCXConf,
    StopListeningMessage,
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
    start_listening_event: threading.Event
    worker_thread: threading.Thread


class DialogflowCXMultiUserWebDemo(SICApplication):
    """
    Multi-user Dialogflow CX web demo.

    Each browser socket that connects gets its own Dialogflow CX session ID.
    The frontend receives only the transcript/response labels for its own socket ID.
    """

    def __init__(self):
        super(DialogflowCXMultiUserWebDemo, self).__init__()

        self.webserver = None
        self.web_port = 8080

        self._users_lock = threading.Lock()
        self._users: Dict[str, UserSessionState] = {}

        self.agent_id = "XXX"  # Replace if needed
        self.location = "XXX"  # Replace if needed
        self.keyfile_json = None

        self.set_log_level(sic_logging.INFO)

        # Load environment variables
        env_path = Path(__file__).parent.parent.parent / "conf" / ".env"
        load_dotenv(env_path)
        
        self.setup()

    def setup(self):
        """
        Initialize the webserver, open the browser UI, and load Dialogflow credentials.

        This does not start any Dialogflow sessions yet; those are created lazily per
        browser socket when we receive a 'register_user' event from the frontend.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        webfiles_dir = os.path.join(current_dir, "webfiles")

        web_conf = WebserverConf(
            host="0.0.0.0",
            port=self.web_port,
            templates_dir=webfiles_dir,
            tunnel_enable=True,
            tunnel_provider="ngrok",
            cors_allowed_origins="*",  # Allow tunnel (ngrok) and other remote origins
        )
        self.webserver = Webserver(conf=web_conf)
        self.webserver.register_callback(self.on_web_event)

        presenter_url = f"http://localhost:{self.web_port}"
        threading.Thread(target=lambda: self._open_when_ready(presenter_url), daemon=True).start()
        self.logger.info(f"Local Web UI (this machine): {presenter_url}")
        threading.Thread(target=self._log_connection_urls, daemon=True).start()

        with open(abspath(join("..", "..", "..", "conf", "google", "google-key.json"))) as f:
            self.keyfile_json = json.load(f)

        self.logger.info("Ready for multi-user Dialogflow sessions")

    def _log_connection_urls(self) -> None:
        """
        Log helpful URLs for connecting to the demo:
        - localhost (current machine)
        - LAN URL (other devices on same network), if detectable
        - Public tunnel URL (if tunnel_enable is on and a tunnel comes up)
        """
        # LAN URL for other devices on the same network.
        try:
            hostname = socket.gethostname()
            lan_ip = socket.gethostbyname(hostname)
        except Exception:
            lan_ip = None

        if lan_ip and lan_ip not in ("127.0.0.1", "localhost"):
            self.logger.info(f"LAN Web UI (same network devices): http://{lan_ip}:{self.web_port}")

        # If a tunnel is enabled, poll the /api/tunnel helper until it reports a public URL.
        api_url = f"http://127.0.0.1:{self.web_port}/api/tunnel"
        deadline = time.time() + 120.0  # give the tunnel some time to start
        public_url: Optional[str] = None

        while time.time() < deadline and not self.shutdown_event.is_set():
            try:
                with urllib.request.urlopen(api_url, timeout=1.0) as resp:
                    data = json.load(resp)
                if data.get("enabled") and data.get("url"):
                    public_url = str(data["url"])
                    break
            except Exception:
                pass
            time.sleep(1.0)

        if public_url:
            self.logger.info(f"Public Web UI (tunnel): {public_url}")
        else:
            self.logger.info("No public Web UI available (tunnel not enabled or failed to start)")

    def _open_when_ready(self, url: str) -> None:
        """
        Poll the webserver /readyz endpoint and open the presenter URL in the
        default browser once the port is reachable (or after a short timeout).
        """
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
        """
        Generate a session ID that is unique across all active user sessions.

        Each browser socket gets its own Dialogflow CX session so their
        conversational context does not interfere.
        """
        while True:
            candidate = int(np.random.randint(1, 1_000_000_000))
            with self._users_lock:
                in_use = any(state.session_id == candidate for state in self._users.values())
            if not in_use:
                return candidate

    def _web_label(self, key: str, socket_id: str) -> str:
        return f"{key}::{socket_id}"

    def _publish_to_user(self, socket_id: str, transcript: Optional[str] = None, agent_response: Optional[str] = None):
        """
        Convenience helper: push transcript / agent_response updates for a single
        user to the web UI via WebInfo labels that are namespaced by socket_id.
        """
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
        """
        Construct a DialogflowCX connector for a single user session.

        Audio is streamed from the browser, not from a local microphone, so we
        do not pass an input_source here.
        """
        ca_conf = DialogflowCXConf(
            keyfile_json=self.keyfile_json,
            agent_id=self.agent_id,
            location=self.location,
            sample_rate_hertz=44100,
            language="en-US",
        )
        # No hardware microphone: audio is streamed from the browser via Socket.IO.
        return DialogflowCX(conf=ca_conf)

    def _start_user_session(self, socket_id: str) -> None:
        """
        Create per-user state (Dialogflow connector + worker thread) for a new
        Socket.IO connection identified by socket_id.

        If a session already exists for this socket_id, this is a no-op.
        """
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
        start_listening_event = threading.Event()
        worker = threading.Thread(
            target=self._user_loop,
            args=(socket_id, session_id, agent, stop_event, start_listening_event),
            daemon=True,
        )
        state = UserSessionState(
            socket_id=socket_id,
            session_id=session_id,
            agent=agent,
            stop_event=stop_event,
            start_listening_event=start_listening_event,
            worker_thread=worker,
        )

        with self._users_lock:
            self._users[socket_id] = state

        self._publish_to_user(socket_id, transcript="—", agent_response="(listening...)")
        worker.start()

    def _stop_user_session(self, socket_id: str) -> None:
        """
        Stop a single user session and its Dialogflow connector, if it exists.
        """
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
        """
        Best-effort shutdown of all active user sessions on application exit.
        """
        with self._users_lock:
            socket_ids = list(self._users.keys())
        for socket_id in socket_ids:
            self._stop_user_session(socket_id)

    def _user_loop(
        self,
        socket_id: str,
        session_id: int,
        agent: DialogflowCX,
        stop_event: threading.Event,
        start_listening_event: threading.Event,
    ) -> None:
        try:
            while not self.shutdown_event.is_set() and not stop_event.is_set():
                # Wait for user to press record before starting the next turn.
                while not stop_event.is_set() and not self.shutdown_event.is_set():
                    if start_listening_event.wait(timeout=0.25):
                        break
                if stop_event.is_set() or self.shutdown_event.is_set():
                    break
                start_listening_event.clear()

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
                # Notify this client that the turn has completed, so it can auto-stop the mic.
                try:
                    self.webserver.send_message(
                        WebInfoMessage(self._web_label("turn_done", socket_id), True)
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to publish turn_done for socket {socket_id}: {e}")
        finally:
            try:
                agent.stop_component()
            except Exception:
                pass

    def on_web_event(self, message):
        """
        Entry point for all events coming from the web UI via ButtonClicked.

        The frontend sends small JSON payloads with a 'type' and 'socket_id'
        field, plus optional audio data when streaming microphone chunks.
        """
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
            return

        # All other events require an active user session.
        with self._users_lock:
            state = self._users.get(socket_id)
        if state is None:
            return

        if event_type == "unregister_user":
            self._stop_user_session(socket_id)
        elif event_type == "start_audio":
            # User pressed record; allow the next DetectIntentRequest to run.
            state.start_listening_event.set()
        elif event_type == "audio_chunk":
            # Browser-streamed PCM16 audio for this user.
            audio_list = data.get("audio")
            if not isinstance(audio_list, list):
                return
            try:
                audio_bytes = bytes(int(b) & 0xFF for b in audio_list)
            except Exception as e:
                self.logger.warning(f"Invalid audio payload for socket {socket_id}: {e}")
                return

            sample_rate = int(data.get("sample_rate") or 44100)
            try:
                state.agent.send_message(AudioMessage(audio_bytes, sample_rate=sample_rate))
            except Exception as e:
                self.logger.error(f"[{socket_id}] Failed to forward audio chunk: {e}")
        elif event_type == "stop_audio":
            # Signal Dialogflow to finalize the current turn.
            try:
                state.agent.send_message(StopListeningMessage(session_id=state.session_id))
            except Exception as e:
                self.logger.error(f"[{socket_id}] Failed to send StopListeningMessage: {e}")

    def run(self):
        """
        Idle main loop that keeps the SICApplication alive until shutdown.

        All Dialogflow work happens in per-user worker threads started in
        _start_user_session; this loop just waits for Ctrl+C or shutdown_event.
        """
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