import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

from sic_framework.services.datastore.redis_datastore import (
    RedisDatastoreConf,
    RedisDatastore,
    SetUsermodelValuesRequest,
    GetUsermodelValuesRequest,
    GetUsermodelRequest,
    GetUsermodelKeysRequest,
    DeleteUsermodelValuesRequest,
    DeleteUserRequest,
    DeleteNamespaceRequest,
    IngestVectorDocsRequest,
    QueryVectorDBRequest,
    UsermodelKeyValuesMessage,
    VectorDBResultsMessage,
    SICSuccessMessage
)


class RAGDemo(SICApplication):
    """
    Demonstrates using Redis datastore for RAG (Retrieval-Augmented Generation) scenarios.
    
    This demo shows how to:
    - Ingest PDF documents using built-in vector embedding capabilities
    - Query documents using semantic similarity search
    - Store conversation history and context
    - Track user knowledge states and preferences
    - Manage multi-turn conversations with persistent context
    
    The demo uses the redis_datastore service's built-in features for:
    - PDF text extraction (via pypdf)
    - Text chunking with configurable overlap
    - OpenAI embeddings generation
    - Vector similarity search
    
    Prerequisites:
    1. Start Redis Stack: docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
    2. Set OPENAI_API_KEY environment variable
    3. Start the datastore service: run-redis
    """

    def __init__(self):
        super(RAGDemo, self).__init__()
        self.datastore = None

        self.set_log_level(sic_logging.DEBUG)
        
        env_path = Path(__file__).parent.parent.parent / "conf" / ".env"
        load_dotenv(env_path)

        self.setup()

    def setup(self):
        """Initialize Redis datastore for RAG."""

        redis_conf = RedisDatastoreConf(
            host="127.0.0.1",
            port=6379,
            password="changemeplease",
            namespace="rag_demo",
            version="v1",
            developer_id=0
        )
        self.datastore = RedisDatastore(conf=redis_conf)
    
    def ingest_pdfs_from_directory(self):
        """Ingest all PDF files from the vector_docs directory using built-in vector RAG."""
        self.logger.info("\n=== Ingesting PDF Documents with Vector Embeddings ===")
        
        docs_dir = os.path.join(os.path.dirname(__file__), 'vector_docs')
        
        if not os.path.exists(docs_dir):
            self.logger.warning(f"Directory not found: {docs_dir}")
            return None
        
        self.logger.info(f"Processing PDFs from: {docs_dir}")
        self.logger.info("Using OpenAI embeddings for semantic search capability")
        
        try:
            result = self.datastore.request(
                IngestVectorDocsRequest(
                    input_path=docs_dir,
                    index_name="rag_demo__docs",
                    partition="demo",
                    glob="**/*.pdf",
                    chunk_chars=1200,
                    chunk_overlap=150,
                    embedding_model="text-embedding-3-large",
                    override_existing=True,
                    force_recreate_index=True
                )
            )
            
            if isinstance(result, VectorDBResultsMessage):
                payload = result.payload
                if payload.get('ok'):
                    for res in payload.get('results', []):
                        self.logger.info(f"Ingested: {res.get('files', 0)} files, {res.get('chunks', 0)} chunks")
                        self.logger.info(f"  Index: {res.get('index', 'unknown')}")
                return result
            
        except Exception as e:
            self.logger.error(f"Error ingesting PDFs: {e}")
            self.logger.info("Make sure OPENAI_API_KEY is set and pypdf is installed")
            return None

    def run(self):
        """Run RAG demo scenarios."""
        try:
            self.ingest_pdfs_from_directory()
            self.demo_semantic_search()
            self.demo_conversation_context()
            self.demo_user_knowledge_state()
            self.demo_multi_turn_conversation()
            self.demo_context_retrieval()
            self.demo_cleanup()
        except Exception as e:
            self.logger.error(f"Demo error: {e}")
        finally:
            self.shutdown()

    def demo_semantic_search(self):
        """Demonstrate semantic search over ingested documents using vector embeddings."""
        self.logger.info("\n=== Semantic Search with Vector Embeddings ===")
        
        queries = [
            "What is natural language processing?",
            "How do robots detect human faces?",
            "Tell me about social robotics"
        ]
        
        for query in queries:
            self.logger.info(f"\nQuery: {query}")
            
            try:
                result = self.datastore.request(
                    QueryVectorDBRequest(
                        episode="rag_demo",
                        character="docs",
                        query_text=query,
                        k=3,
                        partition="demo",
                        index_prefix="",
                        embedding_model="text-embedding-3-large"
                    )
                )
                
                if isinstance(result, VectorDBResultsMessage):
                    payload = result.payload
                    self.logger.info(f"  Found {payload.get('total', 0)} results:")
                    for res in payload.get('results', [])[:3]:
                        self.logger.info(f"    Score: {res.get('score', 0):.4f}")
                        self.logger.info(f"    Doc: {os.path.basename(res.get('doc_path', 'unknown'))}")
                        self.logger.info(f"    Chunk {res.get('chunk_id', 0)}: {res.get('content', '')[:100]}...")
                        
            except Exception as e:
                self.logger.error(f"  Search error: {e}")
                self.logger.info("  Note: Make sure documents were ingested first")

    def demo_document_storage(self):
        """Demonstrate accessing vector search results."""
        self.logger.info("\n=== Vector Database Query Example ===")
        
        try:
            result = self.datastore.request(
                QueryVectorDBRequest(
                    episode="rag_demo",
                    character="docs",
                    query_text="robotics and human interaction",
                    k=5,
                    partition="demo",
                    embedding_model="text-embedding-3-large"
                )
            )
            
            if isinstance(result, VectorDBResultsMessage):
                payload = result.payload
                self.logger.info(f"Index: {payload.get('index', 'unknown')}")
                self.logger.info(f"Total results: {payload.get('total', 0)}")
                
                for idx, res in enumerate(payload.get('results', []), 1):
                    self.logger.info(f"\nResult {idx}:")
                    self.logger.info(f"  Document: {os.path.basename(res.get('doc_path', 'unknown'))}")
                    self.logger.info(f"  Similarity: {res.get('score', 0):.4f}")
                    self.logger.info(f"  Content: {res.get('content', '')[:150]}...")
        
        except Exception as e:
            self.logger.error(f"Query error: {e}")

    def demo_conversation_context(self):
        """Store and retrieve conversation history for context awareness."""
        self.logger.info("\n=== Managing Conversation Context ===")
        
        conversation_id = 'conv_alice_001'
        
        conversation_data = {
            'user_id': 'alice',
            'start_time': datetime.now(timezone.utc).isoformat(),
            'turn_count': '0',
            'current_topic': 'greetings',
            'sentiment': 'neutral',
            'conversation_history': json.dumps([])
        }
        
        self.datastore.request(
            SetUsermodelValuesRequest(user_id=conversation_id, keyvalues=conversation_data)
        )
        self.logger.info(f"Initialized conversation: {conversation_id}")
        
        turns = [
            {'speaker': 'user', 'text': 'Hello, can you help me with robotics?', 'topic': 'robotics'},
            {'speaker': 'bot', 'text': 'Of course! What would you like to know?', 'topic': 'robotics'},
            {'speaker': 'user', 'text': 'How do robots detect faces?', 'topic': 'face_detection'}
        ]
        
        history = []
        for idx, turn in enumerate(turns):
            history.append(turn)
            
            update = {
                'turn_count': str(idx + 1),
                'current_topic': turn['topic'],
                'conversation_history': json.dumps(history),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            self.datastore.request(
                SetUsermodelValuesRequest(user_id=conversation_id, keyvalues=update)
            )
            self.logger.info(f"Turn {idx+1}: {turn['speaker']} - {turn['text'][:30]}...")
        
        final_context = self.datastore.request(GetUsermodelRequest(user_id=conversation_id))
        self.logger.info(f"Conversation has {final_context.keyvalues['turn_count']} turns")

    def demo_user_knowledge_state(self):
        """Track what topics a user has encountered and their expertise."""
        self.logger.info("\n=== Tracking User Knowledge State ===")
        
        user_id = 'alice'
        
        knowledge_state = {
            'known_topics': json.dumps(['python', 'machine_learning']),
            'learning_goals': json.dumps(['robotics', 'computer_vision']),
            'expertise_level': 'intermediate',
            'questions_asked': '0',
            'topics_explored': json.dumps([])
        }
        
        self.datastore.request(
            SetUsermodelValuesRequest(user_id=user_id, keyvalues=knowledge_state)
        )
        self.logger.info(f"Initialized knowledge state for user: {user_id}")
        
        new_topics = ['face_detection', 'speech_recognition']
        current_state = self.datastore.request(GetUsermodelRequest(user_id=user_id))
        
        topics_explored = json.loads(current_state.keyvalues['topics_explored'])
        topics_explored.extend(new_topics)
        questions_count = int(current_state.keyvalues['questions_asked']) + 2
        
        updates = {
            'topics_explored': json.dumps(topics_explored),
            'questions_asked': str(questions_count),
            'last_active': datetime.now(timezone.utc).isoformat()
        }
        
        self.datastore.request(
            SetUsermodelValuesRequest(user_id=user_id, keyvalues=updates)
        )
        self.logger.info(f"Updated knowledge state - explored topics: {topics_explored}")

    def demo_multi_turn_conversation(self):
        """Simulate a multi-turn conversation with context persistence."""
        self.logger.info("\n=== Multi-Turn Conversation with Context ===")
        
        session_id = 'session_bob_001'
        
        turns = [
            {
                'turn': 1,
                'user_query': 'What is a Pepper robot?',
                'retrieved_docs': json.dumps(['doc_robotics_001']),
                'bot_response': 'Pepper is a humanoid social robot...',
                'user_satisfied': 'true'
            },
            {
                'turn': 2,
                'user_query': 'Can it recognize emotions?',
                'retrieved_docs': json.dumps(['doc_robotics_001', 'doc_ai_002']),
                'bot_response': 'Yes, it has emotion recognition capabilities...',
                'user_satisfied': 'true'
            },
            {
                'turn': 3,
                'user_query': 'How accurate is it?',
                'retrieved_docs': json.dumps(['doc_ai_002']),
                'bot_response': 'The accuracy depends on lighting and distance...',
                'user_satisfied': 'false'
            }
        ]
        
        for turn_data in turns:
            turn_num = turn_data['turn']
            turn_key = f"turn_{turn_num}"
            
            self.datastore.request(
                SetUsermodelValuesRequest(
                    user_id=session_id,
                    keyvalues={
                        turn_key: json.dumps(turn_data),
                        'current_turn': str(turn_num),
                        'last_updated': datetime.now(timezone.utc).isoformat()
                    }
                )
            )
            self.logger.info(f"Turn {turn_num}: {turn_data['user_query'][:40]}...")
        
        session_data = self.datastore.request(GetUsermodelRequest(user_id=session_id))
        self.logger.info(f"Session completed with {session_data.keyvalues['current_turn']} turns")
        
        keys = self.datastore.request(GetUsermodelKeysRequest(user_id=session_id))
        self.logger.info(f"Session keys: {keys.keys}")

    def demo_context_retrieval(self):
        """Retrieve conversation context for generating responses."""
        self.logger.info("\n=== Retrieving Context for Response Generation ===")
        
        session_id = 'session_bob_001'
        
        response = self.datastore.request(
            GetUsermodelValuesRequest(
                user_id=session_id,
                keys=['turn_3', 'current_turn']
            )
        )
        
        if isinstance(response, UsermodelKeyValuesMessage):
            self.logger.info(f"Retrieved context: {response.keyvalues}")
            
            if response.keyvalues['turn_3']:
                turn_3_data = json.loads(response.keyvalues['turn_3'])
                self.logger.info(f"Last turn satisfied: {turn_3_data['user_satisfied']}")
                self.logger.info("Context suggests user needs more detailed answer")

    def demo_delete_operations(self):
        """Clean up specific data."""
        self.logger.info("\n=== Deleting Specific Fields ===")
        
        user_id = 'alice'
        
        response = self.datastore.request(
            DeleteUsermodelValuesRequest(user_id=user_id, keys=['last_active'])
        )
        
        if isinstance(response, SICSuccessMessage):
            self.logger.info(f"Deleted 'last_active' field from {user_id}")

    def demo_cleanup(self):
        """Clean up demo data."""
        self.logger.info("\n=== Cleaning Up Demo Data ===")
        
        response = self.datastore.request(DeleteNamespaceRequest())
        if isinstance(response, SICSuccessMessage):
            self.logger.info("Demo namespace cleaned up successfully")


if __name__ == "__main__":
    demo = RAGDemo()
    demo.run()
