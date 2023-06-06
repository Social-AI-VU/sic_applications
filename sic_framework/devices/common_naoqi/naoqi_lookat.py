import threading
from sic_framework import SICComponentManager, utils
from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import AudioMessage, SICConfMessage, SICMessage, BoundingBoxesMessage
from sic_framework.core.sensor_python2 import SICSensor
from sic_framework.devices.common_naoqi.naoqi_motion_streamer import NaoJointAngles

if utils.PYTHON_VERSION_IS_2:
    from naoqi import ALProxy
    import qi


class NaoqiLookAtConf(SICConfMessage):
    def __init__(self, camera_index = 0, camera_y_max = 480, camera_x_max = 640):
        self.camera_index = camera_index  # 0 = top, 1 = bottom
        self.camera_y_max = camera_y_max
        self.camera_x_max = camera_x_max


class LookAtMessage(SICMessage):
    """
    Make the robot look at the normalized image coordinates. X is mirrored by default, as camera images are often mirrored.
    """
    _compress_images = False

    def __init__(self, x, y, mirror_x=True):
        if mirror_x:
            x = -x
        self.x = x
        self.y = y


class NaoqiLookAtComponent(SICComponent):
    def __init__(self, *args, **kwargs):
        super(NaoqiLookAtComponent, self).__init__(*args, **kwargs)

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        self.video_service = self.session.service("ALVideoDevice")
        self.tracker = self.session.service('ALTracker')
        self.motion = self.session.service('ALMotion')

    @staticmethod
    def get_conf():
        return NaoqiLookAtConf()

    @staticmethod
    def get_inputs():
        return [LookAtMessage, BoundingBoxesMessage]

    @staticmethod
    def get_output():
        return AudioMessage

    def on_message(self, message):
        if message == BoundingBoxesMessage:
            # track the most confident boundingbox
            if len(message.bboxes):
                bbox = message.bboxes[0]

                for x in message.bboxes:
                    if bbox.confidence < x.confidence:
                        bbox = x

                y = bbox.y / self.params.camera_y_max
                x = bbox.x / self.params.camera_x_max
                angles = self.video_service.getAngularPositionFromImagePosition(self.params.camera_index, [x, y])

                self.output_message(NaoJointAngles(["HeadYaw", "HeadPitch"], angles))

        elif message == LookAtMessage:
            y = message.y / self.params.camera_y_max
            x = message.x / self.params.camera_x_max
            angles = self.video_service.getAngularPositionFromImagePosition(self.params.camera_index, [x, y])

            self.output_message(NaoJointAngles(["HeadYaw", "HeadPitch"], angles))

    def stop(self, *args):
        self.session.close()
        super(NaoqiLookAtComponent, self).stop(*args)


class NaoqiLookAt(SICConnector):
    component_class = NaoqiLookAtComponent


if __name__ == '__main__':
    SICComponentManager([NaoqiLookAtComponent])
