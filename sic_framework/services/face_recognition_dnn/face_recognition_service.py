import collections

import cv2
import numpy as np
import torch
import torchvision
from dataclasses import dataclass

from numpy import array
from sic_framework.core.connector import SICConnector

from sic_framework.core.component_manager_python2 import SICComponentManager
from sic_framework.core.message_python2 import CompressedImageMessage, SICMessage, BoundingBox, BoundingBoxesMessage
from sic_framework.core.service_python2 import SICService

from sklearn.neighbors import KNeighborsClassifier




class DNNFaceRecognitionService(SICService):

    # loading resnet takes some time
    COMPONENT_STARTUP_TIMEOUT = 15


    def __init__(self, *args, **kwargs):
        super(DNNFaceRecognitionService, self).__init__(*args, **kwargs)
        self.save_image = False
        self.img_timestamp = None

        # Initialize face recognition data
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        # import is relative, so only works when this file is main
        from model import resnet50

        self.model = resnet50(include_top=False, num_classes=8631)
        self.model.load_state_dict(
            torch.load("resnet50_ft_weight.pt"))
        self.model.to(self.device)

        cascadePath = "haarcascade_frontalface_default.xml"
        self.faceCascade = cv2.CascadeClassifier(cascadePath)

        # Define min window size to be recognized as a face_img
        self.minW = 150
        self.minH = 150

        self.ids = []
        self.next_id = 1

        self.classifier = KNeighborsClassifier(n_neighbors=1)

        self.features_history = collections.deque([], maxlen=3000)

    @staticmethod
    def get_inputs():
        return [CompressedImageMessage]

    @staticmethod
    def get_output():
        return BoundingBoxesMessage

    def execute(self, inputs):
        image = inputs.get(CompressedImageMessage).image

        id = 0

        img = array(image)[:, :, ::-1].astype(np.uint8)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        face_boxes = self.faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(self.minW), int(self.minH)),
        )

        faces = []

        for (x, y, w, h) in face_boxes:
            face = img[y:y + h, x:x + w, :]
            face = cv2.resize(face, (224, 224))

            tf = torchvision.transforms.ToTensor()

            face_tensor = tf(face)[np.newaxis, ...].to(self.device)

            features = self.model(face_tensor)
            features = features.detach().cpu().numpy().squeeze()
            self.features_history.append(features)
            feat_hist_arr = np.array(self.features_history)

            # predict id if a face has been seen before
            if len(self.ids) >= 1:
                id = self.classifier.predict([features])[0]

                # simple thresholding to figure out if it is a new face (for which we need to exclude the new face
                # itself)
                dist = np.min(np.linalg.norm(feat_hist_arr[:-1] - features, axis=1))

                if dist > 15:  # very magic trial by error number
                    self.logger.info("-------------------------------------------")
                    self.logger.info("New Face!, high distance of {}".format(dist))
                    self.logger.info("-------------------------------------------")
                    id = self.next_id
                    self.next_id += 1


                else:
                    self.logger.info("Recognized face {}".format(id))

            # update kNN classifier
            self.ids.append(id)
            self.classifier.fit(feat_hist_arr, self.ids)

            face = BoundingBox(x, y, w, h, identifier=id)

            faces.append(face)

        return BoundingBoxesMessage(faces)

class DNNFaceRecognition(SICConnector):
    component_class = DNNFaceRecognitionService



if __name__ == '__main__':
    SICComponentManager([DNNFaceRecognitionService])
