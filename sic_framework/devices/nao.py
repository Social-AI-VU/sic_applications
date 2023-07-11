import argparse
import os

from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.devices.naoqi_shared import Naoqi, shared_naoqi_components


class Nao(Naoqi):
    """
    Wrapper for NAO device to easily access its components (connectors)
    """


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
