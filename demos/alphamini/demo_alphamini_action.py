
"""
This demo shows how to make Nao perform predefined postures and animations.
"""

from sic_framework.devices.alphamini import Alphamini
from sic_framework.devices.common_mini.mini_animation import MiniActionRequest
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Create the SICApplication instance to be able to use the logger and the shutdown event
app = SICApplication()
logger = app.get_app_logger()
app.set_log_level(sic_logging.DEBUG)

try:
    logger.info("Initializing Alphamini...")
    mini = Alphamini(ip="XXX", mini_id="000XXX", mini_password="mini", redis_ip="XXX")

    logger.info("Performing action...")
    mini.animation.request(MiniActionRequest("018"))

except Exception as e:
    logger.error("Exception: {}".format(e))
finally:
    app.shutdown()
