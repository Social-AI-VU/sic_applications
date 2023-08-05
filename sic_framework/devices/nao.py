from __future__ import print_function

import argparse
import os
import time

import six

from sic_framework.core import utils, sic_redis
from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.devices.naoqi_shared import Naoqi, shared_naoqi_components



class Nao(Naoqi):
    """
    Wrapper for NAO device to easily access its components (connectors)
    """

    def __init__(self, ip, **kwargs):
        super(Nao, self).__init__(ip, username="nao", password="nao", **kwargs)
        self.auto_install()

        redis_hostname, _ = sic_redis.get_redis_db_ip_password()

        if redis_hostname == "127.0.0.1" or redis_hostname == "localhost":
            # get own public ip address for the device to use
            redis_hostname = utils.get_ip_adress()


        stop_cmd = """
        pkill -f "python2 nao.py"
        """

        start_cmd = """
        export PYTHONPATH=/opt/aldebaran/lib/python2.7/site-packages; \
        export LD_LIBRARY_PATH=/opt/aldebaran/lib/naoqi; \
        cd ~/framework/sic_framework/devices; \
        echo 'Starting SIC on NAOv6';\
        python2 nao.py --redis_ip={redis_host}; 
        """.format(redis_host=redis_hostname)

        self.ssh.exec_command(stop_cmd)
        time.sleep(.1)
        stdin, stdout, stderr = self.ssh.exec_command(start_cmd, get_pty=True)

        print("Starting SIC on NAOv6")

        # wait for SIC to start
        while True:
            line = stdout.readline()

            # empty line means command is done (which should not happen)
            if len(line) == 0:
                # flush the buffers
                print("".join(stdout.readlines()))
                print("".join(stderr.readlines()))
                raise RuntimeError("Remote SIC program has stopped unexpectedly")

            if "Started component manager" in line:
                print("Success")
                break


        print("TODO NO LOGGING OR ERROR HANDLING IS SET WHEN REMOTE PROCESS FAILS")



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis_ip', type=str, required=True,
                        help="IP address where Redis is running")
    parser.add_argument('--redis_pass', type=str,
                        help="The redis password")
    args = parser.parse_args()

    os.environ['DB_IP'] = args.redis_ip

    if args.redis_pass:
        os.environ['DB_PASS'] = args.redis_pass

    nao_components = shared_naoqi_components + [
        # todo,
    ]

    SICComponentManager(nao_components)
