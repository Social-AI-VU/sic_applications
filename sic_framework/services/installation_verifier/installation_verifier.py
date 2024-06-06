from sic_framework import SICComponentManager
from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import TextMessage, TextRequest


class InstallationVerifierComponent(SICComponent):
    """
    Verify SIC installation
    """

    def __init__(self, *args, **kwargs):
        super(InstallationVerifierComponent, self).__init__(*args, **kwargs)

    @staticmethod
    def get_inputs():
        return [TextRequest, TextMessage]

    @staticmethod
    def get_output():
        return TextMessage

    @staticmethod
    def do_pong():
        """
        :return: TextMessage
        """
        return TextMessage("Installation successful!")

    def on_message(self, message):
        output = self.do_pong()
        self.output_message(output)

    def on_request(self, request):
        return self.do_pong()


class InstallationVerifier(SICConnector):
    component_class = InstallationVerifierComponent


if __name__ == '__main__':
    # Request the service to start using the SICServiceManager on this device
    SICComponentManager([InstallationVerifierComponent])
