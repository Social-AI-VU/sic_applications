from sic_framework import SICComponentManager, SICMessage, utils
from sic_framework.core.connector import SICConnector
from sic_framework.core.component_python2 import SICComponent

if utils.PYTHON_VERSION_IS_2:
    from naoqi import ALProxy
    import qi

class UrlMessage(SICMessage):
    def __init__(self, url):
        super(UrlMessage, self).__init__()
        self.url = url

class NaoqiTabletComponent(SICComponent):
    def __init__(self, *args, **kwargs):
        super(NaoqiTabletComponent, self).__init__(*args, **kwargs)

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')
        self.tablet_service = self.session.service('ALTabletService')


    @staticmethod
    def get_inputs():
        return [UrlMessage]

    @staticmethod
    def get_output():
        return SICMessage


    def on_message(self, message):
        # print("url is ", message.url)
        self.tablet_service.showWebview(message.url)


class NaoqiTablet(SICConnector):
    component_class = NaoqiTabletComponent

if __name__ == '__main__':
    SICComponentManager([NaoqiTabletComponent])
