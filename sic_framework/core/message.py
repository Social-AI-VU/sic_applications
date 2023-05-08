import sys
from dataclasses import dataclass

import numpy as np

from .message_python2 import SICConfMessage as SICConfMessage_python2
from .message_python2 import SICMessage as SICMessage_python2


@dataclass
class SICMessage(SICMessage_python2):
    pass


@dataclass
class SICConfMessage(SICConfMessage_python2):
    pass


if __name__ == '__main__':
    import os
    from redis import Redis


    def connect():
        host = os.getenv('DB_IP')
        password = os.getenv('DB_PASS')
        self_signed = os.getenv('DB_SSL_SELFSIGNED')
        if self_signed == '1':
            return Redis(host=host, ssl=True, ssl_ca_certs='cert.pem', password=password)
        else:
            return Redis(host=host, ssl=True, password=password)


    @dataclass
    class FaceRecData(SICMessage):
        count: int
        arr: np.array


    # np_arr = np.random.random((640, 480, 3)).astype(np.float32)
    # x = FaceRecData(5, np_arr)

    # print(hasattr(x, "count"))
    # exit(1)
    #
    # N = 10
    #
    # print("pickle")
    #
    # time = timeit.timeit(lambda: pickle.dumps(x), number=N)
    # print("  serialize", time)
    #
    # string = pickle.dumps(x)
    # time = timeit.timeit(lambda: pickle.loads(string), number=N)
    # print("  deserialize", time)
    #
    # ##############################
    # print("pickle 2")
    #
    # time = timeit.timeit(lambda: pickle.dumps(x, protocol=2), number=N)
    # print("  serialize", time)
    #
    # string = pickle.dumps(x)
    # time = timeit.timeit(lambda: pickle.loads(string), number=N)
    # print("  deserialize", time)
    #
    # ###########################
    # print("pickle vars")
    #
    # time = timeit.timeit(lambda: bytes(x), number=N)
    # print("  serialize", time)
    #
    # string = bytes(x)
    # time = timeit.timeit(lambda: x.from_bytes(string), number=N)
    # print("  deserialize", time)
    #
    #
    # # HARD
    # # string = x.serialize_vars()
    # # time = timeit.timeit(lambda: x.deserialize_vars(string), number=N)
    # # print("  deserialize", time)
    #
    # ###########################
    #
    # def serialize_numpy(arr: np.array) -> str:
    #     arr_dtype = bytearray(str(arr.dtype), 'utf-8')
    #     arr_shape = bytearray(','.join([str(a) for a in arr.shape]), 'utf-8')
    #     sep = bytearray('|', 'utf-8')
    #     arr_bytes = arr.ravel().tobytes()
    #     to_return = arr_dtype + sep + arr_shape + sep + arr_bytes
    #     return to_return
    #
    #
    # def deserialize_numpy(serialized_arr: str) -> np.array:
    #     sep = '|'.encode('utf-8')
    #     i_0 = serialized_arr.find(sep)
    #     i_1 = serialized_arr.find(sep, i_0 + 1)
    #     arr_dtype = serialized_arr[:i_0].decode('utf-8')
    #     arr_shape = tuple([int(a) for a in serialized_arr[i_0 + 1:i_1].decode('utf-8').split(',')])
    #     arr_str = serialized_arr[i_1 + 1:]
    #     arr = np.frombuffer(arr_str, dtype=arr_dtype).reshape(arr_shape)
    #     return arr
    #
    #
    # print("serialize using np.tobytes and np.frombuffer with struct.pack length and shape")
    # time = timeit.timeit(lambda: serialize_numpy(np_arr), number=N)
    # print("  serialize", time)
    # #
    # string = serialize_numpy(np_arr)
    # time = timeit.timeit(lambda: deserialize_numpy(string), number=N)
    # print("  deserialize", time)
    #
    # # ###########################
    # import io
    #
    # print("serialize using numpy save and load")
    # f = io.BytesIO()
    #
    #
    # def np_writez():
    #     f.flush()
    #     f.seek(0)
    #     np.savez_compressed(f, np_arr)
    #
    #
    # np_fun = np.savez
    #
    # time = timeit.timeit(lambda: np_fun(f, np_arr), number=N)
    # print("  serialize", time)
    # #
    # # string = np.load(np_arr)
    #
    # # def load_np():
    # #     f.seek(0)
    # #     np.load(f)
    #
    # f = io.BytesIO()
    # np_fun(f, np_arr)
    # content = f.getvalue()
    #
    # time = timeit.timeit(lambda: np.load(io.BytesIO(content)), number=N)
    # print("  deserialize", time)
    #
    # b"".join([])
    #
    #
    # np_arr_list = serialize_numpy(np_arr)
    #
    # from sic.image_depth_pb2 import ImageDepth
    #
    #
    # def pack_protobuf():
    #     img_depth = ImageDepth()
    #     img_depth.image_width = np_arr.shape[1]
    #     img_depth.image_height = np_arr.shape[0]
    #     img_depth.depth_image.extend(np_arr_list)
    #     return img_depth.SerializeToString()
    #
    #
    # time = timeit.timeit(pack_protobuf, number=N)
    # print(f"protobuf N = {N}")
    # print("  serialize", time)
    #
    # print()
    # # print(string)

    #
    np.random.seed(0)
    np_arr = (np.random.random((2, 2, 3)) * 255).astype(np.uint8)
    a = FaceRecData(5, np_arr)

    print(f"Python {sys.version_info[0]}: serialized\n{a}")
    ser_a = a.serialize()

    redis = connect()
    redis.set('test_np', ser_a)
    ser_message = redis.get('test_np')
    mess = FaceRecData.deserialize(ser_message)

    print(f"Python {sys.version_info[0]}: deserialized message, got\n{mess}")
    print(np.sum(np.abs(mess.arr - np_arr)))
    # ser_obj = x.serialize()
    # deser_obj = FaceRecData.deserialize(ser_obj)
    #
    # N = 1_000
    # time = timeit.timeit(lambda: FaceRecData(5, np_arr).serialize(), number=N)
    # print(f"Serialize FaceRecData {(time / N)} seconds per iteration (FPS: {round(1/ (time / N))})")
    #
    # time = timeit.timeit(lambda: FaceRecData.deserialize(ser_obj), number=N)
    # print(f"Deserialize FaceRecData {(time / N)} seconds per iteration (FPS: {round(1/ (time / N))})")
