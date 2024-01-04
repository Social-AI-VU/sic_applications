from sic_framework import utils
from sic_framework.core.actuator_python2 import SICActuator
from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import SICRequest, SICConfMessage, SICMessage

if utils.PYTHON_VERSION_IS_2:
    import qi



class StartTrackRequest(SICRequest):
    def __init__(self, target_name, size, mode="Head", effector="None", move_rel_position=None):
        """
        Request to register a tracking target and track it, see http://doc.aldebaran.com/2-5/naoqi/trackers/index.html
        :param target_name: name of object to track , e.g. RedBall, Face
        :param size: size e.g. diameter of ball, width of face (meter)
        :param mode: tracking mode, default mode is "Head", other options: "WholeBody", "Move", see http://doc.aldebaran.com/2-5/naoqi/trackers/index.html#tracking-modes
        :param effector: Name of the effector. Could be: "Arms", "LArm", "RArm" or "None".
        :param move_rel_position: Set the robot position relative to target in Move mode
        """
        super(StartTrackRequest, self).__init__()
        self.target_name = target_name
        self.size = size
        self.mode = mode
        self.effector = effector
        self.move_rel_position = move_rel_position


class StopAllTrackRequest(SICRequest):
    """
    Request to stop the tracker, and unregister all targets
    """
    pass


class RemoveTargetRequest(SICRequest):
    def __init__(self, target_name):
        """
        Request to remove the target_name
        :param target_name: name of object to stop tracking
        """
        super(RemoveTargetRequest, self).__init__()
        self.target_name = target_name


class RemoveAllTargetsRequest(SICRequest):
    """
    Request to remove all tracking targets
    """
    pass


class NaoqiTrackerActuator(SICActuator):
    def __init__(self, *args, **kwargs):
        super(NaoqiTrackerActuator, self).__init__(*args, **kwargs)

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        self.tracker = self.session.service('ALTracker')
        self.posture = self.session.service("ALRobotPosture")
        self.motion = self.session.service('ALMotion')

    @staticmethod
    def get_conf():
        return SICConfMessage()

    @staticmethod
    def get_inputs():
        return [StartTrackRequest, StopAllTrackRequest, RemoveTargetRequest, RemoveAllTargetsRequest]

    @staticmethod
    def get_output():
        return SICMessage

    def execute(self, request):
        if request == StartTrackRequest:
            self.logger.info("Start TrackRequest for {}".format(request.target_name))
            # add target to track
            self.tracker.registerTarget(request.target_name, request.size)
            # set mode
            self.tracker.setMode(request.mode)
            # for Move and WholeBody modes, the robot must be in a standing posture, ready to move
            if request.mode == "Move" or request.mode == "WholeBody":
                self.posture.goToPosture("Stand", 0.5)
            if request.mode == "Move":
                if request.move_rel_position is None:
                    self.logger.info(
                        "The relative position is not passed, "
                        "the value is either the default [0, 0, 0, 0, 0, 0] if never set "
                        "or the previous value passed"
                    )
                    self.logger.info("Get relative position {}".format(self.tracker.getRelativePosition()))
                else:
                    self.tracker.setRelativePosition(request.move_rel_position)
                    self.logger.info("Get relative position {}".format(self.tracker.getRelativePosition()))
            # set effector
            self.tracker.setEffector(request.effector)
            # start tracker
            self.tracker.track(request.target_name)
        elif request == StopAllTrackRequest:
            self.logger.info("Stop TrackRequest")
            self.tracker.stopTracker()
            self.tracker.unregisterAllTargets()
            self.tracker.setEffector("None")
            self.posture.goToPosture("Stand", 0.5)
            self.motion.rest()
        elif request == RemoveTargetRequest:
            self.logger.info("Unregister target {}".format(request.target_name))
            self.tracker.unregisterTarget(request.target_name)
        elif request == RemoveAllTargetsRequest:
            self.tracker.unregisterAllTargets()

        return SICMessage()


class NaoqiTracker(SICConnector):
    component_class = NaoqiTrackerActuator


if __name__ == '__main__':
    SICComponentManager([NaoqiTrackerActuator])
