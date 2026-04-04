# Import basic preliminaries
import queue
import time
import cv2

from sic_framework.core import sic_logging
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.core.sic_application import SICApplication

# Import the device we will be using
from sic_framework.devices.alphamini import Alphamini
from sic_framework.devices.common_mini.mini_camera import MiniCameraConf
from pathlib import Path
from dotenv import load_dotenv


class AlphaminiCameraDemo(SICApplication):
    """
    Alphamini camera demo.

    This demo connects to an Alphamini running SIC, subscribes to the Mini camera
    component (`MiniCameraSensor`), and displays the incoming camera feed using OpenCV.

    Requirements:
    - SIC must be installed and running on the Alphamini (handled by `Alphamini`).
    - The Android `camera_app` must be running on the Alphamini and streaming JPEG
    frames to the port configured in `MiniCameraConf` (default: 6001).
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
        self.mini_ip = "XXX"
        self.mini_id = "XXX"
        self.mini_password = "XXX"
        self.redis_ip = "XXX"

        # Configure logging
        self.set_log_level(sic_logging.INFO)

        # Optionally enable file logging by uncommenting and setting a valid path:
        # self.set_log_file("/path/to/log/directory")


        # Load environment variables
        env_path = Path(__file__).parent.parent.parent / "conf" / ".env"
        load_dotenv(env_path)
        
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
            self.logger.debug(
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
            self.logger.debug(
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
        """
        Initialize and configure the Alphamini camera.

        Resolution control works as follows (implemented inside the Android ``CameraActivity``):

        - It starts from the camera's preferred preview size.
        - If ``MiniCameraConf.target_width`` / ``target_height`` are both > 0,
          that pair is taken as the desired base size.
        - Then ``MiniCameraConf.scale`` is applied on top of that desired size
          (width and height are multiplied by scale) before snapping to the
          nearest supported preview size.

        In other words, ``target_width`` / ``target_height`` and ``scale`` can
        be combined; ``scale`` does not disable the ``target_*`` fields, it
        scales their effect.
        """
        # Configure the Mini camera TCP server (keep defaults unless you changed the Android app port).
        cam_conf = MiniCameraConf(
            port=6001,
            # Example tuning for latency vs quality:
            # - Smaller resolution via scale reduces bandwidth and CPU.
            # - send_fps caps how many frames per second we push into SIC/Redis.
            scale=0.25,  # use a quarter of the default width/height
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

