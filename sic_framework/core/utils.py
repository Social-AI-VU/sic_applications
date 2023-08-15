import binascii
import getpass
import os
import socket
import sys

import six

PYTHON_VERSION_IS_2 = sys.version_info[0] < 3


def get_ip_adress():
    """
    This is harder than you think!
    https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    :return:
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


import socket

def ping_server(server: str, port: int, timeout=3):
    """ping server"""
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server, port))
    except OSError as error:
        return False
    else:
        s.close()
        return True


def get_username_hostname_ip():
    return getpass.getuser() + "_" + socket.gethostname() + "_" + get_ip_adress()



def ensure_binary(s, encoding='utf-8', errors='strict'):
    """
    From a future six version.
    Coerce **s** to six.binary_type.

    For Python 2:
      - `unicode` -> encoded to `str`
      - `str` -> `str`

    For Python 3:
      - `str` -> encoded to `bytes`
      - `bytes` -> `bytes`
    """
    if isinstance(s, six.binary_type):
        return s
    if isinstance(s, six.text_type):
        return s.encode(encoding, errors)
    raise TypeError("not expecting type '%s'" % type(s))

def str_if_bytes(data):
    """
    Compatibility for the channel names between python2 and python3
    a redis channel b'name' differes from "name"
    :param data: str or bytes
    :return: str
    """
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return data


def random_hex(nbytes=8):
    return binascii.b2a_hex(os.urandom(nbytes))


def is_sic_instance(obj, cls):
    """
    Return True if the object argument is an instance of the classinfo argument, or of a (direct, indirect,
    or virtual) subclass thereof.

    isinstance does not work when pickling object, so a looser class name check is performed.
    https://stackoverflow.com/questions/620844/why-do-i-get-unexpected-behavior-in-python-isinstance-after-pickling
    :param obj:
    :param cls:
    :return:
    """
    parents = obj.__class__.__mro__
    for parent in parents:
        if parent.__name__ == cls.__name__:
            return True

    return False


def type_equal_sic(a, b):
    """
    type(a) == type(b), but with support for objects transported across the nework with pickle.
    :param a: object
    :param b: object
    :return:
    """
    return type(a).__name__ == type(b).__name__



if __name__ == "__main__":
    pass
