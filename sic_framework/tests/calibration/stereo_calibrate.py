import numpy as np
import cv2
import codecs
import pickle
from PIL import Image, ImageEnhance, ImageOps
from sic_framework import SICApplication
from sic_framework.devices.common_naoqi.naoqi_camera import StereoPepperCameraSensor, NaoStereoCameraConf
from sic_framework.devices.pepper import Pepper
import time
import matplotlib.pyplot as plt


class Display:
    def __init__(self, wait_for_event=False, size=(640, 360)):
        import pygame
        self.pygame = pygame
        self.wait = wait_for_event

        self.pygame.init()
        self.size = size
        self.display_surface = self.pygame.display.set_mode(self.size)

        self.font = self.pygame.font.SysFont('robotoslab', 30)

    @staticmethod
    def gray(im):
        im = 255 * (im / im.max())
        w, h = im.shape
        ret = np.empty((w, h, 3), dtype=np.uint8)
        ret[:, :, 2] = ret[:, :, 1] = ret[:, :, 0] = im
        return ret

    def clear(self, text=None):
        white = (255, 255, 255)
        self.display_surface.fill(white)

        if text:
            textsurface = self.font.render(text, False, (0, 0, 0))
            self.display_surface.blit(textsurface, (0, 0))

        self.pygame.display.update()

    def show(self, arr, scale=False):
        white = (255, 255, 255)
        assert arr.ndim in [2, 3], "incorrect dimensions"
        img = arr

        # unnormalize
        if arr.dtype in [np.float, np.float32, np.float64]:
            arr -= arr.min()
            arr /= arr.max()
            arr *= 255
            arr = arr.astype(np.int)

        # gray to color
        if arr.ndim == 2:
            arr = self.gray(arr)

        arr = arr.swapaxes(0, 1)  # Fix pygame transposed rendering
        surf = self.pygame.surfarray.make_surface(arr)
        # surf = self.pygame.transform.rotate(surf, -90) # now done by swapaxis

        if scale:
            surf = self.pygame.transform.scale(surf, self.size)

        self.display_surface.fill(white)
        self.display_surface.blit(surf, (0, 0))
        self.pygame.display.update()

        if self.wait:
            self.pygame.event.clear()
            while True:
                event = self.pygame.event.wait()
                if event.type == self.pygame.QUIT:
                    self.close()
                    break

                elif event.type == self.pygame.KEYDOWN:
                    if event.key == self.pygame.K_i:
                        plt.imshow(img)
                        plt.show()
                    else:
                        break

    def wait_for_key(self):
        self.pygame.event.clear()
        while True:
            event = self.pygame.event.wait()
            if event.type == self.pygame.QUIT:
                self.close()
                break

            elif event.type == self.pygame.KEYDOWN:
                return event.key

    def set_caption(self, string):
        self.pygame.display.set_caption(string)

    def close(self):
        self.pygame.quit()


disp = Display()

