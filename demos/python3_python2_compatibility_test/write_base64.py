import base64
import numpy as np


def base64_enc(img):
    out = base64.b64encode(img)
    return out


if __name__ == '__main__':
    shape = (640, 480, 3)
    img = np.random.random(shape) * 255
    img = img.astype(np.uint8)

    with open('test_img_base64', 'wb') as f:
        f.write(base64_enc(img))

    print("DONE writing base64 encoded image with shape {} and type {}".format(shape, img.dtype))
    print("Sanity check: image at location [50, 67, 1] = {}".format(img[50][67][1]))
