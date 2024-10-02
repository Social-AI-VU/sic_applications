import base64
import numpy as np
import sys


def base64_dec(img):
    if sys.version_info[0] >= 3:
        out = np.frombuffer(base64.decodebytes(img), dtype=np.uint8).reshape(shape)
    else:
        out = np.frombuffer(base64.decodestring(img), dtype=np.uint8).reshape(shape)

    return out


if __name__ == '__main__':
    shape = (640, 480, 3)

    with open('test_img_base64', 'rb') as f:
        base64_string = f.readlines()[0]
        decoded_img = base64_dec(base64_string)

    print("DONE reading base64 encoded image. Decoded image has shape {} and dtype {}".format(decoded_img.shape,
                                                                                              decoded_img.dtype))
    print("Sanity check: image at location [50, 67, 1] = {}".format(decoded_img[50][67][1]))
