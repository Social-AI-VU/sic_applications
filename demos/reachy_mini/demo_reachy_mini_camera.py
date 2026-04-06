# import libraries for the demo
import queue
import cv2

# import SIC framework components
from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication

# import devices, services, and message types
from sic_framework.devices.reachy_mini import ReachyMiniDevice
from sic_framework.core.message_python2 import CompressedImageMessage

class ReachyMiniCameraDemo(SICApplication):
    """
    Reachy Mini camera demo.

    Connects to a Reachy Mini, subscribes to the camera sensor, and displays
    the incoming camera feed using OpenCV.
    """

    def __init__(self):
        super(ReachyMiniCameraDemo, self).__init__()

        self.imgs = queue.Queue(maxsize=1)
        self.mini = None

        self.set_log_level(sic_logging.INFO)
        # set log file path if needed
        # self.set_log_file_path("/path/to/logs")


        # Load environment variables
        self.load_env("../../conf/.env")
        
        self.setup()

    def on_image(self, image_message: CompressedImageMessage):
        try:
            while not self.imgs.empty():
                self.imgs.get_nowait()
        except queue.Empty:
            pass
        try:
            self.imgs.put_nowait(image_message.image)
        except queue.Full:
            pass

    def setup(self):
        """Initialize the Reachy Mini device and subscribe to the camera."""
        self.logger.info("Initializing Reachy Mini for camera demo...")
        self.mini = ReachyMiniDevice(mode="sim")
        self.mini.camera.register_callback(callback=self.on_image)

    def run(self):
        """Main application loop."""
        self.logger.info("Starting main loop (press 'q' to quit)")

        try:
            while not self.shutdown_event.is_set():
                try:
                    img = self.imgs.get(timeout=0.1)
                    cv2.imshow("Reachy Mini Camera", img)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                except queue.Empty:
                    continue
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            cv2.destroyAllWindows()
            self.shutdown()


if __name__ == "__main__":
    demo = ReachyMiniCameraDemo()
    demo.run()
