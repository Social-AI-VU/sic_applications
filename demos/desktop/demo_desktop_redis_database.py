# Import basic preliminaries
from time import sleep
from pathlib import Path
from dotenv import load_dotenv

from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

from sic_framework.services.database.redis_database import (
    RedisDatabaseConf,
    RedisDatabase,
    SetUsermodelValuesRequest,
    GetUsermodelValuesRequest,
    UsermodelKeyValuesMessage,
    DeleteUsermodelValuesRequest,
    GetUsermodelRequest,
    DeleteNamespaceRequest,
    SICSuccessMessage
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
        self.set_log_level(sic_logging.INFO)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("")


        # Load environment variables
        env_path = Path(__file__).parent.parent.parent / "conf" / ".env"
        load_dotenv(env_path)
        
        self.setup()

    def setup(self):
        """Initialize and configure redis database."""
        redis_database_conf = RedisDatabaseConf(
            password="changemeplease",
            version="demo",
            developer_id=0
        )
        self.database = RedisDatabase(conf=redis_database_conf)

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
            response = self.database.request(GetUsermodelValuesRequest(user_id=demo_user,
                                                                       keys=['key_2', 'key_3']))
            self.logger.info(f'Retrieved user model data for user {response.user_id} '
                             f'from Redis Database: {response.keyvalues}')

            self.logger.info(f'Deleting key-value pair from user model')
            response = self.database.request(DeleteUsermodelValuesRequest(user_id=demo_user,
                                                                          keys=['key_2']))
            if isinstance(response, SICSuccessMessage):
                self.logger.info('Key-value pair was successfully deleted from user model')

            self.logger.info('Retrieve full user model for user')
            response = self.database.request(GetUsermodelRequest(user_id=demo_user))
            self.logger.info(f'Full user model for user {response.user_id} '
                             f'from Redis Database: {response.keyvalues}')

            self.logger.info(f'Clearing full database')
            self.database.request(DeleteNamespaceRequest())
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = DatabaseDemo()
    demo.run()