class StereoCalibrate(SICApplication):
    def __init__(self, calibration_bytes=None, K_D_matrix=None, filename_suffix=''):
        self.block_size = 10
        self.min_disp = -16
        self.num_disp = 128
        self.uniquenessRatio = 5
        self.specklewind = 200
        self.speckle = 2
        self.disp12MaxDiff = 0

        self.H1, self.H2 = None, None

        self.filename_suffix = filename_suffix
        self.read_calibration(calibration_bytes, K_D_matrix)
        
        super().__init__()

    def read_calibration(self, calibration_bytes, K_D_matrix):
        if not calibration_bytes and K_D_matrix:
            return self.init_undistort(K_D_matrix)

        from pickle import loads
        from codecs import decode

        with open(calibration_bytes, 'rb') as f:
            cameramatrix, K, D, H1, H2 = loads(decode(f.read(), 'base64'))

        self.newcameramtx = cameramatrix
        self.K = K
        self.D = D
        self.H1 = H1
        self.H2 = H2

    def init_undistort(self, path):
        fs = cv2.FileStorage(path, cv2.FILE_STORAGE_READ)
        self.K = fs.getNode("K").mat()
        self.D = fs.getNode("D").mat()

        self.newcameramtx, self.roi = cv2.getOptimalNewCameraMatrix(self.K, self.D, self.image_shape, 1, self.image_shape)

    def undistort_img(self, img):
        # top = int(30 / 360 * img.shape[0])
        # left = int(104 / 640 * img.shape[1])
        # right = int(-66 / 640 * img.shape[1])
        return cv2.undistort(img, self.K, self.D, None, self.newcameramtx) #[top:, left:right]

    def store_calibration(self):
        calibration_info = (self.newcameramtx, self.K, self.D, self.H1, self.H2)
        pickled = codecs.encode(pickle.dumps(calibration_info), "base64")  # Store as byte string

        import time
        timestr = time.strftime("%Y%m%d_%H%M%S")
        with open(f'calibration_info_{self.image_shape[0]}_{self.image_shape[1]}_{timestr}{self.filename_suffix}', 'wb') as f:
            f.write(pickled)

    def calibrate(self, img1: np.ndarray, img2: np.ndarray):
        assert img1.ndim == 2 and img2.ndim == 2, f"Use grayscale images! Got {img1.ndim, img1.shape}"
        img1 = self.undistort_img(img1)
        img2 = self.undistort_img(img2)

        # Initiate SIFT detector
        sift = cv2.SIFT_create()

        # find the keypoints and descriptors with SIFT
        kp1, des1 = sift.detectAndCompute(img1, None)
        kp2, des2 = sift.detectAndCompute(img2, None)

        # Match keypoints in both images
        # Based on: https://docs.opencv.org/master/dc/dc3/tutorial_py_matcher.html
        FLANN_INDEX_KDTREE = 0
        index_params = {'algorithm': FLANN_INDEX_KDTREE, 'trees': 50}
        search_params = {'checks': 1000}
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des1, des2, k=2)

        # Keep good matches: calculate distinctive image features
        # https://www.cs.ubc.ca/~lowe/papers/ijcv04.pdf
        pts1 = []
        pts2 = []

        for i, (m, n) in enumerate(matches):
            if m.distance < 0.6 * n.distance:
                # Keep this keypoint pair
                pts2.append(kp2[m.trainIdx].pt)
                pts1.append(kp1[m.queryIdx].pt)

        pts1 = np.int32(pts1)
        pts2 = np.int32(pts2)
        print("Using", len(pts1), "points for calibration.")
        fundamental_matrix, inliers = cv2.findFundamentalMat(pts1, pts2,
                                                             cv2.FM_RANSAC, 1,
                                                             0.999)
        # We select only inlier points
        if inliers is None:
            print("Calibration failed. Try again")
            exit(1)

        print(f"Calibration uses {round(len(pts1[inliers.ravel() == 1]) / len(pts1) * 100, 1)}% inliers")
        pts1 = pts1[inliers.ravel() == 1]
        pts2 = pts2[inliers.ravel() == 1]

        _, H1, H2 = cv2.stereoRectifyUncalibrated(np.float32(pts1),
                                                  np.float32(pts2),
                                                  fundamental_matrix,
                                                  imgSize=img1.shape)
        self.H1 = H1
        self.H2 = H2

    def rectify(self, img1, img2):
        assert self.H1 is not None and self.H2 is not None, "Calibrate first with self.calibrate()"

        img1 = self.undistort_img(img1)
        img2 = self.undistort_img(img2)

        img1_rectified = cv2.warpPerspective(img1, self.H1, img1.shape[::-1])
        img2_rectified = cv2.warpPerspective(img2, self.H2, img2.shape[::-1])

        return img1_rectified, img2_rectified

    @staticmethod
    def ask_input():
        while True:
            txt = input("Satisfied with calibration? (yes/no)")
            if txt == 'yes' or txt == 'no':
                break
            else:
                print("Type yes or no")

        print()
        return txt == 'yes'

    @staticmethod
    def dummy_rectify(shape, mat):
        temp_img = np.ones(shape)

        img1_rectified = cv2.warpPerspective(temp_img, mat, temp_img.shape[::-1], borderValue=0)
        return np.sum(img1_rectified == 1) / temp_img.size * 100

    def on_stereo(self, img_message):
        self.calibrate(img_message.left_image, img_message.right_image)
        score = np.mean([self.dummy_rectify(img_message.left_image.shape, self.H1),
                         self.dummy_rectify(img_message.left_image.shape, self.H2)])
        print("Score", round(score, 1))

        if score >= 90:
            img1, img2 = self.rectify(img_message.left_image, img_message.right_image)

            # Create anaglyph
            L = Image.fromarray(img1).convert("L")
            L = ImageOps.colorize(L, (0, 0, 0), (0, 255, 255))
            R = Image.fromarray(img2).convert("L")
            R = ImageOps.colorize(R, (0, 0, 0), (255, 0, 0))
            blended = Image.blend(L, R, 0.5)
            enhancer = ImageEnhance.Brightness(blended)
            blended = enhancer.enhance(1.5)
            np_blended = cv2.cvtColor(np.array(blended), cv2.COLOR_RGB2BGR)
            disp.show(np_blended)

            if self.ask_input():
                self.store_calibration()

                # cv2.waitKey(1)
                # cv2.destroyAllWindows()
                self.stop()

    def run(self) -> None:
        # Connect to stereo camera
        pepper = Pepper(device_id='pepper', application=self)
        stereo_conf = NaoStereoCameraConf(calib_params={}, use_calib=False, convert_bw=True, cam_id=3, res_id=14)
        pepper.set_config(StereoPepperCameraSensor, stereo_conf)
        pepper.stereo_camera.register_callback(self.on_stereo)

        time.sleep(10000)


if __name__ == "__main__":
    test_app = StereoCalibrate('calib')
    test_app.run()
    test_app.stop()
