from sic_framework.devices.common_naoqi.naoqi_camera import StereoImageMessage
from sic_framework import UncompressedImageMessage
from sic_framework import SICComponentManager, SICService, SICMessage, SICConfMessage, utils
from cv2 import StereoSGBM_create, ximgproc

import numpy as np


class DepthEstimationService(SICService):
    INVALID_VALUE = -1

    def __init__(self, *args, **kwargs):
        super(DepthEstimationService, self).__init__(*args, **kwargs)

        MIN_DISP = -16
        NUM_DISP = 128  # 128 for high res, 80 for low res
        BLOCK_SIZE = 10  # 10 for high res, 6 for low res
        UNIQUENESS_RATIO = 5
        SPECKLE_WINDOW = 200
        SPECKLE_RANGE = 2
        DISP12_MAX_DIFF = 0
        STEREO_MODE = 3
        LAMBDA = 1000.0
        SIGMA_COLOR = 1.5

        self.left_matcher = StereoSGBM_create(
            minDisparity=MIN_DISP,
            numDisparities=NUM_DISP,
            blockSize=BLOCK_SIZE,
            uniquenessRatio=UNIQUENESS_RATIO,
            speckleWindowSize=SPECKLE_WINDOW,
            speckleRange=SPECKLE_RANGE,
            disp12MaxDiff=DISP12_MAX_DIFF,
            P1=8 * BLOCK_SIZE * BLOCK_SIZE,
            P2=32 * BLOCK_SIZE * BLOCK_SIZE,
            mode=STEREO_MODE
        )
        self.right_matcher = ximgproc.createRightMatcher(self.left_matcher)
        self.wls_filter = ximgproc.createDisparityWLSFilter(self.left_matcher)
        self.wls_filter.setLambda(LAMBDA)
        self.wls_filter.setSigmaColor(SIGMA_COLOR)

    @staticmethod
    def get_inputs():
        return [StereoImageMessage]

    @staticmethod
    def get_output():
        return UncompressedImageMessage

    @staticmethod
    def disp_to_cm(disp):
        return (45 * 78) / (disp + 1e-5)

    def execute(self, inputs):
        # Notice that the images are already rectified by StereoPepperCamera
        stereo_msg = inputs.get(StereoImageMessage)
        left, right = stereo_msg.left_image, stereo_msg.right_image

        # Calculate combined left-to-right and right-to-left disparities
        left_disp = self.left_matcher.compute(left, right)
        print(round(np.sum(left_disp < -16) / left_disp.size * 100, 2), left_disp.max())

        right_disp = self.right_matcher.compute(right, left)
        print(round(np.sum(right_disp < -16) / right_disp.size * 100, 2) , right_disp.max())

        filtered_disp = self.wls_filter.filter(left_disp, left, disparity_map_right=right_disp)
        print(np.sum((filtered_disp.astype(float) / 16.0) == -1))

        disparity_img = filtered_disp.astype(np.float) / 16.0

        # print(np.sum(disparity_img == -1))
        print()

        return UncompressedImageMessage(disparity_img)

        # disparity_img = SICservice.crop_image(disparity_img)
        # disparity_img[disparity_img < 0] = self.INVALID_VALUE  # Disparity cannot be negative
        # disparity_img[disparity_img >= left.shape[1]] = self.INVALID_VALUE  # Disparity larger than image width is not possible
        #
        # depth_img = self.disp_to_cm(disparity_img.copy())  # Disparity values to cm
        # depth_img[depth_img < 0] = self.INVALID_VALUE  # Depth cannot be negative
        # depth_img[depth_img > 10000] = self.INVALID_VALUE  # Max distance
        # return ImageMessage(depth_img)


if __name__ == '__main__':
    SICComponentManager([DepthEstimationService], "local")
