import argparse
import os
import time

from sic_framework.core import utils
from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.devices.naoqi_shared import Naoqi, shared_naoqi_components

import paramiko

class Nao(Naoqi):
    """
    Wrapper for NAO device to easily access its components (connectors)
    """

    def __init__(self, ip, **kwargs):
        super(Nao, self).__init__(ip, **kwargs, username="nao", password="nao")
        self.auto_install()

        stop_cmd = """
        pkill -f "python2 nao.py"
        """

        start_cmd = """
        export PYTHONPATH=/opt/aldebaran/lib/python2.7/site-packages; \
        export LD_LIBRARY_PATH=/opt/aldebaran/lib/naoqi; \
        cd ~/framework/sic_framework/devices; \
        echo 'Starting SIC on NAOv6';\
        python2 nao.py --redis_ip={redis_host}; 
        """.format(redis_host=os.environ['DB_IP'])

        self.ssh.exec_command(stop_cmd)
        time.sleep(.1)
        self.ssh.exec_command(start_cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis_ip', type=str, required=True,
                        help="IP address where Redis is running")
    args = parser.parse_args()

    os.environ['DB_IP'] = args.redis_ip

    nao_components = shared_naoqi_components + [
        # todo,
    ]

    SICComponentManager(nao_components)
