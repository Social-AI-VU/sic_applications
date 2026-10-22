# import basic SIC framework components
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging
from sic_framework.core.message_python2 import AudioRequest

# import device(s), service(s), and message(s) we will be using
from sic_framework.devices.reachy_mini import ReachyMiniDevice
from sic_framework.devices.common_reachy_mini.reachy_mini_speakers import ReachyMiniSpeakersConf
from sic_framework.devices.common_reachy_mini.reachy_mini_motion import (
    ReachyMiniAntennaRequest,
    ReachyMiniBodyYawRequest,
    ReachyMiniHeadRequest,
    ReachyMiniSetTargetRequest,
)
from sic_framework.devices.common_reachy_mini.reachy_mini_autonomous import (
    ReachyMiniAutonomousConf,
    ReachyMiniBreathingRequest,
    ReachyMiniHeadTrackingRequest,
    ReachyMiniListeningRequest,
    ReachyMiniSpeakingMovementRequest,
)

# import demo-specific modules
import math
import time
import wave
from os.path import abspath, dirname, join

from reachy_mini.utils import create_head_pose


class ReachyMiniAutonomousDemo(SICApplication):
    """
    Reachy Mini autonomous movement demo.

    Walks through all autonomous behaviours step by step and logs what you
    should see on the robot:

    1. Breathing at the neutral pose (on by default)
    2. Motion requests blending with breathing; the head stays where it is moved
    3. Streaming set-target requests
    4. Speaking movement (head wobble) while audio plays, and with it turned off
    5. Listening: antennas freeze and breathing pauses
    6. Head tracking, paused while the robot speaks
    7. Breathing off/on; a pose set while it is off is remembered
    8. wake_up() while the autonomous movement is running

    Uses ``example_media/audio/demo_audio.wav``, so no TTS service is needed.
    Set ``self.interactive = True`` to press Enter between steps.
    """

    def __init__(self):
        super(ReachyMiniAutonomousDemo, self).__init__()

        self.mini = None
        self.mini_ip = "XXX"
        # Set to True to press Enter before each step
        self.interactive = False

        self.set_log_level(sic_logging.INFO)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file_path("/path/to/log/directory")

        # Load environment variables
        self.load_env("../../conf/.env")

        self.setup()

    def _load_wav(self):
        """Load the demo WAV file and return (waveform_bytes, sample_rate)."""
        app_root = dirname(dirname(dirname(abspath(__file__))))
        wav_path = join(app_root, "example_media", "audio", "demo_audio.wav")

        with wave.open(wav_path, "rb") as wf:
            sample_rate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())

        return frames, sample_rate

    def setup(self):
        """Initialize the Reachy Mini device with the autonomous movement defaults."""
        self.waveform, self.sample_rate = self._load_wav()
        # Use the first 5 seconds of audio for each speech test (16-bit mono)
        self.speech = self.waveform[: self.sample_rate * 2 * 5]

        self.logger.info("Initializing Reachy Mini for autonomous movement demo...")
        self.mini = ReachyMiniDevice(
            mode="wireless",
            robot_ip=self.mini_ip,
            speakers_conf=ReachyMiniSpeakersConf(sample_rate=self.sample_rate),
            # These are the defaults, spelled out for clarity
            autonomous_conf=ReachyMiniAutonomousConf(
                speaking_movement=True, breathing=True, head_tracking=False,
            ),
        )

    def step(self, title, expect):
        """Announce a test step and what should happen on the robot."""
        self.logger.info("")
        self.logger.info("=== {} ===".format(title))
        self.logger.info("Expect: {}".format(expect))
        if self.interactive:
            input("Press Enter to start this step...")

    def speak(self):
        """Play the speech sample; blocks until playback is done."""
        self.mini.speakers.request(AudioRequest(self.speech, self.sample_rate))

    def autonomous(self, request):
        self.mini.autonomous.request(request)

    def run(self):
        """Main application logic."""
        try:
            # 1. Breathing at neutral
            self.step(
                "1. Breathing (default on)",
                "head upright at neutral, slowly bobbing up and down (5 mm, one breath "
                "per 10 s); antennas swaying in opposite directions",
            )
            time.sleep(12)

            # 2. Motion requests blend with breathing
            self.step(
                "2. Motion requests",
                "head turns left and looks down smoothly, then STAYS there while "
                "breathing resumes around that pose; antennas and body move too",
            )
            self.mini.motion.request(ReachyMiniHeadRequest(yaw=25, pitch=10, duration=1.0))
            time.sleep(5)
            self.mini.motion.request(ReachyMiniAntennaRequest(right=0.6, left=-0.6, duration=0.8))
            time.sleep(3)
            self.mini.motion.request(ReachyMiniBodyYawRequest(yaw=0.4, duration=1.0))
            self.mini.motion.request(ReachyMiniBodyYawRequest(yaw=0.0, duration=1.0))
            time.sleep(3)

            # 3. Streaming set-target requests
            self.step(
                "3. Streaming set targets",
                "head sweeps smoothly from side to side for 4 s; no breathing during "
                "the sweep, breathing returns shortly after it ends",
            )
            start = time.time()
            while time.time() - start < 4.0:
                yaw = 20 * math.sin(2 * math.pi * 0.5 * (time.time() - start))
                self.mini.motion.request(ReachyMiniSetTargetRequest(head=create_head_pose(yaw=yaw)))
                time.sleep(0.03)
            time.sleep(3)

            self.logger.info("Returning to the neutral pose")
            self.mini.motion.request(ReachyMiniHeadRequest(duration=1.0))
            self.mini.motion.request(ReachyMiniAntennaRequest(right=-0.1745, left=0.1745, duration=0.8))
            time.sleep(2)

            # 4. Speaking movement
            self.step(
                "4a. Speaking movement on (default)",
                "head wobbles along with the audio, in sync with the speech",
            )
            self.speak()
            time.sleep(2)

            self.step(
                "4b. Speaking movement off",
                "same audio, but the head no longer wobbles (only breathing)",
            )
            self.autonomous(ReachyMiniSpeakingMovementRequest(False))
            self.speak()
            self.autonomous(ReachyMiniSpeakingMovementRequest(True))
            time.sleep(2)

            # 5. Listening
            self.step(
                "5. Listening",
                "for 5 s the antennas freeze and breathing fades out (as if the user "
                "is talking); afterwards the antennas blend back and breathing resumes",
            )
            self.autonomous(ReachyMiniListeningRequest(True))
            time.sleep(5)
            self.autonomous(ReachyMiniListeningRequest(False))
            time.sleep(5)

            # 6. Head tracking
            self.step(
                "6a. Head tracking",
                "sit in front of the robot and move your head: it follows your face for 15 s",
            )
            self.autonomous(ReachyMiniHeadTrackingRequest(True))
            time.sleep(15)

            self.step(
                "6b. Head tracking while speaking",
                "while the audio plays the head holds still on you (only wobbling), "
                "then starts following your face again",
            )
            self.speak()
            time.sleep(8)
            self.autonomous(ReachyMiniHeadTrackingRequest(False))
            self.mini.motion.request(ReachyMiniHeadRequest(duration=1.0))
            time.sleep(2)

            # 7. Breathing off/on with a remembered pose
            self.step(
                "7. Breathing off and on",
                "breathing fades out and the robot goes completely still; the head "
                "then turns right; when breathing is turned back on it breathes "
                "there instead of jumping back to neutral",
            )
            self.autonomous(ReachyMiniBreathingRequest(False))
            time.sleep(4)
            self.mini.motion.request(ReachyMiniHeadRequest(yaw=-20, duration=1.0))
            time.sleep(3)
            self.autonomous(ReachyMiniBreathingRequest(True))
            time.sleep(8)

            # 8. wake_up while autonomous movement runs
            self.step(
                "8. wake_up()",
                "the wake-up animation plays undisturbed (back to neutral), then "
                "breathing resumes at the neutral pose",
            )
            self.mini.wake_up()
            time.sleep(8)

            self.logger.info("")
            self.logger.info("Autonomous movement demo complete")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = ReachyMiniAutonomousDemo()
    demo.run()
