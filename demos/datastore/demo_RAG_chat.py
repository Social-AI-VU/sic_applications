import os
from pathlib import Path
from dotenv import load_dotenv

from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

from sic_framework.services.datastore.redis_datastore import (
    RedisDatastoreConf,
    RedisDatastore,
    IngestVectorDocsRequest,
    QueryVectorDBRequest,
    VectorDBResultsMessage,
    DeleteNamespaceRequest,
    SICSuccessMessage
)

from sic_framework.services.llm import GPT, GPTConf, GPTRequest


class RAGChatDemo(SICApplication):
    """
    RAG Chat Demo: Conversational AI with Document Search

    This demo combines document retrieval with LLM chat to create a chatbot that can
    answer questions using information from ingested PDF documents.

    For more details on how to ingest/query the vector database, see the demo_RAG.py file.

    The demo shows:
    - Document ingestion with vector embeddings
    - Semantic search to find relevant context
    - Streaming LLM responses using the SIC GPT service
    - Multi-turn conversation with context

    Prerequisites:
    1. Start Redis Stack: docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 -e REDIS_ARGS="--requirepass changemeplease" redis/redis-stack:latest
    2. Set OPENAI_API_KEY in conf/.env
    3. Start the datastore service: run-datastore-redis
    4. Start the GPT service: run-gpt
    5. Install dependencies: pip install social-interaction-cloud[openai-gpt] python-dotenv
    """

    def __init__(self):
        super(RAGChatDemo, self).__init__()
        self.datastore = None
        self.gpt = None
        self.conversation = []
        
        self.set_log_level(sic_logging.INFO)
        
        # Load environment variables
        env_path = Path(__file__).parent.parent.parent / "conf" / ".env"
        load_dotenv(env_path)
        
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            self.logger.error("OPENAI_API_KEY not found in environment")
            raise RuntimeError("OPENAI_API_KEY is required")

        self.setup()

    def setup(self):
        """Initialize connections to Redis datastore and OpenAI GPT service."""
        # Initialize Redis datastore for document storage
        redis_conf = RedisDatastoreConf(
            host="127.0.0.1",
            port=6379,
            password="changemeplease",
            namespace="rag_chat_demo",
            version="v1",
            developer_id=0
        )
        self.datastore = RedisDatastore(conf=redis_conf)
        
        # Initialize SIC GPT service
        gpt_conf = GPTConf(
            openai_key=self.openai_api_key,
            system_message="You are a helpful AI assistant with access to a knowledge base about robotics, NLP, and computer vision. Use the provided context to answer questions accurately and cite sources when possible.",
            model="gpt-4o-mini",
            temp=0.7,
            max_tokens=500,
            response_format=None,
        )
        self.gpt = GPT(conf=gpt_conf)
        
        # Register callback for streaming responses
        self.gpt.register_callback(self._on_stream_chunk)
        
        self.logger.info("Services initialized")

    def _on_stream_chunk(self, message):
        """
        Callback for streaming GPT response chunks.
        
        Prints tokens as they arrive in real-time for a better user experience.
        """
        if not hasattr(message, "response"):
            return
        
        is_chunk = getattr(message, "is_stream_chunk", False)
        
        if is_chunk:
            # Print streaming chunks without newlines
            chunk_text = message.response.replace("\n", " ")
            print(chunk_text, end="", flush=True)
        else:
            # Final response - print newline
            print()

    def ingest_documents(self):
        """Ingest PDF documents from the vector_docs directory."""
        docs_dir = Path(__file__).parent / "vector_docs"
        
        if not docs_dir.exists():
            self.logger.error(f"Documents directory not found: {docs_dir}")
            return False
        
        try:
            result = self.datastore.request(
                IngestVectorDocsRequest(
                    input_path=str(docs_dir),
                    openai_api_key=self.openai_api_key,
                    index_name="rag_chat_demo__docs",
                    partition="demo",
                    glob="**/*.pdf",
                    chunk_chars=800,
                    chunk_overlap=100,
                    embedding_model="text-embedding-3-large",
                    override_existing=True,
                    force_recreate_index=True
                )
            )
            
            if isinstance(result, VectorDBResultsMessage) and result.payload.get('ok'):
                for res in result.payload.get('results', []):
                    self.logger.info(f"  Ingested {res.get('files', 0)} files -> {res.get('chunks', 0)} chunks")
                return True
            
        except Exception as e:
            self.logger.error(f"  Error: {e}")
            return False

    def search_documents(self, query: str, k: int = 3) -> list[dict]:
        """Search for relevant document chunks using semantic similarity."""
        try:
            result = self.datastore.request(
                QueryVectorDBRequest(
                    episode="rag_chat_demo",
                    character="docs",
                    query_text=query,
                    openai_api_key=self.openai_api_key,
                    k=k,
                    partition="demo",
                    index_prefix="",
                    embedding_model="text-embedding-3-large"
                )
            )
            
            if isinstance(result, VectorDBResultsMessage):
                return result.payload.get('results', [])
        
        except Exception as e:
            self.logger.error(f"Search error: {e}")
        
        return []

    def ask_question(self, user_question: str, stream: bool = True) -> str:
        """
        Answer a question using RAG: retrieve relevant docs, then generate response.
        
        Args:
            user_question: The user's question
            stream: Whether to stream the response in real-time
            
        Returns:
            AI assistant's complete response
        """
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"User: {user_question}")
        
        # Step 1: Retrieve relevant document chunks
        self.logger.info("Searching documents...")
        search_results = self.search_documents(user_question, k=3)
        
        if not search_results:
            self.logger.info("  No relevant documents found - using general knowledge")
            context = ""
        else:
            # Build context from search results
            context_parts = []
            for idx, result in enumerate(search_results, 1):
                doc_name = os.path.basename(result.get('doc_path', 'unknown'))
                content = result.get('content', '').strip()
                score = result.get('score', 0)
                
                context_parts.append(f"[Source {idx}: {doc_name}]\n{content}")
                self.logger.info(f"  {doc_name} (relevance: {score:.3f})")
            
            context = "\n\n".join(context_parts)
        
        # Step 2: Build prompt with retrieved context
        if context:
            augmented_prompt = f"""Context from knowledge base:

{context}

Based on the context above, please answer: {user_question}

Cite your sources when using information from the context."""
        else:
            augmented_prompt = user_question
        
        # Add to conversation history
        self.conversation.append({"role": "user", "content": augmented_prompt})
        
        # Step 3: Generate response using SIC GPT service with streaming
        self.logger.info("Assistant:")
        
        try:
            request = GPTRequest(
                prompt=augmented_prompt,
                role_messages=self.conversation,
                stream=stream  # Enable streaming for real-time token display
            )
            
            if stream:
                print("  ", end="", flush=True)  # Position cursor for streaming output
            
            reply = self.gpt.request(request)
            response = reply.response
            
            if not stream:
                # Non-streaming: print complete response
                print(response)
            
            # Add assistant response to conversation history
            self.conversation.append({"role": "assistant", "content": response})
            
            # Keep conversation history manageable (last 8 messages = 4 exchanges)
            if len(self.conversation) > 8:
                self.conversation = self.conversation[-8:]
            
            return response
            
        except Exception as e:
            self.logger.error(f"\nError generating response: {e}")
            return "I'm sorry, I encountered an error generating a response."

    def run_interactive_chat(self):
        """Run an interactive chat session where users ask questions."""
        self.logger.info("\n" + "="*70)
        self.logger.info("RAG Chat Assistant - Ask questions about the documents!")
        self.logger.info("="*70)
        self.logger.info("\nThe knowledge base contains documents about:")
        self.logger.info("  - Natural Language Processing (NLP)")
        self.logger.info("  - Face Detection")
        self.logger.info("  - Social Robotics")
        self.logger.info("\nType 'quit' or 'exit' to end the conversation.\n")
        
        try:
            while not self.shutdown_event.is_set():
                user_input = input("You: ").strip()
                
                if user_input.lower() in {"exit", "quit", "q"}:
                    self.logger.info("Ending chat session...")
                    break
                
                if not user_input:
                    continue
                
                self.ask_question(user_input, stream=True)
                print()  # Add spacing after response
        
        except KeyboardInterrupt:
            self.logger.info("\nChat session interrupted by user")
        except EOFError:
            self.logger.info("\nChat session ended")

    def run(self):
        """Main demo flow."""
        try:
            # Step 1: Ingest documents
            self.logger.info("Step 1: Ingesting PDF documents into vector database...")
            if not self.ingest_documents():
                self.logger.error("Failed to ingest documents. Exiting.")
                return
            
            # Step 2: Run interactive chat
            self.logger.info("\nStep 2: Starting interactive chat session...\n")
            self.run_interactive_chat()
            
            # Step 3: Cleanup
            self.logger.info("\n" + "="*70)
            self.logger.info("=== Cleanup ===")
            response = self.datastore.request(DeleteNamespaceRequest())
            if isinstance(response, SICSuccessMessage):
                self.logger.info("Demo data cleaned up")
                
        except Exception as e:
            self.logger.error(f"Demo error: {e}")
        finally:
            self.shutdown()


if __name__ == "__main__":
    print(__doc__)
    demo = RAGChatDemo()
    demo.run()
