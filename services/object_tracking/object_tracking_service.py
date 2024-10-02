import numpy as np
from motpy import Detection, MultiObjectTracker

from sic_framework.core.message_python2 import CompressedImageMessage, BoundingBoxesMessage, SICConfMessage, BoundingBox
from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.core.service_python2 import SICService


class ObjectTrackingConfig(SICConfMessage):
    def __init__(self, delta_time=.1):
        super(ObjectTrackingConfig, self).__init__()
        self.delta_time = delta_time


class ObjectTrackingService(SICService):
    def __init__(self, *args, **kwargs):
        super(ObjectTrackingService, self).__init__(*args, **kwargs)

        self.tracker = MultiObjectTracker(dt=self.params.delta_time)

    @staticmethod
    def get_conf():
        return ObjectTrackingConfig()

    @staticmethod
    def get_inputs():
        return [BoundingBoxesMessage]

    @staticmethod
    def get_output():
        return BoundingBoxesMessage

    def execute(self, inputs):
        message = inputs.get(BoundingBoxesMessage)

        detection_bboxes = []

        for bbox in message.bboxes:
            detection_bboxes.append(Detection([bbox.x, bbox.y, bbox.x + bbox.w, bbox.y + bbox.h]))

        self.tracker.step(detection_bboxes)

        tracks = self.tracker.active_tracks()


        filtered_bboxes = []
        for track in tracks:
            xmin, ymin, xmax, ymax = track.box.astype(np.int)

            bbox = BoundingBox(xmin, ymin, xmax - xmin, ymax - ymin, track.id[:8])
            filtered_bboxes.append(bbox)

        return BoundingBoxesMessage(filtered_bboxes)


if __name__ == '__main__':
    SICComponentManager([ObjectTrackingService], "local")
