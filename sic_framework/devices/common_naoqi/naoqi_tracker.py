import argparse

from sic_framework import utils
from sic_framework.core.actuator_python2 import SICActuator
from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import SICRequest, SICConfMessage, SICMessage

if utils.PYTHON_VERSION_IS_2:
    import qi


class RegisterTargetRequest(SICRequest):
    def __init__(self, target_name, diameter):
        """
        Request to register a tracking target, see http://doc.aldebaran.com/2-5/naoqi/trackers/index.html#tracking-targets
        :param target_name: name of object to track
        :param diameter: diameter
        """
        super(RegisterTargetRequest, self).__init__()
        self.target_name = target_name
        self.diameter = diameter


class SetModeRequest(SICRequest):
    def __init__(self, mode):
        """
        Request to set the tracking mode, see http://doc.aldebaran.com/2-5/naoqi/trackers/index.html#tracking-modes
        :param mode: name of tracking mode
        """
        super(SetModeRequest, self).__init__()
        self.mode = mode


class SetEffectorRequest(SICRequest):
    def __init__(self, effector):
        """
        Request to set the effector mode. Tracker always used the Head.
        :param effector: Name of the effector. Could be: “Arms”, “LArm”, “RArm” or “None”..
        """
        super(SetEffectorRequest, self).__init__()
        self.effector = effector


class StartTrackRequest(SICRequest):
    def __init__(self, target_name):
        """
        Request to start tracking the target_name
        :param target_name: name of object to start tracking
        """
        super(StartTrackRequest, self).__init__()
        self.target_name = target_name


class StopTrackRequest(SICRequest):
    """
    Request to stop the tracker
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

    @staticmethod
    def get_conf():
        return SICConfMessage()

    @staticmethod
    def get_inputs():
        return [RegisterTargetRequest, SetModeRequest, SetEffectorRequest, StartTrackRequest, ]

    @staticmethod
    def get_output():
        return SICMessage

    def execute(self, request):
        if request == RegisterTargetRequest:
            self.tracker.registerTarget(request.target_name, request.diameter)
        elif request == SetModeRequest:
            self.tracker.setMode(request.mode)
        elif request == SetEffectorRequest:
            self.tracker.setEffector(request.effector)
        elif request == StartTrackRequest:
            self.tracker.track(request.target_name)
        elif request == StopTrackRequest:
            self.tracker.stopTracker()
            self.tracker.unregisterAllTargets()
            self.tracker.setEffector("None")
        elif request == RemoveTargetRequest:
            self.tracker.unregisterTarget(request.target_name)
        elif request == RemoveAllTargetsRequest:
            self.tracker.unregisterAllTargets()

        return SICMessage()


class NaoqiTracker(SICConnector):
    component_class = NaoqiTrackerActuator


if __name__ == '__main__':
    SICComponentManager([NaoqiTrackerActuator])
