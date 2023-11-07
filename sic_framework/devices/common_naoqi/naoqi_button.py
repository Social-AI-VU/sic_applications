from sic_framework.core.component_python2 import SICComponent

from sic_framework import utils, SICComponentManager, SICMessage, SICRequest, \
    SICConfMessage, SICSensor

from sic_framework.core.connector import SICConnector

if utils.PYTHON_VERSION_IS_2:
    import qi


class NaoqiButtonMessage(SICMessage):
    def __init__(self, value):
        """
        Button values as reported on change by the ALTouch module
        http://doc.aldebaran.com/2-4/naoqi/sensors/altouch.html

        Examples:
        [[“Head/Touch/Middle”, True], [“ChestBoard/Button”, True]]
        [[“Head/Touch/Middle”, False]]
        :param value: The button value
        """
        super(NaoqiButtonMessage, self).__init__()
        self.value = value

class NaoqiButtonSensor(SICComponent):
    """
    NaoqiButtonSensor is a sensor that reads the robot's physical button and touch values from the ALMemory module.
    """
    def __init__(self, *args, **kwargs):
        super(NaoqiButtonSensor, self).__init__(*args, **kwargs)

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        # Connect to AL proxies
        self.memory_service = self.session.service("ALMemory")

        self.ids = []


    @staticmethod
    def get_conf():
        return SICConfMessage()

    @staticmethod
    def get_inputs():
        return []

    @staticmethod
    def get_output():
        return NaoqiButtonMessage

    def onTouchChanged(self, value):
        self.output_message(NaoqiButtonMessage(value))

    def start(self):
        super(NaoqiButtonSensor, self).start()

        self.touch = self.memory_service.subscriber("TouchChanged")
        id = self.touch.signal.connect(self.onTouchChanged)
        self.ids.append(id)


    def stop(self, *args):
        for id in self.ids:
            self.touch.signal.disconnect(id)
        super(NaoqiButtonSensor, self).stop()



class NaoqiButton(SICConnector):
    component_class = NaoqiButtonSensor


if __name__ == '__main__':
    SICComponentManager([NaoqiButtonSensor])
