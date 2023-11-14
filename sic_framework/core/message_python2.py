# import dataclasses
import io
import random
import os
import time


import numpy as np
import six

from . import utils

if not six.PY3:
    import cPickle as pickle
    # Set path manually on pepper and nao
    lib_turbo_jpeg_path = "/" + os.path.join(*__file__.split(os.sep)[:-3]) + "/lib/libtubojpeg/lib32/libturbojpeg.so.0"
else:
    lib_turbo_jpeg_path = None
    import pickle

try:
    from turbojpeg import TurboJPEG
    turbojpeg = TurboJPEG(lib_turbo_jpeg_path)
except (RuntimeError, ImportError):
    # fall back to PIL in case TurboJPEG is not installed
    # PIL _can_ use turbojpeg, but can also fall back to a slower libjpeg
    # it is recommended to install turbojpeg
    print("Turbojpeg not found, falling back to PIL")
    from PIL import Image


    class FakeTurboJpeg:
        def encode(self, array):
            output = io.BytesIO()
            image = Image.fromarray(array)
            image.save(output, format="JPEG")
            output.seek(0)
            return output.read()

        def decode(self, bytes):
            image = Image.open(io.BytesIO(bytes))
            image = np.array(image)
            image = np.flipud(image)[:, :, ::-1]
            return image


    turbojpeg = FakeTurboJpeg()


