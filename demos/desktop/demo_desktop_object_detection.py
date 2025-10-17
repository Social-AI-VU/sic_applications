# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging
from sic_framework.core import utils
from sic_framework.core import utils_cv2

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop

# Import the service(s) we will be using
from sic_framework.services.object_detection.object_detection import ObjectDetection, ObjectDetectionConf

# Import the configuration(s) for the components
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf

# Import the message type(s) we're using
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage,
    CompressedImageMessage,
)

# Queue for storing images
import queue

# Computer vision library for displaying images
import cv2


class ObjectDetectionDemo(SICApplication):
    """
    Desktop object detection demo application.

    IMPORTANT:
    Object-detection service needs to be running:
    1. pip install --upgrade social_interaction_cloud[object-detection]
        Note: on macOS you might need use quotes pip install --upgrade "social-interaction-cloud[...]"
    2. run-object-detection
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(ObjectDetectionDemo, self).__init__()
        
        # Demo-specific initialization
        # Queue for storing images
        self.imgs_buffer = queue.Queue(maxsize=1)
        # Store the latest detections
        self.latest_objects = []
        # Desktop device and camera component
        self.desktop = None
        self.desktop_cam = None
        # Object detection component
        self.object_det = None
        
        # Configure logging
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
        # Remove old image if buffer is full
        try:
            self.imgs_buffer.get_nowait()
        except queue.Empty:
            pass
        self.imgs_buffer.put(image_message.image)
    
    def on_objects(self, message: BoundingBoxesMessage):
        """
        Callback function for incoming object detection results.
        
        Args:
            message: The bounding boxes message containing detected objects.
        
        Returns:
            None
        """
        # Update latest detections
        self.latest_objects = message.bboxes
    
    def setup(self):
        """Initialize and configure the desktop camera and object detection service."""
        self.logger.info("Creating pipeline...")
        
        # Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image
        conf = DesktopCameraConf(fx=1.0, fy=1.0, flip=1)
        
        # initialize the device(s) we want to use with relevant configuration(s)
        self.desktop = Desktop(camera_conf=conf)
        
        self.logger.info("Starting desktop camera")
        # initialize the component(s) we want to use
        self.desktop_cam = self.desktop.camera
        
        self.logger.info("Setting up object detection service")
        # Configure object detection with frequency of N Hz (detections every 1/N seconds)
        obj_det_conf = ObjectDetectionConf(frequency=15.0)  # You can adjust this value
        # setup the service(s) we want to use, taking the output of the desktop camera as the input
        self.object_det = ObjectDetection(input_source=self.desktop_cam, conf=obj_det_conf)
        
        self.logger.info("Subscribing callback functions")
        
        # register the callback functions to act upon arrival of the relevant messages
        self.desktop_cam.register_callback(callback=self.on_image)
        self.object_det.register_callback(callback=self.on_objects)
    
    def run(self):
        """Main application loop."""
        self.logger.info("Starting main loop")
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    # Get latest image (non-blocking with timeout)
                    img = self.imgs_buffer.get(timeout=0.1)
                    
                    # Draw the latest detections on every frame
                    for obj in self.latest_objects:
                        utils_cv2.draw_bbox_on_image(obj, img)
                    
                    cv2.imshow("Object Detection", img)
                    cv2.waitKey(1)
                except queue.Empty:
                    # No new image, continue loop to check shutdown flag
                    continue
            
            self.logger.info("Cleaning up...")
            cv2.destroyAllWindows()
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            cv2.destroyAllWindows()
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = ObjectDetectionDemo()
    demo.run()
