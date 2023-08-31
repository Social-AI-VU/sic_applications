"""
A wrapper around redis to provide a simpler interface for sending SICMessages, using two different API's. The blocking
API is used for devices, from which we expect a reply when the action is completed. The non-blocking API is used for
services, which do not have to wait for a response as communication is one way only.

Non-blocking:
    ## DEVICE A
        r.register_message_handler("my_channel", do_something_fn)

    ## DEVICE B
        r.send_message("my_channel", SICMessage("abc"))


Blocking:
    ## DEVICE A
        def do_reply(channel, request):
            return SICMessage()

        r.register_request_handler("my_channel", do_reply)

    ## DEVICE B
        reply = r.request("my_channel", NamedRequest("req_handling"), timeout=5)

Note: You can send a non-blocking request by sending with send_message("channel", SICRequest()), but this
is somewhat discouraged as it may lead to harder to understand behaviour. The same goes for sending messages
to request handlers with

"""
import atexit
import os
import threading
import time

import redis
import six
from sic_framework.core.message_python2 import SICMessage, SICRequest
from sic_framework.core.utils import is_sic_instance
from sic_framework.core import utils
from six.moves import queue


class CallbackThread:
    def __init__(self, function, pubsub, thread):
        self.function = function
        self.pubsub = pubsub
        self.thread = thread


# keep track of all redis instances, so we can close them on exit
_sic_redis_instances = []


def cleanup_on_exit():
    for s in _sic_redis_instances:
        s.close()

    time.sleep(.2)
    if len([x.is_alive() for x in threading.enumerate()]) > 1:
        print("Left over threads:")
        for thread in threading.enumerate():
            if thread.is_alive() and thread.name != "SICRedisCleanup":
                print(thread.name, " is still alive")


atexit.register(cleanup_on_exit)


def get_redis_db_ip_password():
    """
    Get the redis db ip and password from environment variables. If not set, use default values.
    """
    host = os.getenv('DB_IP', "127.0.0.1")
    password = os.getenv('DB_PASS', "changemeplease")
    return host, password


