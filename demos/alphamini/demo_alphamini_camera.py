"""
Alphamini camera demo.

This demo connects to an Alphamini running SIC, subscribes to the Mini camera
component (`MiniCameraSensor`), and displays the incoming camera feed using OpenCV.

Requirements:
- SIC must be installed and running on the Alphamini (handled by `Alphamini`).
- The Android `camera_app` must be running on the Alphamini and streaming JPEG
  frames to the port configured in `MiniCameraConf` (default: 6001).
"""

import queue
import time

import cv2

from sic_framework.core import sic_logging
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.core.sic_application import SICApplication
from sic_framework.devices.alphamini import Alphamini
from sic_framework.devices.common_mini.mini_camera import MiniCameraConf


class AlphaminiCameraDemo(SICApplication):
    """
    Alphamini camera demo application.
    """

    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(AlphaminiCameraDemo, self).__init__()

        # Queue for incoming images
        self.imgs = queue.Queue(maxsize=1)

        # Device and connector handles
        self.mini = None
        self.mini_cam = None

        # Connection parameters (fill these in before running)
        self.mini_ip = "10.0.0.155"
        self.mini_id = "00268"
        self.mini_password = "alphago"
        self.redis_ip = "10.0.0.184"

        # Configure logging
        self.set_log_level(sic_logging.DEBUG)

        # Optionally enable file logging by uncommenting and setting a valid path:
        # self.set_log_file("/path/to/log/directory")

        self.setup()

    def on_image(self, image_message: CompressedImageMessage):
        """
        Callback function for incoming camera images.
        """
        # Compute end-to-end latency if the capture timestamp is present
        capture_ts = getattr(image_message, "image_timestamp", None)
        if capture_ts is not None:
            now = time.time()
            latency_ms = (now - capture_ts) * 1000.0
            img = image_message.image
            size_bytes = img.nbytes if hasattr(img, "nbytes") else None
            self.logger.info(
                "Received image message "
                "(latency ~{latency:.1f} ms, shape={shape}, size={size} bytes)".format(
                    latency=latency_ms,
                    shape=getattr(img, "shape", None),
                    size=size_bytes,
                )
            )
        else:
            img = image_message.image
            size_bytes = img.nbytes if hasattr(img, "nbytes") else None
            self.logger.info(
                "Received image message (shape={shape}, size={size} bytes)".format(
                    shape=getattr(img, "shape", None), size=size_bytes
                )
            )
        # Always keep only the most recent frame to avoid lag.
        try:
            while not self.imgs.empty():
                self.imgs.get_nowait()
        except queue.Empty:
            pass

        try:
            self.imgs.put_nowait(image_message.image)
        except queue.Full:
            # In case of race, just drop; a newer frame will arrive soon.
            pass

    def setup(self):
        """Initialize and configure the Alphamini camera."""
        # Configure the Mini camera TCP server (keep defaults unless you changed the Android app port)
        cam_conf = MiniCameraConf(
            port=6001,
            # Example tuning for latency vs quality:
            # - Smaller resolution via scale reduces bandwidth and CPU.
            # - send_fps caps how many frames per second we push into SIC/Redis.
            scale=0.4,  # use half the default width/height
            send_fps=5.0,
            jpeg_quality=100,
        )

        self.logger.info("Initializing Alphamini for camera demo...")
        self.mini = Alphamini(
            ip=self.mini_ip,
            mini_id=self.mini_id,
            mini_password=self.mini_password,
            redis_ip=self.redis_ip,
            camera_conf=cam_conf,
            dev_test=True,
            # test_repo="/Users/landon/Desktop/SAIL/social-interaction-cloud",
        )

        # Get camera connector
        self.mini_cam = self.mini.camera

        self.logger.info("Subscribing camera callback")
        self.mini_cam.register_callback(callback=self.on_image)

    def run(self):
        """Main application loop."""
        self.logger.info("Starting Alphamini camera main loop (press 'q' to quit)")

        try:
            while True:
                # Block until we get the next image
                img = self.imgs.get()
                cv2.imshow("Alphamini Camera Feed", img)

                # Exit when user presses 'q'
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        except Exception as e:
            self.logger.error("Exception in camera demo: {}".format(e))
        finally:
            cv2.destroyAllWindows()
            self.shutdown()


if __name__ == "__main__":
    demo = AlphaminiCameraDemo()
    demo.run()

