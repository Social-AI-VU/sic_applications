import time

from sic_framework import SICComponentManager, SICService, SICMessage, sic_logging
from sic_framework.core.actuator_python2 import SICActuator
from sic_framework.core.message_python2 import SICRequest


class TestSlowActionRequest(SICRequest):
    def __init__(self, text):
        super().__init__()
        self.text = text


class SlowActionTest(SICActuator):
    def __init__(self, *args, **kwargs):
        super(SlowActionTest, self).__init__(*args, **kwargs)

    @staticmethod
    def get_inputs():
        return [TestSlowActionRequest]

    @staticmethod
    def get_output():
        return SICMessage

    def execute(self, input):
        self.logger.info("RUNNING!")
        time.sleep(5)
        self.logger.info("message! {}".format(input.text))
        time.sleep(1)
        self.logger.info("Action took six seconds!")
        return SICMessage()


if __name__ == "__main__":
    SICComponentManager([SlowActionTest], "nao")

    # from threading import Thread
    #
    # thread = Thread(target=StreamImg)
    # thread.start()
    #
    # thread.join()
    #
    # pass
