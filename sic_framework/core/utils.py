import binascii
import getpass
import os
import socket
import sys

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

def get_username_hostname_ip():
    return getpass.getuser() + "_" + socket.gethostname() + "_" + get_ip_adress()



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


def isinstance_pickle(obj, cls):
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


def type_equal_pickle(a, b):
    """
    type(a) == type(b), but with support for objects transported across the nework with pickle.
    :param a: object
    :param b: object
    :return:
    """
    return type(a).__name__ == type(b).__name__



if __name__ == "__main__":
    pass
