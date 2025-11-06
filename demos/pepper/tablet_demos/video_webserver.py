"""
Simple Video Web Server

This is a standalone web server that serves and displays a video file.

Usage:
    python video_webserver.py

Requirements:
    - demo_video.mp4 file in the same directory
    - you can replace the video file with your own video file by changing the VIDEO_FILE variable.
    - If you want to display the video on Pepper's tablet, the video must have a width of 1080 pixels or less.

How it works:
    1. Starts an HTTP server on port 8000
    2. Serves a video player HTML page
    3. Serves the video file
    4. Open http://localhost:8000 in your browser to watch the video
    5. Other devices on the network can access it using your local IP address
"""

import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from sic_framework.core import utils


# ────────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────────
HTTP_PORT = 8000
VIDEO_FILE = "demo_video.mp4"


# ─────────────────────────────────────────────────────────────────────────────
# Custom HTTP Handler with Range Request Support
# ─────────────────────────────────────────────────────────────────────────────
class VideoHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP handler that supports range requests for video streaming."""
    
    def log_error(self, format, *args):
        """Suppress BrokenPipeError and favicon errors."""
        if "Broken pipe" in str(args) or "favicon.ico" in str(args):
            pass
        else:
            super().log_error(format, *args)
    
    def send_head(self):
        """Override to add proper range request support for video streaming."""
        # Handle root path - serve index.html
        if self.path == '/':
            self.path = '/index.html'
        
        path = self.translate_path(self.path)
        
        # Check if file exists
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None
        
        try:
            fs = os.fstat(f.fileno())
            file_len = fs.st_size
            
            # Check if client requested a range
            range_header = self.headers.get('Range')
            
            if range_header:
                # Parse range header (e.g., "bytes=0-1023")
                try:
                    ranges = range_header.strip().lower().replace('bytes=', '').split('-')
                    start = int(ranges[0]) if ranges[0] else 0
                    end = int(ranges[1]) if ranges[1] else file_len - 1
                    
                    # Validate range
                    if start >= file_len:
                        self.send_error(416, "Requested Range Not Satisfiable")
                        f.close()
                        return None
                    
                    end = min(end, file_len - 1)
                    content_length = end - start + 1
                    
                    # Send 206 Partial Content response
                    self.send_response(206)
                    self.send_header("Content-Type", self.guess_type(path))
                    self.send_header("Content-Range", "bytes {}-{}/{}".format(start, end, file_len))
                    self.send_header("Content-Length", str(content_length))
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()
                    
                    # Seek to start position
                    f.seek(start)
                    return f
                    
                except (ValueError, IndexError):
                    pass
            
            # No range request - send full file
            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(path))
            self.send_header("Content-Length", str(file_len))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            return f
            
        except Exception as e:
            f.close()
            self.send_error(500, "Internal Server Error: {}".format(str(e)))
            return None
    
    def copyfile(self, source, outputfile):
        """Copy file data, handling partial content properly."""
        try:
            range_header = self.headers.get('Range')
            if range_header:
                ranges = range_header.strip().lower().replace('bytes=', '').split('-')
                start = int(ranges[0]) if ranges[0] else 0
                end = int(ranges[1]) if ranges[1] else None
                
                if end:
                    length = end - start + 1
                    chunk_size = 64 * 1024
                    remaining = length
                    while remaining > 0:
                        chunk = source.read(min(chunk_size, remaining))
                        if not chunk:
                            break
                        outputfile.write(chunk)
                        remaining -= len(chunk)
                else:
                    super().copyfile(source, outputfile)
            else:
                super().copyfile(source, outputfile)
        except BrokenPipeError:
            pass
        except Exception:
            pass
    
    def do_GET(self):
        """Handle GET requests with proper error handling."""
        try:
            f = self.send_head()
            if f:
                try:
                    self.copyfile(f, self.wfile)
                finally:
                    f.close()
        except BrokenPipeError:
            pass
        except Exception as e:
            if "Broken pipe" not in str(e):
                self.log_error("Error: %s", str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────
def create_video_html(video_filename):
    """Create an HTML page with just a video player."""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #000;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            overflow: hidden;
        }}
        video {{
            max-width: 100%;
            max-height: 100%;
            width: auto;
            height: auto;
        }}
    </style>
</head>
<body>
    <video controls autoplay muted>
        <source src="{}" type="video/mp4">
        <source src="{}" type="video/quicktime">
        Your browser does not support the video tag.
    </video>
</body>
</html>""".format(video_filename, video_filename)
    
    return html_content


# ─────────────────────────────────────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────────────────────────────────────
def main():
    """Start the video web server."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check if video file exists
    if not os.path.exists(VIDEO_FILE):
        print("ERROR: Video file '{}' not found!".format(VIDEO_FILE))
        print("Please ensure the video file is in the same directory as this script.")
        return
    
    # Get video file size
    file_size_mb = os.path.getsize(VIDEO_FILE) / (1024 * 1024)
    
    # Create index.html with video player
    html_content = create_video_html(VIDEO_FILE)
    with open('index.html', 'w') as f:
        f.write(html_content)
    
    # Get local IP address using SIC framework utils
    local_ip = utils.get_ip_adress()
    
    print("=" * 70)
    print("Simple Video Web Server")
    print("=" * 70)
    print("Video file: {}".format(VIDEO_FILE))
    print("Video size: {:.2f} MB".format(file_size_mb))
    print("")
    print("Starting HTTP server on port {}...".format(HTTP_PORT))
    
    # Create and start the HTTP server
    server = HTTPServer(("", HTTP_PORT), VideoHTTPRequestHandler)
    
    print("")
    print("=" * 70)
    print("Server is running!")
    print("=" * 70)
    print("")
    print("Access the video:")
    print("")
    print("  Video player page (HTML5):")
    print("    Local:   http://localhost:{}".format(HTTP_PORT))
    print("    Network: http://{}:{}".format(local_ip, HTTP_PORT))
    print("")
    print("  Direct video file URL:")
    print("    Local:   http://localhost:{}/{}".format(HTTP_PORT, VIDEO_FILE))
    print("    Network: http://{}:{}/{}".format(local_ip, HTTP_PORT, VIDEO_FILE))
    print("")
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server.shutdown()
        print("Server stopped.")


if __name__ == "__main__":
    main()

