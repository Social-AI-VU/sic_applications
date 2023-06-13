from sic_framework import utils, SICComponentManager, SICMessage, SICRequest, \
    SICConfMessage

from sic_framework import SICActuator
from sic_framework.core.connector import SICConnector

if utils.PYTHON_VERSION_IS_2:
    import qi


class NaoBlinkingRequest(SICRequest):
    """
    Enable or disable autonomous blinking.
    value - boolean to enable/disable autonomous blinking
    """
    def __init__(self, value):
        super(NaoBlinkingRequest, self).__init__()
        self.value = value


class NaoBackgroundMovingRequest(SICRequest):
    """
    Enable or disable autonomous background moving.
    value - boolean to enable/disable background moving
    """
    def __init__(self, value):
        super(NaoBackgroundMovingRequest, self).__init__()
        self.value = value


class NaoListeningMovementRequest(SICRequest):
    """
    Enable or disable slight movements showing that the robot is listening.
    value - boolean to enable/disable
    """
    def __init__(self, value):
        super(NaoListeningMovementRequest, self).__init__()
        self.value = value


class NaoSpeakingMovementRequest(SICRequest):
    """
    Enable or disable autonomously movements during speech of the robot.
    value - boolean to enable/disable
    mode - string to determine speaking movement mode. 2 options: "random" or "contextual", see http://doc.aldebaran.com/2-5/naoqi/interaction/autonomousabilities/alspeakingmovement.html#speaking-movement-mode
    """
    def __init__(self, value, mode=None):
        super(NaoSpeakingMovementRequest, self).__init__()
        self.value = value
        self.mode = mode


class NaoRestRequest(SICRequest):
    """
    Go to the rest position. It is good practise to do this when not using the robot, to allow the motors to cool and
    reduce wear on the robot.
    """
    pass


class NaoWakeUpRequest(SICRequest):
    """
    The robot wakes up: sets Motor on and, if needed, goes to initial position.
    Enable FullyEngaged mode to appear alive.
    """
    pass


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


class NaoqiAutonomousActuator(SICActuator):
    """
    Wrapper class for sevaral Naoqi autonomous abilities, see http://doc.aldebaran.com/2-5/ref/life/autonomous_abilities_management.html?highlight=autonomous%20life
    Also implements wakeUp and rest requests.
    """
    def __init__(self, *args, **kwargs):
        super(NaoqiAutonomousActuator, self).__init__(*args, **kwargs)

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        # Connect to AL proxies
        self.blinking = self.session.service('ALAutonomousBlinking')
        self.background_movement = self.session.service('ALBackgroundMovement')
        self.basic_awareness = self.session.service('ALBasicAwareness')
        self.listening_movement = self.session.service('ALListeningMovement')
        self.speaking_movement = self.session.service('ALSpeakingMovement')
        self.autonomous_life = self.session.service('ALAutonomousLife')
        self.motion = self.session.service('ALMotion')

    @staticmethod
    def get_conf():
        return SICConfMessage()

    @staticmethod
    def get_inputs():
        return [NaoBlinkingRequest, NaoBackgroundMovingRequest,
                NaoBasicAwarenessRequest, NaoListeningMovementRequest,
                NaoSpeakingMovementRequest, NaoWakeUpRequest, NaoRestRequest]

    @staticmethod
    def get_output():
        return SICMessage

    def execute(self, message):
        if message == NaoRestRequest:
            self.motion.rest()
        elif message == NaoWakeUpRequest:
            self.motion.wakeUp()
        elif message == NaoBlinkingRequest:
            self.blinking.setEnabled(message.value)
        elif message == NaoBackgroundMovingRequest:
            self.background_movement.setEnabled(message.value)
        elif message == NaoListeningMovementRequest:
            self.listening_movement.setEnabled(message.value)
        elif message == NaoSpeakingMovementRequest:
            self.speaking_movement.setEnabled(message.value)
            if message.mode:
                self.speaking_movement.setMode(message.mode)
        elif message == NaoBasicAwarenessRequest:
            self.basic_awareness.setEnabled(message.value)
            for name, val in message.stimulus_detection:
                self.basic_awareness.setStimulusDetectionEnabled(name, val)
            if message.engagement_mode:
                self.basic_awareness.setEngagementMode(message.engagement_mode)
            if message.tracking_mode:
                self.basic_awareness.setTrackingMode(message.tracking_mode)

        return SICMessage()


class NaoqiAutonomous(SICConnector):
    component_class = NaoqiAutonomousActuator


if __name__ == '__main__':
    SICComponentManager([NaoqiAutonomousActuator])
