# import libraries for the demo
import queue
import cv2

# import SIC framework components
from sic_framework.core import sic_logging, utils_cv2
from sic_framework.core.sic_application import SICApplication

# import devices, services, and message types
from sic_framework.devices.reachy_mini import ReachyMiniDevice
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage,
    CompressedImageMessage,
)
from sic_framework.services.face_detection.face_detection import FaceDetection


class ReachyMiniFaceDetectionDemo(SICApplication):
    """
    Reachy Mini camera with face detection demo application.
    
    IMPORTANT:
    face-detection service needs to be running:
    1. pip install --upgrade social-interaction-cloud[face-detection]
    2. run-face-detection
    
    """

    def __init__(self):
        super(ReachyMiniFaceDetectionDemo, self).__init__()

        self.imgs_buffer = queue.Queue(maxsize=1)
        self.faces_buffer = queue.Queue(maxsize=1)
        self.mini = None
        self.face_det = None

        self.set_log_level(sic_logging.INFO)
        # set log file path if needed
        # self.set_log_file_path("/path/to/logs")


        # Load environment variables
        self.load_env("../../conf/.env")
        
        self.setup()

    def on_image(self, image_message: CompressedImageMessage):
        self.imgs_buffer.put(image_message.image)

    def on_faces(self, message: BoundingBoxesMessage):
        self.faces_buffer.put(message.bboxes)

    def setup(self):
        """Initialize the Reachy Mini device and face detection pipeline."""
        self.logger.info("Creating pipeline...")

        self.mini = ReachyMiniDevice(mode="sim")

        self.logger.info("Setting up face detection service")
        self.face_det = FaceDetection(input_source=self.mini.camera)

        self.logger.info("Subscribing callback functions")
        self.mini.camera.register_callback(callback=self.on_image)
        self.face_det.register_callback(callback=self.on_faces)

    def run(self):
        """Main application loop."""
        self.logger.info("Starting main loop")

        try:
            while not self.shutdown_event.is_set():
                try:
                    img = self.imgs_buffer.get(timeout=0.1)
                    faces = self.faces_buffer.get(timeout=0.1)

                    for face in faces:
                        utils_cv2.draw_bbox_on_image(face, img)
                    cv2.imshow("Reachy Mini Face Detection", img)
                    cv2.waitKey(1)
                except queue.Empty:
                    continue
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            cv2.destroyAllWindows()
            self.shutdown()


if __name__ == "__main__":
    demo = ReachyMiniFaceDetectionDemo()
    demo.run()
