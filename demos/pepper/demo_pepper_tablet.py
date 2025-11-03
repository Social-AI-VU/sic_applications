"""
Pepper Tablet Display Demo

This demo showcases the different types of content that can be displayed on Pepper's tablet:
1. External URLs (e.g., YouTube videos)
2. Direct image URLs
3. Direct video URLs
4. Local HTML pages (automatically uploaded to Pepper)

The tablet uses a webview that can display any web content accessible via URL.
Local content is automatically uploaded to Pepper's built-in web server via SCP.

Usage:
    python demo_pepper_tablet.py

Requirements:
    - Pepper robot connected to network
    - Update ROBOT_IP with your Pepper's IP address
    - SSH access to Pepper (uses default passwords)

Features:
    - Automatic file upload to Pepper's web server
    - No need for external HTTP server
    - Displays sample HTML with interactive buttons
"""

# External imports
import time
import os

# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Pepper

# Import message types
from sic_framework.devices.common_pepper.pepper_tablet import UrlMessage


# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
ROBOT_IP = "XXX"  # Replace with your Pepper's IP address

# Display duration for each demo (in seconds)
DISPLAY_DURATION = 10


# ─────────────────────────────────────────────────────────────────────────────
# Pepper Tablet Demo Application
# ─────────────────────────────────────────────────────────────────────────────
class PepperTabletDemo(SICApplication):
    """
    Pepper tablet demo application.
    
    Demonstrates how to display various types of content on Pepper's tablet:
    - External URLs (YouTube, websites)
    - Images (direct URLs)
    - Videos (direct URLs)
    - Local HTML content
    
    Usage:
        python demo_pepper_tablet.py
    
    Features:
    - Displays multiple types of web content
    - Demonstrates URL handling for different content types
    - Shows best practices for tablet interaction
    """
    
    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(PepperTabletDemo, self).__init__()
        
        # Demo-specific configuration
        self.robot_ip = ROBOT_IP
        self.display_duration = DISPLAY_DURATION
        
        # Robot instance
        self.pepper = None
        
        self.set_log_level(sic_logging.INFO)
        
        # Optional: Log files will only be written if set_log_file is called
        # self.set_log_file("/path/to/log/directory")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure Pepper robot."""
        self.logger.info("Starting Pepper Tablet Demo...")
        
        # Initialize Pepper
        self.logger.info("Connecting to Pepper at {}...".format(self.robot_ip))
        self.pepper = Pepper(self.robot_ip)
        
        self.logger.info("Robot initialized successfully")
    
    def display_content(self, url, description):
        """
        Display content on Pepper's tablet.
        
        Args:
            url (str): The URL to display
            description (str): Description of what's being displayed
        """
        self.logger.info("Displaying: {}".format(description))
        self.logger.info("URL: {}".format(url))
        
        try:
            self.pepper.tablet_display_url.request(UrlMessage(url))
            self.logger.info("Content loaded successfully")
            time.sleep(self.display_duration)
        except Exception as e:
            self.logger.error("Error displaying content: {}".format(e))
    
    def run(self):
        """Main application logic - cycles through different content types."""
        try:
            self.logger.info("Starting tablet content demonstrations...")
            self.logger.info("=" * 80)
            
            # ─────────────────────────────────────────────────────────────────────────────
            # 1. External URL: YouTube Video
            # ─────────────────────────────────────────────────────────────────────────────
            self.logger.info("\n1. EXTERNAL URL DEMO: YouTube Video")
            self.logger.info("-" * 80)
            youtube_url = "https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1"
            self.display_content(
                youtube_url,
                "YouTube video (embedded player with autoplay)"
            )
            
            # ─────────────────────────────────────────────────────────────────────────────
            # 2. Direct Image URL
            # ─────────────────────────────────────────────────────────────────────────────
            self.logger.info("\n2. IMAGE URL DEMO: Direct Image Display")
            self.logger.info("-" * 80)
            image_url = "https://picsum.photos/1280/800"  # Random placeholder image
            self.display_content(
                image_url,
                "High-resolution image (direct URL)"
            )
            
            # Alternative: Using a specific image
            specific_image = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/1200px-Cat03.jpg"
            self.display_content(
                specific_image,
                "Specific image from direct URL"
            )
            
            # ─────────────────────────────────────────────────────────────────────────────
            # 3. HTML Page with Multiple Images
            # ─────────────────────────────────────────────────────────────────────────────
            self.logger.info("\n3. WEBPAGE DEMO: Interactive Content")
            self.logger.info("-" * 80)
            
            # Example: Display a simple webpage
            webpage_url = "https://example.com"
            self.display_content(
                webpage_url,
                "Simple webpage (example.com)"
            )
            
            # ─────────────────────────────────────────────────────────────────────────────
            # 4. Video Content
            # ─────────────────────────────────────────────────────────────────────────────
            self.logger.info("\n4. VIDEO DEMO: Direct Video URL")
            self.logger.info("-" * 80)
            
            # Note: For direct video playback, the tablet browser needs to support the format
            # MP4 videos work best. For YouTube, use the embed URL format shown above.
            video_url = "https://www.w3schools.com/html/mov_bbb.mp4"
            self.display_content(
                video_url,
                "Direct video file (MP4)"
            )
            
            # ─────────────────────────────────────────────────────────────────────────────
            # 5. Local HTML Content (uploaded to Pepper)
            # ─────────────────────────────────────────────────────────────────────────────
            self.logger.info("\n5. LOCAL CONTENT DEMO: Custom HTML Page")
            self.logger.info("-" * 80)
            
            # Get the path to the sample HTML file
            demo_dir = os.path.dirname(os.path.abspath(__file__))
            html_file = os.path.join(demo_dir, "pepper_tablet_demo.html")
            
            if os.path.exists(html_file):
                self.logger.info("Uploading sample HTML file to Pepper's web server...")
                try:
                    # Upload the HTML file to Pepper and get the URL
                    tablet_url = self.pepper.upload_to_tablet(html_file)
                    
                    # Display the uploaded HTML page
                    self.display_content(
                        tablet_url,
                        "Custom HTML page (hosted on Pepper)"
                    )
                except Exception as e:
                    self.logger.error("Failed to upload HTML file: {}".format(e))
                    self.logger.info("Skipping local HTML demo")
            else:
                self.logger.warning("Sample HTML file not found at: {}".format(html_file))
                self.logger.info("You can create custom HTML files and upload them using:")
                self.logger.info("  url = pepper.upload_to_tablet('my_page.html')")
                self.logger.info("  pepper.tablet_display_url.request(UrlMessage(url))")
            
            # ─────────────────────────────────────────────────────────────────────────────
            # 6. Interactive Web Application
            # ─────────────────────────────────────────────────────────────────────────────
            self.logger.info("\n6. INTERACTIVE DEMO: Web Application")
            self.logger.info("-" * 80)
            
            # Example: Display an interactive web app
            interactive_url = "https://pepper-tablet-demo.netlify.app"  # Example URL
            self.logger.info("""
Interactive web applications can include:
- Touch-responsive buttons and controls
- Games and activities
- Forms and surveys
- Real-time data visualization
- Custom interfaces for your application

Note: The URL above is an example. Create your own web app and host it
to have full control over the tablet interface.
            """)
            
            # Uncomment to display an actual interactive app:
            # self.display_content(interactive_url, "Interactive web application")
            
            # ─────────────────────────────────────────────────────────────────────────────
            # Summary and Tips
            # ─────────────────────────────────────────────────────────────────────────────
            self.logger.info("\n" + "=" * 80)
            self.logger.info("DEMO COMPLETE")
            self.logger.info("=" * 80)
            self.logger.info("""
Tips for Pepper Tablet Development:

1. URL Requirements:
   - Must be accessible via HTTP/HTTPS
   - Local content can be uploaded directly to Pepper
   - Pepper must have network access to external URLs

2. Uploading Local Content:
   - Use pepper.upload_to_tablet() to upload HTML, images, videos
   - Files are hosted on Pepper at http://198.18.0.1/apps/webserver/
   - No need for external web server!
   - Example:
       url = pepper.upload_to_tablet('my_page.html')
       pepper.tablet_display_url.request(UrlMessage(url))

3. Supported Content:
   - HTML pages (full CSS/JavaScript support)
   - Images (JPEG, PNG, GIF, WebP)
   - Videos (MP4 recommended, use H.264 codec)
   - Embedded content (YouTube, Vimeo, etc.)

4. Best Practices:
   - Design for 1280x800 resolution (Pepper tablet size)
   - Use large, touch-friendly buttons (min 44x44px)
   - Test network latency for external content
   - Upload frequently used content to Pepper for better performance
   - Handle network failures gracefully

5. Advanced Features:
   - JavaScript can interact with page elements
   - Touch events work like mobile devices
   - Consider responsive design principles
   - Use WebSockets for real-time communication

6. Debugging:
   - Check Pepper's network connectivity
   - Verify URLs are accessible from Pepper's network
   - Test URLs in a regular browser first
   - Monitor tablet service logs on Pepper
            """)
            
        except KeyboardInterrupt:
            self.logger.info("Interrupt received. Stopping demo...")
        except Exception as e:
            self.logger.error("Error during demo: {}".format(e))
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of the application."""
        self.logger.info("Shutting down Pepper Tablet Demo...")
        
        try:
            # Optionally clear the tablet display
            # You could display a "goodbye" message or return to home screen
            self.logger.info("Demo complete")
            
        except Exception as e:
            self.logger.error("Error during shutdown: {}".format(e))
        
        # Call parent shutdown to clean up connectors
        super(PepperTabletDemo, self).shutdown()


# ─────────────────────────────────────────────────────────────────────────────
# Script entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Create and run the demo
    demo = PepperTabletDemo()
    demo.run()

