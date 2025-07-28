"""
Boilerplate setup for SIC applications.
"""

from sic_framework.core import utils
from sic_framework.core import sic_logging
from dotenv import load_dotenv
import os

# Initialize logging
sic_logging.set_log_level(sic_logging.INFO)

# set log file path (relative to the sic_app.py file)
LOG_PATH = "../sic_logs/"
# sic logging will automatically create the log directory if it doesn't exist
sic_logging.set_log_file_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), LOG_PATH))

# load in any environment variables from the .env file
load_dotenv("../.env")