class SICMessage(object):
    """
    The abstract message structure to pass messages around the SIC framework. Supports python types, numpy arrays
    and JPEG compression using libturbo-jpeg.
    _compress_images=True allow arrays of WxHx3 to be jpeg compressed for higher transfer speed.
    """

    # timestamp of the creation date of the data at its origin, e.g. camera, but not face detection (as it uses the
    # camera data, and should be aligned with data from the same creation time.
    _timestamp = None
    # A string with the name of the previous component that created it, used to differentiate messages of the same type.
    _previous_component_name = ""
    __NP_VALUES = []
    __JPEG_VALUES = []
    __SIC_MESSAGES = []
    _compress_images = False
    # this request id must be set when the message is sent as a reply to a SICRequest
    _request_id = None

    def __eq__(self, other):
        """
        Loose check to compare if messages are the same type. type(a) == type(b) might not work because the messages
        might have been created on different machines.
        :param other:
        :return:
        """
        if hasattr(other, "get_message_name"):
            return self.get_message_name() == other.get_message_name()
        else:
            return False

    @classmethod
    def get_message_name(cls):
        """
        The pretty name of this service.
        :return:
        """
        return cls.__name__

    @staticmethod
    def _np2base(inp):
        """
        Convert numpy arrays to byte arrays.
        :param inp: a numpy array
        :return: the byte string
        """
        mem_stream = io.BytesIO()
        np.save(mem_stream, inp)
        return mem_stream.getvalue()

    @staticmethod
    def _base2np(inp):
        """
        Convert back from byte arrays to numpy arrays.
        :param inp: a byte string
        :return: the numpy array
        """
        memfile = io.BytesIO()
        memfile.write(inp)
        memfile.seek(0)
        return np.load(memfile)

    @staticmethod
    def np2jpeg(inp):
        return turbojpeg.encode(inp)

    @staticmethod
    def jpeg2np(inp):
        # takes about 15 ms for 1280x960px
        img = turbojpeg.decode(inp)

        # the img np array now has the following flags:
        # C_CONTIGUOUS : False
        # OWNDATA: False

        # cv2 drawing functions fail, with cryptic type errors (but cv2.imShow does not)
        # the np.array() sets these flags to true
        # takes about 1 ms for 1280x960px
        img = np.array(img)

        return img

    def serialize(self):
        """
        Convert object to its bytes representation, compatible between python2 and python3 and
        with support for numpy arrays.
        :return: 'bytes' in python3, 'str' in python2 (which are roughly the same)
        """
        self.__NP_VALUES = []
        self.__JPEG_VALUES = []
        self.__SIC_MESSAGES = []

        # Compress np arrays with np.save
        for attr in vars(self):
            attr_value = getattr(self, attr)

            if isinstance(attr_value, SICMessage):
                setattr(self, attr, attr_value.serialize())
                self.__SIC_MESSAGES.append(attr)
            elif isinstance(attr_value, np.ndarray):
                if self._compress_images and attr_value.ndim == 3 and attr_value.shape[-1] == 3:
                    setattr(self, attr, self.np2jpeg(attr_value))
                    self.__JPEG_VALUES.append(attr)
                else:
                    setattr(self, attr, self._np2base(attr_value))
                    self.__NP_VALUES.append(attr)

        # Pickle dataclass
        return pickle.dumps(self, protocol=2)

    @staticmethod
    def _pickle_load(byte_string):
        """
        The pickle loads call is different between python versions. To reduce code duplication, this
        function is created to contain only the difference.
        :param byte_string:
        :return:
        """

        try:
            if utils.PYTHON_VERSION_IS_2:
                byte_string = utils.ensure_binary(byte_string)
                return pickle.loads(byte_string)
            else:
                return pickle.loads(byte_string, encoding='latin1')

        except pickle.UnpicklingError as e:
            raise pickle.UnpicklingError('Byte string is likely not a SICMessage ({})'.format(e))

        except AttributeError as e:
            raise AttributeError(
                "You likely haven't imported the class that caused the original error in your SICApplication.\n--> Original error: {}".format(
                    e))
        except TypeError as e:
            raise TypeError(
                "You tried to deserialize a wrong type of message, or sent unpickleable types such as numpy arrays nested in objects. \n Got message:\n\n{}\n\n(original error: {})".format(
                    byte_string, e))

    @classmethod
    def deserialize(cls, byte_string):
        """
        Convert object from its bytes representation, compatible between python2 and python3 and
        with support for numpy arrays.
        :return: a SICMessage subclass
        """
        # Read pickle object
        obj = cls._pickle_load(byte_string)

        # Decompress SICMessage bytes to SICMessage
        for field in obj.__SIC_MESSAGES:
            field_val = getattr(obj, field)
            if not isinstance(field_val, bytes):
                field_val = field_val.encode('latin1')
            setattr(obj, field, SICMessage.deserialize(field_val))

        # Decompress numpy bytes to numpy arrays
        for field in obj.__NP_VALUES:
            field_val = getattr(obj, field)
            if not isinstance(field_val, bytes):
                field_val = field_val.encode('latin1')
            setattr(obj, field, obj._base2np(field_val))

        # Decompress JPEG images to numpy arrays
        for field in obj.__JPEG_VALUES:
            field_val = getattr(obj, field)
            if not isinstance(field_val, bytes):
                field_val = field_val.encode('latin1')
            setattr(obj, field, obj.jpeg2np(field_val))

        return obj

    def __repr__(self):
        max_len = 20
        out = str(self.__class__.__name__) + "\n"

        for attr in sorted(vars(self)):
            if attr.startswith("__"):
                continue

            attr_value = str(getattr(self, attr))
            out += " " + attr + ":" + attr_value[:max_len]

            if len(attr_value) > max_len:
                out += "[...]"

            out += "\n"

        return out


######################################################################################
#                             Message types                                          #
######################################################################################

class SICConfMessage(SICMessage):
    """
    A type of message that carries configuration information for services.
    """
    pass


class SICRequest(SICMessage):
    """
    A type of message that must be met with a reply, a SICMessage with the same request id, on the same channel.
    """
    _request_id = None

    def __init__(self, request_id=None):
        if request_id:
            self._request_id = request_id
        else:
            # TODO https://softwareengineering.stackexchange.com/questions/339125/acceptable-to-rely-on-random-ints-being-unique
            # should be a global that gets incremented, or 512
            self._request_id = random.getrandbits(128)


class SICControlMessage(SICMessage):
    """
    Superclass for all messages that are related to component control
    """


class SICControlRequest(SICRequest):
    """
    Superclass for all requests that are related to component control
    """

class SICPingRequest(SICControlRequest):
    """
    A request for a ping to check if alive.
    """

class SICPongMessage(SICControlMessage):
    """
    A pong to reply to a ping request.;
    """


class SICSuccessMessage(SICControlMessage):
    """
    Special type of message to signal a request was successfully completed.
    """


