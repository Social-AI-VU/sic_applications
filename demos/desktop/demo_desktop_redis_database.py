# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

from sic_framework.services.database.redis_database import (
    RedisDatabaseConf,
    RedisDatabase,
    SetUsermodelValuesRequest,
    GetUsermodelValuesRequest,
    UsermodelKeyValuesMessage
)


class DatabaseDemo(SICApplication):
    """
    Redis local persistent database demo.

    IMPORTANT
    1. run the persistent local redis database
        - Windows: ./conf/redis.exe conf/redis-store.conf
    2.run the database service: run-database-redis
    """

    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(DatabaseDemo, self).__init__()

        self.database = None

        # Configure logging
        self.set_log_level(sic_logging.DEBUG)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        self.set_log_file("C:/Users/mlt222/repositories/sic_v2/sic_applications/logs")

        self.setup()

    def setup(self):
        """Initialize and configure redis database."""
        redisDatabaseConf = RedisDatabaseConf(
            password="changemeplease",
            version="demo",
            developer_id="0"
        )
        self.database = RedisDatabase(conf=redisDatabaseConf)
        self.database.register_callback(callback=self.on_data_received)

    def on_data_received(self, data):
        if isinstance(data, UsermodelKeyValuesMessage):
            self.logger.info(f'Data received for {data.user_id}: {data.keyvalues}')
        else:
            self.logger.info(f'Database request returned {data}')

    def run(self):
        """Main demo code."""
        try:
            demo_user = 'demo_user'
            demo_user_model = {
                'key_1': 'value_1',
                'key_2': 'value_2',
                'key_3': 'value_3'
            }
            self.logger.info(f'Sending user model to Redis Database')
            self.database.request(SetUsermodelValuesRequest(user_id=demo_user,
                                                            keyvalues=demo_user_model))

            self.logger.info('Retrieving user model data from Redis Database')
            self.database.request(GetUsermodelValuesRequest(user_id=demo_user,
                                                            keys=['key_2', 'key_3']))
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = DatabaseDemo()
    demo.run()
