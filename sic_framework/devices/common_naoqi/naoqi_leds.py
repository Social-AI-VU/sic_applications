from sic_framework import utils, SICComponentManager, SICMessage, SICRequest, \
    SICConfMessage

from sic_framework import SICActuator
from sic_framework.core.connector import SICConnector

if utils.PYTHON_VERSION_IS_2:
    import qi


class NaoLEDRequest(SICRequest):
    """
    Turn LED(s) on or off
    name - RGB LED or Group name (string), see http://doc.aldebaran.com/2-5/naoqi/sensors/alleds.html
    value - boolean to turn on/off
    """
    def __init__(self, name, value):
        super(NaoLEDRequest, self).__init__()
        self.name = name
        self.value = value


class NaoSetIntensityRequest(SICRequest):
    """
    Change intensity of LED(s)
    name - RGB LED or Group name (string), see http://doc.aldebaran.com/2-5/naoqi/sensors/alleds.html
    intensity - float [0,1] representing intensity value
    """
    def __init__(self, name, intensity):
        super(NaoSetIntensityRequest, self).__init__()
        self.name = name
        self.intensity = intensity


class NaoGetIntensityRequest(SICRequest):
    """
    Gets the intensity of LED(s)
    name - RGB LED or Group name (string), see http://doc.aldebaran.com/2-5/naoqi/sensors/alleds.html
    """
    def __init__(self, name):
        super(NaoGetIntensityRequest, self).__init__()
        self.name = name


class NaoGetIntensityReply(SICMessage):
    """
    SICMessage that contains the intensity of LED(s) as per requested by NaoGetIntensityRequest
    value - float [0, 1] representing the intensity value
    """
    def __init__(self, value):
        super(NaoGetIntensityReply, self).__init__()
        self.value = value


class NaoFadeRGBRequest(SICRequest):
    """
    Fade color of LED(s)
    name - RGB LED or Group name (string), see http://doc.aldebaran.com/2-5/naoqi/sensors/alleds.html
    r - float [0, 1] representing intensity of red channel
    g - float [0, 1] representing intensity of green channel
    b - float [0, 1] representing intensity of blue channel
    duration - float representing time in seconds to fade to given color. Default = 0, so instantly
    """
    def __init__(self, name, r, g, b, duration=0.):
        super(NaoFadeRGBRequest, self).__init__()
        self.name = name
        self.r = r
        self.g = g
        self.b = b
        self.duration = duration


class NaoFadeListRGBRequest(SICRequest):
    """
    Change LED(s) to multiple colors over time
    name - RGB LED or Group name (string), see http://doc.aldebaran.com/2-5/naoqi/sensors/alleds.html
    rgbs - list of RGB LED values in hexa-decimal [0x00RRGGBB, ...]
    durations - list of respective time to reach each RGB value in rgbs
    """
    def __init__(self, name, rgbs, durations):
        super(NaoFadeListRGBRequest, self).__init__()
        self.name = name
        self.rgbs = rgbs
        self.durations = durations

class NaoBasicAwarenessRequest(SICRequest):
    """
    Enable or disable basic awareness.
    value - boolean to enable/disable basic awareness
    stimulus_detection - list of tuples with (name, bool) to enable / disable stimulus detection for the given stimulus name, see http://doc.aldebaran.com/2-5/naoqi/interaction/autonomousabilities/albasicawareness.html#albasicawareness-stimuli-types
    engagement_mode - string to value engagement mode, see http://doc.aldebaran.com/2-5/naoqi/interaction/autonomousabilities/albasicawareness.html#albasicawareness-engagement-modes
    tracking_mode - string to value tracking mode, see http://doc.aldebaran.com/2-5/naoqi/interaction/autonomousabilities/albasicawareness.html#albasicawareness-tracking-modes
    """
    def __init__(self, value, stimulus_detection=None, engagement_mode=None, tracking_mode=None):
        super(NaoBasicAwarenessRequest, self).__init__()
        self.value = value
        self.stimulus_detection = stimulus_detection if stimulus_detection else []
        self.engagement_mode = engagement_mode
        self.tracking_mode = tracking_mode


class NaoqiLEDsActuator(SICActuator):
    """
    Wrapper class for sevaral Naoqi autonomous abilities, see http://doc.aldebaran.com/2-5/ref/life/autonomous_abilities_management.html?highlight=autonomous%20life
    Also implements wakeUp and rest requests.
    """
    def __init__(self, *args, **kwargs):
        super(NaoqiLEDsActuator, self).__init__(*args, **kwargs)

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        # Connect to AL proxies
        self.leds = self.session.service('ALLeds')

    @staticmethod
    def get_conf():
        return SICConfMessage()

    @staticmethod
    def get_inputs():
        return [NaoFadeRGBRequest, NaoFadeListRGBRequest, NaoLEDRequest,
                NaoSetIntensityRequest, NaoGetIntensityRequest]

    @staticmethod
    def get_output():
        return SICMessage

    def execute(self, message):
        if message == NaoFadeRGBRequest:
            self.leds.fadeRGB(message.name, message.r, message.g, message.b, message.duration)
        elif message == NaoFadeListRGBRequest:
            self.leds.fadeListRGB(message.name, message.rgbs, message.durations)
        elif message == NaoLEDRequest:
            if message.value:
                self.leds.on(message.name)
            else:
                self.leds.off(message.name)
        elif message == NaoSetIntensityRequest:
            self.leds.setIntensity(message.name, message.intensity)
        elif message == NaoGetIntensityRequest:
            return NaoGetIntensityReply(self.leds.getIntensity(message.name))
        return SICMessage()


class NaoqiLEDs(SICConnector):
    component_class = NaoqiLEDsActuator


if __name__ == '__main__':
    SICComponentManager([NaoqiLEDs])
