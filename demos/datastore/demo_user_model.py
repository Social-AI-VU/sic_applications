# import demo-specific modules

# import basic SIC framework components
from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication

# import services, and message types
from sic_framework.services.datastore.redis_datastore import (
    RedisDatastoreConf,
    RedisDatastore,
    SetUsermodelValuesRequest,
    GetUsermodelValuesRequest,
    GetUsermodelKeysRequest,
    GetUsermodelRequest,
    DeleteUsermodelValuesRequest,
    DeleteUserRequest,
    UsermodelKeyValuesMessage,
    UsermodelKeysMessage,
    SICSuccessMessage
)

class UserModelDemo(SICApplication):
    """
    Demonstrates user model management with Redis datastore.
    
    This demo shows how to:
    - Create and store user profiles
    - Update user preferences and interaction history
    - Retrieve specific user data
    - List all keys in a user model
    - Delete specific fields or entire users
    
    Prerequisites:
    1. Start Redis server: redis-server conf/redis-store.conf OR docker run -d --name redis-stack -p 6379:6379 -e REDIS_ARGS="--requirepass changemeplease" -p 8001:8001 redis/redis-stack:latest
    2. Start the datastore service: run-datastore-redis
    """

    def __init__(self):
        super(UserModelDemo, self).__init__()
        self.datastore = None

        self.set_log_level(sic_logging.DEBUG)
        
        # set log file path if needed
        # self.set_log_file_path("/path/to/logs")

        # Load environment variables
        self.load_env("../../conf/.env")
        
        self.setup()

    def setup(self):
        """Initialize Redis datastore connection."""
        redis_conf = RedisDatastoreConf(
            host="127.0.0.1",
            port=6379,
            password="changemeplease",
            namespace="usermodel_demo",
            version="v1",
            developer_id=0
        )
        self.datastore = RedisDatastore(conf=redis_conf)

    def run(self):
        """Demonstrate comprehensive user model operations."""
        try:
            self.demo_create_users()
            self.demo_retrieve_data()
            self.demo_update_preferences()
            self.demo_inspect_keys()
            self.demo_delete_operations()
            self.demo_interaction_tracking()
        except Exception as e:
            self.logger.error(f"Demo error: {e}")
        finally:
            self.shutdown()

    def demo_create_users(self):
        """Create multiple users with initial profiles."""
        self.logger.info("\n=== Creating User Profiles ===")
        
        users = {
            'user_001': {
                'name': 'Alice',
                'age': '28',
                'language': 'en',
                'interaction_count': '0',
                'first_seen': '2026-04-02'
            },
            'user_002': {
                'name': 'Bob',
                'age': '35',
                'language': 'nl',
                'interaction_count': '0',
                'first_seen': '2026-04-02'
            }
        }
        
        for user_id, profile in users.items():
            response = self.datastore.request(
                SetUsermodelValuesRequest(user_id=user_id, keyvalues=profile)
            )
            if isinstance(response, SICSuccessMessage):
                self.logger.info(f"Created profile for {user_id}")

    def demo_retrieve_data(self):
        """Retrieve specific user data."""
        self.logger.info("\n=== Retrieving User Data ===")
        
        response = self.datastore.request(
            GetUsermodelValuesRequest(user_id='user_001', keys=['name', 'language'])
        )
        
        if isinstance(response, UsermodelKeyValuesMessage):
            self.logger.info(f"User {response.user_id} data: {response.keyvalues}")

    def demo_update_preferences(self):
        """Update user preferences and interaction count."""
        self.logger.info("\n=== Updating User Preferences ===")
        
        updates = {
            'language': 'de',
            'interaction_count': '5',
            'last_interaction': '2026-04-02T10:30:00'
        }
        
        response = self.datastore.request(
            SetUsermodelValuesRequest(user_id='user_001', keyvalues=updates)
        )
        
        if isinstance(response, SICSuccessMessage):
            self.logger.info("Updated user preferences")
            
            full_model = self.datastore.request(GetUsermodelRequest(user_id='user_001'))
            self.logger.info(f"Updated profile: {full_model.keyvalues}")

    def demo_inspect_keys(self):
        """List all keys in a user model."""
        self.logger.info("\n=== Inspecting User Model Keys ===")
        
        response = self.datastore.request(GetUsermodelKeysRequest(user_id='user_002'))
        
        if isinstance(response, UsermodelKeysMessage):
            self.logger.info(f"User {response.user_id} has keys: {response.keys}")

    def demo_delete_operations(self):
        """Demonstrate deleting fields and users."""
        self.logger.info("\n=== Delete Operations ===")
        
        self.logger.info("Deleting 'age' field from user_002")
        response = self.datastore.request(
            DeleteUsermodelValuesRequest(user_id='user_002', keys=['age'])
        )
        
        if isinstance(response, SICSuccessMessage):
            model = self.datastore.request(GetUsermodelRequest(user_id='user_002'))
            self.logger.info(f"User model after deletion: {model.keyvalues}")
        
        self.logger.info("Deleting entire user_002")
        response = self.datastore.request(DeleteUserRequest(user_id='user_002'))
        
        if isinstance(response, SICSuccessMessage):
            self.logger.info("User_002 deleted successfully")

    def demo_interaction_tracking(self):
        """Track user interactions over time."""
        self.logger.info("\n=== Tracking User Interactions ===")
        
        user_id = 'user_003'
        
        for i in range(3):
            interaction_data = {
                'name': 'Charlie',
                'last_interaction': f'2026-04-02T10:{30+i}:00',
                'interaction_count': str(i + 1),
                'last_topic': ['greetings', 'weather', 'goodbye'][i]
            }
            
            self.datastore.request(
                SetUsermodelValuesRequest(user_id=user_id, keyvalues=interaction_data)
            )
            self.logger.info(f"Interaction {i+1} recorded")
        
        final_model = self.datastore.request(GetUsermodelRequest(user_id=user_id))
        self.logger.info(f"Final user model: {final_model.keyvalues}")


if __name__ == "__main__":
    demo = UserModelDemo()
    demo.run()
