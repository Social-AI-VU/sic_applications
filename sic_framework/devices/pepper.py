import argparse
import os

from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.devices.common_naoqi.naoqi_camera import StereoPepperCamera, DepthPepperCamera, \
    DepthPepperCameraSensor, StereoPepperCameraSensor
from sic_framework.devices.nao import shared_naoqi_components, Naoqi


class Pepper(Naoqi):
    def __init__(self, *args,
                 stereo_camera_conf=None,
                 depth_camera_conf=None,
                 **kwargs
                 ):
        super().__init__(*args, **kwargs)

        self.configs[StereoPepperCamera] = stereo_camera_conf
        self.configs[DepthPepperCamera] = depth_camera_conf

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
