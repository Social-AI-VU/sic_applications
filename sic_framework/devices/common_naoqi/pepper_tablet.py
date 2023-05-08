import argparse
from sic_framework import SICComponentManager, SICService, SICMessage, SICConfMessage, utils
if utils.PYTHON_VERSION_IS_2:
    from naoqi import ALProxy
    import qi


# @dataclass
class NaoqiLoadUrl(SICMessage):
    def __init__(self, url):
        super(NaoqiLoadUrl, self).__init__()
        self.url = url



class NaoqiTabletConf(SICConfMessage):
    def __init__(self):
        self.ip = '127.0.0.1'
        self.port = 9559


# make it service because we don't want it to be notified if the url has received or not
class NaoqiTabletService(SICService):
    def __init__(self, *args, **kwargs):
        super(NaoqiTabletService, self).__init__(*args, **kwargs)

        self.session = qi.Session()
        self.session.connect('tcp://{}:{}'.format(self.params._ip, self.params.port))
        self.tablet_service = self.session.service('ALTabletService')

    @staticmethod
    def get_conf():
        return NaoqiTabletConf()

    @staticmethod
    def get_inputs():
        return [NaoqiLoadUrl]

    @staticmethod
    def get_output():
        return SICMessage

    def execute(self, message):
        # display a webview on a pepper's tablet given a url
        self.tablet_service.showWebview(message[NaoqiLoadUrl.id()].url)
        return SICMessage()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('robot_name')
    args = parser.parse_args()
    SICComponentManager([NaoqiTabletService], args.robot_name)
