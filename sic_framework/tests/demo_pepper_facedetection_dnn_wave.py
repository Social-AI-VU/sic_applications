import queue

import cv2

from sic_framework.core.message_python2 import BoundingBoxesMessage
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.core.utils_cv2 import draw_bbox_on_image
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoBasicAwarenessRequest, NaoBackgroundMovingRequest, \
    NaoWakeUpRequest
from sic_framework.devices.common_naoqi.naoqi_camera import NaoqiTopCamera, NaoqiCameraConf
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiIdlePostureRequest, NaoqiAnimationRequest
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import NaoqiMotionRecorder, NaoqiMotionRecording, PlayRecording
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness
from sic_framework.devices.pepper import Pepper
from sic_framework.services.face_detection_dnn.face_detection_dnn import DNNFaceDetection

""" 
This demo recognizes faces from your webcam and displays the result on your laptop.
"""

imgs_buffer = queue.Queue()


def on_image(image_message: CompressedImageMessage):
    try:
        imgs_buffer.get_nowait()  # remove previous message if its still there
    except queue.Empty:
        pass
    imgs_buffer.put(image_message.image)


faces_buffer = queue.Queue()


def on_faces(message: BoundingBoxesMessage):
    try:
        faces_buffer.get_nowait()  # remove previous message if its still there
    except queue.Empty:
        pass
    faces_buffer.put(message.bboxes)


conf = NaoqiCameraConf(cam_id=0, res_id=2)

# pepper = Pepper("192.168.0.165", top_camera_conf=conf)
pepper = Pepper("10.15.3.226", top_camera_conf=conf)

#
# pepper.motion.request(NaoqiIdlePostureRequest("Body", True))
# pepper.autonomous.request(NaoBasicAwarenessRequest(True))
# pepper.autonomous.request(NaoBackgroundMovingRequest(True))
pepper.autonomous.request(NaoWakeUpRequest())

# Connect to the services
face_det = DNNFaceDetection()

# Feed the camera images into the face recognition component
face_det.connect(pepper.top_camera)

# Send back the outputs to this program
pepper.top_camera.register_callback(on_image)
face_det.register_callback(on_faces)


recording = NaoqiMotionRecording.load("wave.motion")
chain = ["RArm"]


# print("Replaying action")





while True:
    img = imgs_buffer.get()
    faces = faces_buffer.get()

    for face in faces:
        draw_bbox_on_image(face, img)

        if face.w > (face.w / img.shape[0]) > .125:
            # pepper.stiffness.request(Stiffness(.95, chain))
            # pepper.motion_record.request(PlayRecording(recording), block=False)
            # pepper.stiffness.request(Stiffness(.1, chain))
            pepper.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Hey_3"), block=False)
            

    cv2.imshow('', img[:,:,::-1])
    cv2.waitKey(1)
