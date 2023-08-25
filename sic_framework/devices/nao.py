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
        super(Nao, self).__init__(ip, robot_type="nao", username="nao", passwords="nao", **kwargs)




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
