# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device we will be using
from sic_framework.devices.desktop import Desktop

# Import the configuration for the component
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf

# Import the message type we're using
from sic_framework.core.message_python2 import CompressedImageMessage

# Queue for storing images
import queue

# Computer vision library for displaying images
import cv2


class CameraDemo(SICApplication):
    """
    Desktop camera demo application.
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(CameraDemo, self).__init__()
        
        # Demo-specific initialization
        self.imgs = queue.Queue()
        self.desktop = None
        self.desktop_cam = None
        
        # Configure logging
        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demoss/desktop/logs")
        
        self.setup()
    
    def on_image(self, image_message: CompressedImageMessage):
        """
        Callback function for incoming camera images.
        
        Args:
            image_message: The incoming camera image message.
        
        Returns:
            None
        """
        self.imgs.put(image_message.image)
    
    def setup(self):
        """Initialize and configure the desktop camera."""
        # Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image (set to -1 to flip)
        conf = DesktopCameraConf(fx=1.0, fy=1.0, flip=1)

        # initialize the device we want to use with relevant configuration
        self.desktop = Desktop(camera_conf=conf)

        # initialize the component we want to use
        self.desktop_cam = self.desktop.camera
        
        self.logger.info("Subscribing callback function")
        # register the callback function to act upon arrival of the relevant message
        self.desktop_cam.register_callback(callback=self.on_image)
    
    def run(self):
        """Main application loop."""
        self.logger.info("Starting main loop")
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    # Use timeout to make the queue operation non-blocking
                    img = self.imgs.get(timeout=0.1)  # 100ms timeout
                    cv2.imshow("Camera Feed", img)
                    cv2.waitKey(1)
                except queue.Empty:
                    # No new image, continue loop to check shutdown flag
                    continue
            self.logger.info("Cleaning up...")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            cv2.destroyAllWindows()
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = CameraDemo()
    demo.run()
