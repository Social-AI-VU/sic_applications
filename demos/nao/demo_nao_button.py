"""
This script demonstrates how to use the Nao buttons.
"""

from sic_framework.devices import Nao
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# In case you want to use the logger with a neat format as opposed to logger.info statements.
app = SICApplication()
logger = app.get_app_logger()

# can be DEBUG, INFO, WARNING, ERROR, CRITICAL
app.set_log_level(sic_logging.DEBUG)

# Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
# app.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")

# Use the shutdown event as a loop condition.
shutdown_flag = app.get_shutdown_event()

def test_func(a):
    logger.info("Pressed: ", a.value)


nao = Nao(ip="XXX")

nao.buttons.register_callback(test_func)

while not shutdown_flag.is_set():
    pass  # Keep script alive