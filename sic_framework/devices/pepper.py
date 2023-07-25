import argparse
import os
import time

from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.devices.common_naoqi.naoqi_camera import StereoPepperCamera, DepthPepperCamera, \
    DepthPepperCameraSensor, StereoPepperCameraSensor
from sic_framework.devices.naoqi_shared import shared_naoqi_components, Naoqi


class Pepper(Naoqi):
    """
    Wrapper for Pepper device to easily access its components (connectors)
    """

    def __init__(self, ip,
                 stereo_camera_conf=None,
                 depth_camera_conf=None,
                 **kwargs):
        super(Pepper, self).__init__(ip, **kwargs, username="nao", password="nao")

        self.configs[StereoPepperCamera] = stereo_camera_conf
        self.configs[DepthPepperCamera] = depth_camera_conf

        self.auto_install()

        stop_cmd = """
        pkill -f "python2 pepper.py"
        """

        start_cmd = """
        export PYTHONPATH=/opt/aldebaran/lib/python2.7/site-packages; \
        export LD_LIBRARY_PATH=/opt/aldebaran/lib/naoqi; \
        cd ~/framework/sic_framework/devices; \
        echo 'Starting SIC on NAOv6';\
        python2 pepper.py --redis_ip={redis_host}; 
        """.format(redis_host=os.environ['DB_IP'])

        self.ssh.exec_command(stop_cmd)
        time.sleep(.1)
        self.ssh.exec_command(start_cmd)

    @property
    def stereo_camera(self):
        return self._get_connector(StereoPepperCamera)

    @property
    def depth_camera(self):
        return self._get_connector(DepthPepperCamera)

    # @property
    # def tablet_load_url(self):
    #     return self._get_connector(NaoqiTablet)

    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis_ip', type=str, required=True,
                        help="IP address where Redis is running")
    args = parser.parse_args()

    os.environ['DB_IP'] = args.redis_ip


    pepper_components = shared_naoqi_components + [
        # NaoqiLookAtComponent,
        # NaoqiTabletService,
        DepthPepperCameraSensor,
        StereoPepperCameraSensor,
    ]

    SICComponentManager(pepper_components)
