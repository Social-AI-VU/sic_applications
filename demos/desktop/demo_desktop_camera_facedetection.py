# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging
from sic_framework.core import utils
from sic_framework.core import utils_cv2

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop

# Import the service(s) we will be using
from sic_framework.services.face_detection.face_detection import FaceDetection

# Import the configuration(s) for the components
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf

# Import the message type(s) we're using
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage,
    CompressedImageMessage,
)

# Queue for storing images and detection results
import queue

# Computer vision library for displaying images
import cv2


class FaceDetectionDemo(SICApplication):
    """
    This demo recognizes faces from your webcam and displays the result on your laptop.

    IMPORTANT
    face-detection service needs to be running:
    1. run-face-detection
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(FaceDetectionDemo, self).__init__()
        
        # Demo-specific initialization
        # Queue for storing images and detection results
        self.imgs_buffer = queue.Queue(maxsize=1)
        self.faces_buffer = queue.Queue(maxsize=1)
        # Desktop device and camera component
        self.desktop = None
        self.desktop_cam = None
        # Face detection component
        self.face_dec = None

        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")
                
        self.setup()
    
    def on_image(self, image_message: CompressedImageMessage):
        """
        Callback function for incoming camera images.
        
        Args:
            image_message: The incoming camera image message.
        
        Returns:
            None
        """
        self.imgs_buffer.put(image_message.image)
    
    def on_faces(self, message: BoundingBoxesMessage):
        """
        Callback function for incoming face detection results.
        
        Args:
            message: The bounding boxes message containing detected faces.
        
        Returns:
            None
        """
        self.faces_buffer.put(message.bboxes)
    
    def setup(self):
        """Initialize and configure the desktop camera and face detection service."""
        self.logger.info("Creating pipeline...")
        
        # Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image
        conf = DesktopCameraConf(fx=1.0, fy=1.0, flip=1)
        
        # initialize the device(s) we want to use with relevant configuration(s)
        self.desktop = Desktop(camera_conf=conf)
        
        self.logger.info("Starting desktop camera")
        # initialize the component(s) we want to use
        self.desktop_cam = self.desktop.camera
        
        self.logger.info("Setting up face detection service")
        # setup the service(s) we want to use, taking the output of the desktop camera as the input
        self.face_dec = FaceDetection(input_source=self.desktop_cam)
        
        self.logger.info("Subscribing callback functions")
        
        # register the callback functions to act upon arrival of the relevant messages
        self.desktop_cam.register_callback(callback=self.on_image)
        self.face_dec.register_callback(callback=self.on_faces)
    
    def run(self):
        """Main application loop."""
        self.logger.info("Starting main loop")
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    # Use timeout to make queue operations non-blocking
                    img = self.imgs_buffer.get(timeout=0.1)  # 100ms timeout
                    faces = self.faces_buffer.get(timeout=0.1)
                    
                    for face in faces:
                        utils_cv2.draw_bbox_on_image(face, img)
                    
                    cv2.imshow("Face Detection", img)
                    cv2.waitKey(1)
                except queue.Empty:
                    # No new data, continue loop to check shutdown flag
                    continue
            cv2.destroyAllWindows()
            self.logger.info("Cleaning up...")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            cv2.destroyAllWindows()
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = FaceDetectionDemo()
    demo.run()
