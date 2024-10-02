from sic_old.factory import SICfactory

from depth_estimation_service import DepthEstimationService


class DepthEstimationFactory(SICfactory):
    def __init__(self):
        super().__init__()

    def get_connection_channel(self):
        return 'depth_estimation'

    def create_service(self, connect, identifier, disconnect):
        return DepthEstimationService(connect, identifier, disconnect)


if __name__ == '__main__':
    factory = DepthEstimationFactory()
    factory.run()
