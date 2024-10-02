from threading import Event

from cv2 import StereoSGBM_create, ximgproc
from numpy import array, float16, mean, median, std
from sic_old.image_depth_pb2 import ImageDepth
from sic_old.image_masks_pb2 import ImageMasks
from sic_old.service import SICservice
import cv2

from multiprocessing import Process

NAN_PLACEHOLDER = 9999

MIN_DISP = -16
NUM_DISP = 80  # 128 for high res, 80 for low res
BLOCK_SIZE = 6  # 10 for high res, 6 for low res
UNIQUENESS_RATIO = 5
SPECKLE_WINDOW = 200
SPECKLE_RANGE = 2
DISP12_MAX_DIFF = 0
STEREO_MODE = 3
LAMBDA = 1000.0
SIGMA_COLOR = 1.5
CRITERION = 'median'


class DepthEstimationService(SICservice):
    def __init__(self, connect, identifier, disconnect):
        self.is_running = False
        self.img_timestamp = None
        self.img_tuple = None
        self.img_segmentation = None
        self.img_available = Event()

        # Configuration
        self.calibration_bytes = None
        self.disparities = []
        self.stereo_sgbm = None
        self.disparity_map = None
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

        super(DepthEstimationService, self).__init__(connect, identifier, disconnect)
        self.events_topic = self.get_full_channel('events')
        self.calibration_topic = self.get_full_channel('image_calibration')
        self.segmentation_topic = self.get_full_channel('segmentation_stream')
        self.depth_topic = self.get_full_channel('depth_stream')
        self.depth_estimated_topic = self.get_full_channel('depth_estimated')

        self.calibration_bytes = self.redis.get(self.calibration_topic)
        self.update_image_properties()

    def get_device_types(self):
        return ['cam']

    def get_channel_action_mapping(self):
        return {self.get_full_channel('events'): self.execute}

    def execute(self, message):
        data = message['data'].decode()
        if data.startswith('SegmentationStarted'):
            split = data.split(';')
            self.img_timestamp = int(split[1])

            left, right = self.retrieve_image(self.img_timestamp, want_stereo=True)
            if left is not None and right is not None:
                estimation_thread = Process(target=self.estimate_depth,
                                            args=(left, right, None))  # TODO: currently img_segmentation always set to None, no standalone-mode supported.
                estimation_thread.start()

    def estimate_depth(self, img_left, img_right, img_segmentation):
        self.produce_event('DepthEstimationStarted;' + str(self.img_timestamp))

        img_left, img_right = cv2.cvtColor(img_left, cv2.COLOR_BGR2GRAY), cv2.cvtColor(img_right, cv2.COLOR_BGR2GRAY)
        img1, img2 = SICservice.rectify_image(self.calibration_bytes, left=img_left, right=img_right)

        if img_segmentation is None:
            image_masks = []
        else:
            # Protobuf back to numpy array
            mask_shape = (img_segmentation.mask_count, img_segmentation.mask_height, img_segmentation.mask_width)
            prediction_masks = array(img_segmentation.masks).reshape(mask_shape)
            image_masks = prediction_masks.astype(bool)

        left_disp = self.left_matcher.compute(img1, img2)
        right_disp = self.right_matcher.compute(img2, img1)
        filtered_disp = self.wls_filter.filter(left_disp, img1, disparity_map_right=right_disp)
        disparity_img = filtered_disp.astype(float16) / 16.0

        disparity_img = SICservice.crop_image(disparity_img)
        disparity_img[disparity_img < 0] = NAN_PLACEHOLDER  # Disparity cannot be negative
        disparity_img[disparity_img >= img1.shape[1]] = NAN_PLACEHOLDER  # Disparity larger than image width is not possible

        depth_img = self.disp_to_cm(disparity_img.copy())  # Disparity values to cm
        depth_img[depth_img < 0] = NAN_PLACEHOLDER  # Camera cannot be negative
        depth_img[depth_img > 10000] = NAN_PLACEHOLDER  # Protobuf max

        # Create estimations, standard deviations
        estimations = []
        for image_mask in image_masks:
            estimation, deviation = DepthEstimationService.estimate(depth_img, image_mask)
            estimations.append((int(estimation), int(deviation)))

        img_depth = ImageDepth()
        img_depth.timestamp_ms = self.img_timestamp
        img_depth.image_width = depth_img.shape[1]
        img_depth.image_height = depth_img.shape[0]
        img_depth.depth_image.extend(depth_img.flatten().astype(int).tolist())

        # Publish the depth image and the estimations
        pipe = self.redis.pipeline()
        pipe.zadd(self.depth_topic, {img_depth.SerializeToString(): self.img_timestamp})
        pipe.zremrangebyrank(self.depth_topic, 0, -10)
        pipe.publish(self.events_topic, 'DepthEstimationDone;' + str(self.img_timestamp))

        # for estimation, deviation in estimations:
        #     pipe.publish(self.depth_estimated_topic, str(estimation) + ';' + str(deviation))
        # pipe.execute()

        pipe.execute()

        print(f"{self.img_timestamp}: Depth estimated")

    @staticmethod
    def estimate(img, seg=None):
        if seg is not None:
            img = img[seg]

        # Convert disparities to cm's
        img = DepthEstimationService.disp_to_cm(img.copy())

        # Get one value for selected area based on criterion
        distance, deviation = DepthEstimationService.img_to_depth(img)

        return max(0, distance), min(NAN_PLACEHOLDER, deviation)

    @staticmethod
    def disp_to_cm(disp):
        return (45 * 78) / (disp + 1e-5)

    @staticmethod
    def img_to_depth(img):
        img = img[img != NAN_PLACEHOLDER]
        if CRITERION == 'mean':
            return int(mean(img)), int(std(img))
        elif CRITERION == 'median':
            return int(median(img)), int(std(img))
        else:
            raise ValueError('Criterion ' + CRITERION + ' not known; should be "mean" or "median"')
