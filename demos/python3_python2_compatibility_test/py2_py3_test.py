import sys
import timeit
import numpy as np
import cv2
import base64
from turbojpeg import TurboJPEG

if __name__ == '__main__':
    # Constants
    N = 10_000
    shape = (640, 480, 3)
    img = np.random.random(shape) * 255
    img = img.astype(np.uint8)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]

    # Info
    print(f"Evaluating with N={N}")
    print(f"Evaluating image with shape {img.shape} and dtype {img.dtype}")
    print()


    def cv2_comp(img):
        return cv2.imencode('.jpg', img, encode_param)[1]


    def cv2_decomp(img):
        return cv2.imdecode(img, 1).reshape(shape)


    def turbo_comp(img):
        jpeg = TurboJPEG()
        return jpeg.encode(img)


    def turbo_decomp(img):
        jpeg = TurboJPEG()
        return jpeg.decode(img)


    def base64_enc(img):
        out = base64.b64encode(img)
        return out


    def base64_dec(img, reshape_img=False):
        out = np.frombuffer(base64.decodebytes(img), dtype=np.uint8)
        if reshape_img:
            out = out.reshape(shape)
        return out


    base64_enc_img = base64_enc(img)
    print("Original img size", sys.getsizeof(img))
    print("Base64 encoded img size", sys.getsizeof(base64_enc_img))
    print()

    cv2_jpeg_comp = cv2_comp(img)
    base64_enc_jpeg_img = base64_enc(cv2_jpeg_comp)
    jpeg_comp_img = cv2.imencode('.jpg', img, encode_param)[1]
    turbo_comped_img = turbo_comp(img)

    # base64 + CV2
    time = timeit.timeit(lambda: base64_enc(cv2_comp(img)), number=N)
    print(
        f"OpenCV JPEG compression then base64 encode {(time / N)} seconds per iteration (FPS: {round(1 / (time / N))})")

    time = timeit.timeit(lambda: cv2_decomp(base64_dec(base64_enc_jpeg_img)), number=N)
    print(
        f"base64 decode then OpenCV JPEG decompression {(time / N)} seconds per iteration (FPS: {round(1 / (time / N))})")
    print(f"FILE SIZE: {sys.getsizeof(base64_enc(cv2_comp(img))) // 1000} kB")
    print()

    # base64
    time = timeit.timeit(lambda: base64_enc(img), number=N)
    print(f"NO compression, so only base64 encode {(time / N)} seconds per iteration (FPS: {round(1 / (time / N))})")

    time = timeit.timeit(lambda: base64_dec(base64_enc_img, reshape_img=True), number=N)
    print(f"base64 decode, NO JPEG decompression {(time / N)} seconds per iteration (FPS: {round(1 / (time / N))})")
    print(f"FILE SIZE: {sys.getsizeof(base64_enc(img)) // 1000} kB")
    print()

    # TurboJPEG
    time = timeit.timeit(lambda: turbo_comp(img), number=N)
    print(f"TurboJPEG JPEG compression and encoding {(time / N)} seconds per iteration (FPS: {round(1 / (time / N))})")

    time = timeit.timeit(lambda: turbo_decomp(turbo_comped_img), number=N)
    print(
        f"TurboJPEG JPEG decompression and decoding {(time / N)} seconds per iteration (FPS: {round(1 / (time / N))})")
    print(f"FILE SIZE: {sys.getsizeof(turbo_comp(img)) // 1000} kB")
    print()

    with open('test_img_base64_comp', 'wb') as f:
        f.write(base64_enc(cv2_comp(img)))