class SICRedis:
    """
    A custom version of redis, that more transparently handles the type of communication necessary for SIC. The aim
    is to mostly reduce code duplication, and provide a clear blocking and non-blocking API.

    Redis pubsub API can also be quite fickle due to not-so-useful subscriber messages and blocking behaviour, and
    this is ignored by this extension. Using any other redis functions 'as is' is discouraged.
    """

    def __init__(self, parent_name=None):
        """
        :param parent_name: The name of the module that uses this redis connection, for easier debugging
        """

        self._running_callbacks = []

        # we assume that a password is required
        host, password = get_redis_db_ip_password()

        # Let's try to connect first without TLS / working without TLS facilitates simple use of redis-cli
        try:
            self._redis = redis.Redis(host=host, ssl=False, password=password)
        except redis.exceptions.AuthenticationError:
            # redis is running without a password, do not supply it.
            self._redis = redis.Redis(host=host, ssl=False)
        except redis.exceptions.ConnectionError as e:
            # Must be a connection error; so now let's try to connect with TLS
            ssl_ca_certs = os.path.join(os.path.dirname(__file__), 'cert.pem')
            print('TLS required. Looking for certificate here:', ssl_ca_certs, "(Source error {})".format(e))
            self._redis = redis.Redis(host=host, ssl=True, ssl_ca_certs=ssl_ca_certs, password=password)

        try:
            self._redis.ping()
        except redis.exceptions.ConnectionError:
            e = Exception("Could not connect to redis at {} \n\n Have you started redis? Use: `redis-server conf/redis/redis.conf`".format(host))
            # six.raise_from(e, None) # unsupported on some peppers
            six.reraise(Exception, e, None)

        # To be set by any component that requires exceptions in the callback threads to be logged to somewhere
        self.parent_logger = None

        # service name (assigned to thread to help debugging)
        self.service_name = parent_name

        _sic_redis_instances.append(self)

    def register_message_handler(self, channels, callback, ignore_requests=True):
        """
        Subscribe a callback function to one or more channels, and also start a thread to monitor for new messages.
        By default, ignores SICRequests.
        :param callback: a function expecting a SICMessage and a channel argument to process the messages received on `channel`
        :param channels: channel or channels to listen to
        :param ignore_requests: Flag to control whether the message handler should also trigger the callback if the
                                message is a SICRequest
        :return: The CallbackThread object containing the the thread that is listening to the channel.
        """

        # convert single channel case to list of channels case
        channels = utils.str_if_bytes(channels)
        if isinstance(channels, six.text_type):
            channels = [channels]

        assert len(channels), "Must provide at least one channel"

        # ignore subscribers messages as to not trigger the callback with useless information
        pubsub = self._redis.pubsub(ignore_subscribe_messages=True)

        # unpack pubsub message to SICMessage
        def wrapped_callback(pubsub_msg):
            try:
                sic_message = self.parse_pubsub_message(pubsub_msg)

                if ignore_requests and is_sic_instance(sic_message, SICRequest):
                    return

                return callback(sic_message)
            except Exception as e:
                # Errors in a remote thread fail silently, so explicitly catch anything and log to the user.
                if self.parent_logger:
                    self.parent_logger.exception(e)
                raise e

        channels = [utils.str_if_bytes(c) for c in channels]

        pubsub.subscribe(**{c: wrapped_callback for c in channels})

        # sleep_time is how often the thread checks if the connection is still alive (and checks the stop condition),
        # if it is 0.0 it can never time out. It can receive messages much faster, so be nice to the CPU.
        thread = pubsub.run_in_thread(sleep_time=0.1, daemon=True)

        if self.service_name:
            thread.name = "{}_callback_thread".format(self.service_name)

        c = CallbackThread(callback, pubsub=pubsub, thread=thread)
        self._running_callbacks.append(c)

        return c

    def unregister_callback(self, callback_thread):
        """
        Unhook a callback by unsubscribing from redis and stopping the thread. Will unregister all hooks if
        multiple hooks are created.
        :param callback_thread: The CallbackThread to unregister
        """

        callback_thread.pubsub.unsubscribe()
        callback_thread.thread.stop()
        self._running_callbacks.remove(callback_thread)

    def send_message(self, channel, message):
        """
        Send a SICMessage to a service/device listening on the channel.
        :param channel: The redis pubsub channel to communicate on.
        :param message: The message
        :return: The number of subscribers that received the message.
        """
        assert isinstance(message, SICMessage), "Message must inherit from SICMessage (got {})".format(type(message))

        return self._redis.publish(channel, message.serialize())

    def _reply(self, channel, request, reply):
        """
        Send a reply to a specific request. This is done by sending a SICMessage to the same channel, where
        the requesting thread/client is waiting for the reply.
        :param channel: The redis pubsub channel to communicate on.
        :param request: The SICRequest
        :param reply: The SICMessage reply to send back to the requesting client.
        """
        # auto-reply to the request if the request id is not set. Used for example when a service manager
        # does not want to reply to a request, so a reply is returned but its not a reply to the request
        if reply._request_id is None:
            reply._request_id = request._request_id
        self.send_message(channel, reply)

    def request(self, channel, request, timeout=5, block=True):
        """
        Send a request, and wait for the reply on the same channel. If the reply takes longer than
        `timeout` seconds to arrive, a TimeoutError is raised. If block is set to false, the reply is
        ignored and the function returns immediately.
        :param channel: The redis pubsub channel to communicate on.
        :param request: The SICRequest
        :param timeout: Timeout in seconds in case the reply takes too long.
        :param block: If false, immediately returns None after sending the request.
        :return: the SICMessage reply
        """

        if request._request_id is None:
            raise ValueError("Invalid request id for request {}".format(request.get_message_name()))

        # Set up a callback to listen to the same channel, where we expect the reply.
        # Once we have the reply the queue passes the data back to this thread and the
        # event signals we have received the reply. Subscribe first, as to not miss it
        # if the reply is faster than our subscription.
        done = threading.Event()
        q = queue.Queue(1)

        def await_reply(reply):
            # If not our own request but is a SICMessage with the right id, then it is the reply
            # we are waiting for
            if not is_sic_instance(reply, SICRequest) and reply._request_id == request._request_id:
                q.put(reply)
                done.set()

        if block:
            callback_thread = self.register_message_handler(channel, await_reply)

        self.send_message(channel, request)

        if not block:
            return None

        else:

            done.wait(timeout)

            if not done.is_set():
                raise TimeoutError("Waiting for reply to {} to request timed out".format(request.get_message_name()))

            # cleanup by unsubscribing and stopping the subscriber thread
            self.unregister_callback(callback_thread)

            return q.get()

    def register_request_handler(self, channel, callback):
        """
        Register a function to listen to SICRequest's (and ignore SICMessages). Handler must return a SICMessage as a reply.
        Will block receiving new messages until the callback is finished.
        :param channel: The redis pubsub channel to communicate on.
        :param callback: function to run upon receiving a SICRequest. Must return a SICMessage reply
        """

        def wrapped_callback(request):
            if is_sic_instance(request, SICRequest):
                reply = callback(request)

                assert not is_sic_instance(reply, SICRequest) and is_sic_instance(reply, SICMessage), \
                    "Request handler callback must return a SICMessage but not SICRequest, " \
                    "received: {}".format(type(reply))

                self._reply(channel, request, reply)

        return self.register_message_handler(channel, wrapped_callback, ignore_requests=False)

    def time(self):
        return self._redis.time()

    def close(self):
        """
        Cleanup function to stop listening to all callback channels and disconnect redis.
        """
        for c in self._running_callbacks:
            c.pubsub.unsubscribe()
            c.thread.stop()
        self._redis.close()

    def __del__(self):
        # we can no longer unregister_message_handler as python is shutting down, but we can still stop
        # any remaining threads
        for c in self._running_callbacks:
            c.thread.stop()

    @staticmethod
    def parse_pubsub_message(pubsub_msg):
        """
        Convert a redis pub/sub message to a SICMessage (sub)class.
        :param pubsub_msg:
        :return:
        """
        type_, channel, data = pubsub_msg["type"], pubsub_msg["channel"], pubsub_msg["data"]

        if type_ == "message":
            message = SICMessage.deserialize(data)
            return message

        return None