class SICStopRequest(SICControlRequest):
    """
    Special type of message to signal a device it should stop as the user no longer needs it.
    """


class SICIgnoreRequestMessage(SICControlMessage):
    """
    Special type of message with the request_response_id set to -1. This means it will not
    be automatically set to the id of the request this is a reply to, and in effect will
    not reply to the request as the user will ignore this reply.
    """
    _request_id = -1


######################################################################################
#                             Common data formats                                    #
######################################################################################

class CompressedImage(object):
    """
    Compress WxHx3 np arrays using libturbo-jpeg to speed up network transfer of
    images. This is LOSSY JPEG compression, which means the image is not exactly the same.
    Non-image array content will be destroyed by this compression.
    """
    _compress_images = True

    def __init__(self, image):
        self.image = image


class CompressedImageMessage(CompressedImage, SICMessage):
    """
    See CompressedImage
    """
    def __init__(self, *args, **kwargs):
        CompressedImage.__init__(self, *args, **kwargs)
        SICMessage.__init__(self)


class CompressedImageRequest(CompressedImage, SICRequest):
    """
    See CompressedImage
    """
    def __init__(self, *args, **kwargs):
        CompressedImage.__init__(self, *args, **kwargs)
        SICRequest.__init__(self)


class UncompressedImageMessage(SICMessage):
    """
    Message class to send images/np array without JPEG compression. The data is
    compressed using default np.save lossless compression. In other words: the
    data does not change after compression, but this is much slower than JPEGCompressedImageMessage
    """
    _compress_images = False

    def __init__(self, image):
        self.image = image


class Audio(object):
    """
    A message that should contain _byte representation_ of pulse-code modulated (PCM) 16-bit signed little endian
    integer waveform audio data. The integers are represented as a python byte array because this is the expected and
    provided data format of common hardware audio hardware and libraries. For compatibility with other services ensure
    that your data follows EXACTLY this data type. This should be the most common format, but please check your data
    format.

    You can convert to and from .wav files using the built-in module
    https://docs.python.org/2/library/wave.html
    """

    def __init__(self, waveform, sample_rate):
        self.sample_rate = sample_rate
        assert isinstance(waveform, bytes) or isinstance(waveform, bytearray), "Waveform must be a byte array"
        self.waveform = waveform


class AudioMessage(Audio, SICMessage):
    """
    See Audio
    """
    def __init__(self, *args, **kwargs):
        Audio.__init__(self, *args, **kwargs)
        SICMessage.__init__(self)


class AudioRequest(Audio, SICRequest):
    """
    See Audio
    """
    def __init__(self, *args, **kwargs):
        Audio.__init__(self, *args, **kwargs)
        SICRequest.__init__(self)


class Text(object):
    """
    A simple object with a string as text.
    """
    def __init__(self, text):
        self.text = text

class TextMessage(Text, SICMessage):
    """
    See Text
    """
    def __init__(self, *args, **kwargs):
        Text.__init__(self, *args, **kwargs)
        SICMessage.__init__(self)

class TextRequest(Text, SICRequest):
    """
    See Text
    """
    def __init__(self, *args, **kwargs):
        Text.__init__(self, *args, **kwargs)
        SICRequest.__init__(self)

class BoundingBox(object):
    """
    A generic class representing a single bounding box with optional identifier of the object.
    (x,y) represents the top-left pixel of the bounding box, and (w,h) indicates the width and height.
    Identifier can be used implementation specific to for example indicate a specific object type or
    detected person.
    Confidence indicates can be used to indicate the confidence of the detection mechanism.
    """

    def __init__(self, x, y, w, h, identifier=None, confidence=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.identifier = identifier
        self.confidence = confidence

    def xywh(self):
        """
        Get the coordinates as a numpy array.
        :return:
        """
        return np.array([self.x, self.y, self.w, self.h])

    def __str__(self):
        return "BoundingBox\nxywh: {}\nidentifier: {}\nconfidence: {}".format(self.xywh(), self.identifier, self.confidence)


class BoundingBoxesMessage(SICMessage):
    """
    A generic class containing multiple bounding boxes as a list of BoundingBox objects.
    """

    def __init__(self, bboxes):
        self.bboxes = bboxes  # List[BoundingBox]
