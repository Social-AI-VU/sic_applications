import os
import threading
import time
import json
import urllib.request
import webbrowser

from sic_framework.core.sic_application import SICApplication
from sic_framework.core.utils import is_sic_instance
from sic_framework.services.webserver.webserver_service import (
    ButtonClicked,
    WebInfoMessage,
    Webserver,
    WebserverConf,
)


class AudienceSurveyDemo(SICApplication):
    def __init__(self):
        super(AudienceSurveyDemo, self).__init__()

        self.port = 8080
        self.enable_tunnel = True
        self.tunnel_provider = "cloudflared"  # or "ngrok" (requires the binary installed)
        self.survey_duration_s = 120
        self.question = "Audience survey: which option do you vote for?"
        self.options = ["Option A", "Option B", "Option C"]

        self.webserver = None

        self._lock = threading.Lock()
        self._started_at = None
        self._ends_at = None
        self._voting_open = False
        self._vote_counts = {opt: 0 for opt in self.options}
        self._audience_url = None

        self.setup()

    def setup(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        webfiles_dir = os.path.join(current_dir, "webfiles")

        conf = WebserverConf(
            host="0.0.0.0",
            port=self.port,
            templates_dir=webfiles_dir,
            static_dir=webfiles_dir,
            ephemeral=True,
            tunnel_enable=self.enable_tunnel,
            tunnel_provider=self.tunnel_provider,
        )

        self.webserver = Webserver(conf=conf)
        self.webserver.register_callback(self.on_web_event)

        self._start_survey()
        threading.Thread(target=self._broadcast_loop, daemon=True).start()
        threading.Thread(target=self._tunnel_watch_loop, daemon=True).start()

        presenter_url = f"http://localhost:{self.port}"
        threading.Timer(0.75, lambda: webbrowser.open(presenter_url, new=2)).start()
        print(f"Presenter page: {presenter_url}")
        self._audience_url = f"http://{self.client_ip}:{self.port}/vote.html"
        print(f"Audience link: {self._audience_url}")

    def _tunnel_watch_loop(self):
        """
        Poll the webserver's /api/tunnel endpoint until a public URL is available,
        then switch the audience URL to the tunneled URL.
        """
        if not self.enable_tunnel:
            return

        tunnel_api = f"http://localhost:{self.port}/api/tunnel"
        while not self.shutdown_event.is_set():
            try:
                with urllib.request.urlopen(tunnel_api, timeout=1.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                public_url = data.get("url")
                if public_url:
                    with self._lock:
                        self._audience_url = public_url.rstrip("/") + "/vote.html"
                    print(f"Public tunnel URL: {public_url}")
                    print(f"Audience link (public): {self._audience_url}")
                    return
            except Exception:
                pass
            time.sleep(1.0)

    def _start_survey(self):
        with self._lock:
            self._started_at = time.time()
            self._ends_at = self._started_at + float(self.survey_duration_s)
            self._voting_open = True
            self._vote_counts = {opt: 0 for opt in self.options}

    def _parse_vote(self, raw):
        if raw is None:
            return None
        if isinstance(raw, dict):
            if raw.get("type") == "request_state":
                return "__request_state__"
            if raw.get("type") == "vote":
                return str(raw.get("option", "")).strip()
            return None

        text = str(raw).strip()
        if text == "request_state":
            return "__request_state__"
        if text.startswith("vote:"):
            return text.split("vote:", 1)[1].strip()
        return text

    def on_web_event(self, message):
        if not is_sic_instance(message, ButtonClicked):
            return

        vote = self._parse_vote(message.button)
        if vote is None:
            return

        if vote == "__request_state__":
            # Immediately send current state to all clients.
            state = self._snapshot()
            try:
                self.webserver.send_message(WebInfoMessage("survey_state", state))
            except Exception as e:
                print(f"Failed to send survey_state: {e}")
            return

        # Allow a simple presenter reset command if ever needed.
        if vote.lower() == "reset":
            self._start_survey()
            return

        with self._lock:
            if not self._voting_open:
                return
            if vote in self._vote_counts:
                self._vote_counts[vote] += 1

    def _snapshot(self):
        with self._lock:
            now = time.time()
            seconds_left = max(0, int(round(self._ends_at - now))) if self._ends_at else 0
            if self._voting_open and now >= self._ends_at:
                self._voting_open = False

            total = sum(self._vote_counts.values())
            results = []
            for opt in self.options:
                count = int(self._vote_counts.get(opt, 0))
                pct = (count / total * 100.0) if total > 0 else 0.0
                results.append({"option": opt, "count": count, "percent": round(pct, 1)})

            return {
                "question": self.question,
                "options": list(self.options),
                "votingOpen": bool(self._voting_open),
                "secondsLeft": seconds_left,
                "totalVotes": int(total),
                "results": results,
            }

    def _broadcast_loop(self):
        # Periodically broadcast survey state so late-joining clients sync automatically.
        while not self.shutdown_event.is_set():
            state = self._snapshot()
            try:
                self.webserver.send_message(WebInfoMessage("survey_state", state))
                self.webserver.send_message(
                    WebInfoMessage(
                        "audience_url",
                        self._audience_url or f"http://{self.client_ip}:{self.port}/vote.html",
                    )
                )
            except Exception as e:
                # Don't spam logs; just show a periodic error.
                print(f"Failed to broadcast survey_state: {e}")
            time.sleep(0.5 if state.get("votingOpen") else 1.5)

    def run(self):
        try:
            while not self.shutdown_event.is_set():
                time.sleep(0.25)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = AudienceSurveyDemo()
    demo.run()
