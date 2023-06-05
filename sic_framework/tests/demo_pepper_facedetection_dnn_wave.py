import queue

import cv2

from sic_framework.core.message_python2 import BoundingBoxesMessage
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.core.utils_cv2 import draw_on_image
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoCamera, NaoqiCameraConf
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import PepperMotionRecorder, NaoqiMotionRecording, \
    SetStiffness, PlayRecording
from sic_framework.services.face_detection_dnn.face_detection_dnn_service import DNNFaceDetection

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


# Connect to the services
conf = NaoqiCameraConf(cam_id=0, res_id=2)
camera = TopNaoCamera(ip="192.168.0.148", conf=conf)
face_rec = DNNFaceDetection()

# Feed the camera images into the face recognition component
face_rec.connect(camera)

# Send back the outputs to this program
camera.register_callback(on_image)
face_rec.register_callback(on_faces)


recorder = PepperMotionRecorder("192.168.0.148")
recording = NaoqiMotionRecording.load("wave_fast.motion")
chain = ["LArm", "RArm", "Head"]

# print("Replaying action")





while True:
    img = imgs_buffer.get()
    faces = faces_buffer.get()

    for face in faces:
        draw_on_image(face, img)

        if face.w > 80:
            print("WAVE")
            recorder.request(SetStiffness(.95, chain))
            recorder.request(PlayRecording(recording))
            recorder.request(SetStiffness(.1, chain))

    cv2.imshow('', img[:,:,::-1])
    cv2.waitKey(1)
