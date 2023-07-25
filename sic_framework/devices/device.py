from sic_framework.core import utils
from sic_framework.core.actuator_python2 import SICActuator
from sic_framework.core.connector import SICConnector


class SICDevice(object):
    """
    Abstract class to facilitate property initialization for SICConnector properties.
    This way components of a device can easily be used without initializing all device components manually.
    """

    def __init__(self, ip):
        self.ip = ip

        # TODO ping device manager to quickly fail if ip is incorrect

        self.connectors = dict()
        self.configs = dict()



    def _get_connector(self, component_connector):
        """
        Get the active connection the component, or initialize it if it is not yet connected to.

        :param component_connector: The component connector class to start, e.g. NaoCamera
        :return: SICConnector
        """

        assert issubclass(component_connector, SICConnector), "Component connector must be a SICConnector"

        if component_connector not in self.connectors:
            conf = self.configs.get(component_connector, None)

            try:
                self.connectors[component_connector] = component_connector(self.ip, conf=conf)
            except TimeoutError as e:
                raise TimeoutError("Could not connect to {} on device {}.".format(component_connector.component_class.get_component_name(), self.ip))
        return self.connectors[component_connector]

    """ja t
    example property:
    
    @property
    def top_camera(self):
        component = TopNaoCamera
        return self._get_connector(component)
    
    """