if __name__ == '__main__':
    class NamedMessage(SICMessage):
        def __init__(self, name):
            self.name = name


    class NamedRequest(NamedMessage, SICRequest):
        pass


    r = SICRedis()


    def do(channel, message):
        print("do", message.name)

    # print("Message callback:")
    # r.register_message_handler("service", do, )
    # r.send_message("service", NamedMessage("abc"))
    #
    #
    # def do_reply(channel, message):
    #     print("do_reply", message.name)
    #     return NamedMessage("reply" + message.name)
    #
    #
    # print("\n\nRequest handling")
    #
    # r.register_request_handler("device", do_reply)
    # reply = r.request("device", NamedRequest("req_handling"), timeout=5)
    # print("reply:", reply.name)
    #
    # print("\n\nincorrect handler: ", )
    # try:
    #     r.register_message_handler("a", do_reply)
    #     reply = r.request("a", NamedRequest("req_incorrect_handler"), timeout=1)
    #     print("reply:", reply.name)
    # except TimeoutError as e:
    #     print("success")
    #
    # print("\n\nduplicate handler")
    # r.register_request_handler("b", do_reply)
    # r.register_message_handler("b", do)
    # reply = r.request("b", NamedRequest("req_duplicate_handler"), timeout=5)
    # print("reply:", reply.name)
    #
    # print("\n\ncallbacks")
    # for k in r._running_callbacks:
    #     print(k.function)
    #
    # print("\n\nSpeed:")
    #
    # r.register_request_handler("c", lambda *args: SICMessage())
    # start = time.time()
    # for i in range(100):
    #     reply = r.request("c", NamedRequest("req_duplicate_handler"), timeout=5)
    # print("100 request took", time.time() - start)
    #
    # start = time.time()
    # for i in range(100):
    #     r.send_message("d", SICMessage())
    # print("100 send_message took", time.time() - start)

    # print("Test callback blocking behaviour")
    #
    #
    # def do_reply_slow(channel, message):
    #     print("do_reply", message.name)
    #     time.sleep(5)
    #     return NamedMessage("reply " + message.name)
    #
    #
    # r.register_request_handler("f", do_reply_slow)
    #
    # for i in range(5):
    #     reply = r.request("f", NamedRequest(f"fast{i}"), timeout=6)
    #     print(reply.name)
    #
    # r.close()
