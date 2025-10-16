# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Nao
from sic_framework.devices.nao_stub import NaoStub

# Import configuration and message types
from sic_framework.devices.common_naoqi.naoqi_camera import NaoqiCameraConf
from sic_framework.core.message_python2 import CompressedImageMessage

# Import libraries necessary for the demo
import queue
import cv2


class NaoCameraDemo(SICApplication):
    """
    NAO camera demo application.
    Demonstrates how to use the NAO robot camera.
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(NaoCameraDemo, self).__init__()
        
        # Demo-specific initialization
        self.nao_ip = "XXX"
        self.nao = None
        self.imgs = queue.Queue()
        
        self.set_log_level(sic_logging.INFO)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/nao/logs")

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
        """Initialize and configure the NAO robot camera."""
        self.logger.info("Initializing NAO...")
        
        # Create camera configuration using vflip to flip the image vertically
        # See "NaoqiCameraConf" for more options like brightness, contrast, sharpness, etc
        conf = NaoqiCameraConf(vflip=1)
        
        # Initialize the NAO robot
        self.nao = Nao(ip=self.nao_ip, top_camera_conf=conf)
        
        self.logger.info("Registering callback...")
        self.nao.top_camera.register_callback(self.on_image)
    
    def run(self):
        """Main application loop."""
        self.logger.info("Starting demo...")
        
        try:
            while not self.shutdown_event.is_set():
                try:
                    img = self.imgs.get(timeout=0.1)
                    cv2.imshow("NAO Camera", img[..., ::-1])  # cv2 is BGR instead of RGB
                    cv2.waitKey(1)
                except queue.Empty:
                    continue
            
            cv2.destroyAllWindows()
            self.logger.info("Camera demo completed")
        except Exception as e:
            self.logger.error("Error: {}".format(e=e))
        finally:
            cv2.destroyAllWindows()
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = NaoCameraDemo()
    demo.run()
