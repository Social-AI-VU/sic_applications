from sic_framework.core.message_python2 import TextRequest
from sic_framework.services.verify_installation.verify_installation import InstallationVerifier

"""
This demo tests the installation of SIC on your machine.
Note that it only tests the installation of redis and SIC's basic sending and receiving of messages.

Don't forget to start redis in the framework folder with `redis-server conf/redis/redis.conf` in a separate terminal.
Don't forget to run `python verify_installation/verify_installation.py` in a separate terminal.
Then, run this file with `python verify_installation.py`

On success, "Installation successful!" is displayed in your terminal.
"""

verifier = InstallationVerifier()
response = verifier.request(TextRequest("Am I successful installed?"))
print(response.text)
