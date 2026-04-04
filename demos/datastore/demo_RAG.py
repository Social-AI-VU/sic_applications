# import demo-specific modules
import os
from pathlib import Path
from dotenv import load_dotenv

# import SIC framework components
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# import services, and message types
from sic_framework.services.datastore.redis_datastore import (
    RedisDatastoreConf,
    RedisDatastore,
    IngestVectorDocsRequest,
    QueryVectorDBRequest,
    VectorDBResultsMessage,
    DeleteNamespaceRequest,
    SICSuccessMessage
)


class RAGDemo(SICApplication):
    """
    Demonstrates vector-based document search using Redis datastore.
    
    This demo shows how to:
    - Ingest PDF documents with automatic text extraction and chunking
    - Generate embeddings using OpenAI
    - Perform semantic similarity search over documents
    
    Prerequisites:
    1. Start Redis Stack: docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
    2. Set OPENAI_API_KEY environment variable (in conf/.env or export)
    3. Start the datastore service: run-redis
    """

    def __init__(self):
        super(RAGDemo, self).__init__()
        self.datastore = None

        self.set_log_level(sic_logging.INFO)
        
        # Load environment variables (including OPENAI_API_KEY)
        env_path = Path(__file__).parent.parent.parent / "conf" / ".env"
        load_dotenv(env_path)
        
        # Get API key from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            self.logger.warning("OPENAI_API_KEY not found in environment")

        self.setup()

    def setup(self):
        """Initialize Redis datastore connection."""
        redis_conf = RedisDatastoreConf(
            host="127.0.0.1",
            port=6379,
            password="changemeplease",
            namespace="rag_demo",
            version="v1",
            developer_id=0
        )
        self.datastore = RedisDatastore(conf=redis_conf)
    
    def ingest_documents(self):
        """
        Ingest PDF documents from the vector_docs directory.
        
        Documents are stored in Redis Stack as follows:
        
        1. **Vector Index**: Created with name "rag_demo_docs"
           - Check indexes: FT._LIST
           - View index info: FT.INFO rag_demo_docs
        
        2. **Document Chunks**: Stored as Redis hashes with keys:
           - Pattern: vec:rag_demo_docs:demo:<file_hash>:<chunk_number>
           - Example: vec:rag_demo_docs:demo:a3f5c8d9e1b2:0
        
        3. **Hash Fields** for each chunk:
           - partition: "demo" (for filtering/isolation)
           - doc_path: Full path to original PDF file
           - chunk_id: Chunk number within the document
           - content: Text content of the chunk
           - embedding: Float32 vector (3072 dimensions for text-embedding-3-large)
        
        4. **Index Schema**: RediSearch creates the following searchable fields:
           - partition (TAG): For filtering by partition
           - doc_path (TEXT): Full-text searchable document path
           - chunk_id (NUMERIC): Chunk number
           - content (TEXT): Full-text searchable content
           - embedding (VECTOR): HNSW index for similarity search
        
        You can inspect the data using redis-cli:
        ```
        # List all indexes
        FT._LIST
        
        # Get index info
        FT.INFO rag_demo_docs
        
        # List all document chunks
        KEYS vec:rag_demo_docs:demo:*
        
        # View a specific chunk
        HGETALL vec:rag_demo_docs:demo:<hash>:0
        ```
        """
        self.logger.info("\n=== Ingesting PDF Documents ===")
        
        if not self.openai_api_key:
            self.logger.error("✗ OPENAI_API_KEY not set")
            self.logger.info("  Set it in conf/.env or: export OPENAI_API_KEY='your-key-here'")
            return None
        
        docs_dir = Path(__file__).parent / "vector_docs"
        
        if not docs_dir.exists():
            self.logger.warning(f"Directory not found: {docs_dir}")
            return None
        
        self.logger.info(f"Processing PDFs from: {docs_dir}")
        self.logger.info("Extracting text, chunking, and generating embeddings...")
        
        try:
            result = self.datastore.request(
                IngestVectorDocsRequest(
                    # Path to directory containing PDFs to ingest
                    input_path=str(docs_dir),
                    
                    # OpenAI API key for generating embeddings
                    openai_api_key=self.openai_api_key,
                    
                    # Redis index name (used for FT.SEARCH queries)
                    # Will create keys like: vec:rag_demo_docs:demo:*
                    index_name="rag_demo_docs",
                    
                    # Logical partition for isolating/filtering documents
                    # Allows multiple document sets in the same index
                    partition="demo",
                    
                    # File glob pattern for matching files to ingest
                    # "**/*.pdf" = recursively find all PDFs in subdirectories
                    glob="**/*.pdf",
                    
                    # Maximum characters per text chunk
                    # Larger chunks = more context, but less granular retrieval
                    chunk_chars=1200,
                    
                    # Character overlap between consecutive chunks
                    # Helps maintain context across chunk boundaries
                    chunk_overlap=150,
                    
                    # OpenAI embedding model to use
                    # text-embedding-3-large = 3072 dimensions, high quality
                    embedding_model="text-embedding-3-large",
                    
                    # Delete existing documents in this partition before ingesting
                    # False = append new docs, True = replace all docs in partition
                    override_existing=True,
                    
                    # Drop and recreate the entire index (destructive!)
                    # True = delete index and all partitions, False = keep existing index
                    force_recreate_index=True
                )
            )
            
            if isinstance(result, VectorDBResultsMessage):
                payload = result.payload
                if payload.get('ok'):
                    for res in payload.get('results', []):
                        self.logger.info(f"✓ Ingested {res.get('files', 0)} files → {res.get('chunks', 0)} chunks")
                        self.logger.info(f"  Index: {res.get('index', 'unknown')}")
                return result
            
        except RuntimeError as e:
            error_msg = str(e)
            if "RediSearch module is not available" in error_msg:
                self.logger.error("✗ RediSearch module not found - Redis Stack required")
                self.logger.info("  Install: docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest")
            elif "openai_api_key parameter is required" in error_msg:
                self.logger.error("✗ OpenAI API key not provided")
                self.logger.info("  Set it in conf/.env or: export OPENAI_API_KEY='your-key-here'")
            elif "Missing dependency: pypdf" in error_msg:
                self.logger.error("✗ pypdf not installed")
                self.logger.info("  Install: pip install pypdf")
            elif "Missing dependency: openai" in error_msg:
                self.logger.error("✗ openai not installed")
                self.logger.info("  Install: pip install openai")
            elif "Missing dependency: numpy" in error_msg:
                self.logger.error("✗ numpy not installed")
                self.logger.info("  Install: pip install numpy")
            else:
                self.logger.error(f"✗ Error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"✗ Unexpected error: {e}")
            return None

    def search_documents(self, query: str, k: int = 3):
        """Search documents using semantic similarity."""
        self.logger.info(f"\nQuery: '{query}'")
        
        if not self.openai_api_key:
            self.logger.error("  ✗ OPENAI_API_KEY not set")
            return
        
        try:
            result = self.datastore.request(
                QueryVectorDBRequest(
                    # Index name components: <index_prefix><episode>__<character>
                    # Results in index name: "rag_demo__docs"
                    episode="rag_demo",
                    character="docs",
                    
                    # The search query text to find similar documents
                    query_text=query,
                    
                    # OpenAI API key for generating query embedding
                    openai_api_key=self.openai_api_key,
                    
                    # Number of top results to return (ranked by similarity)
                    k=k,
                    
                    # Optional: filter results to specific partition
                    # Must match partition used during ingestion
                    partition="demo",
                    
                    # Optional prefix for index name composition
                    # Empty string means no prefix
                    index_prefix="",
                    
                    # Must match the model used during ingestion
                    # to ensure compatible embedding dimensions
                    embedding_model="text-embedding-3-large"
                )
            )
            
            if isinstance(result, VectorDBResultsMessage):
                payload = result.payload
                total = payload.get('total', 0)
                
                if total == 0:
                    self.logger.info("  No results found")
                    return
                
                self.logger.info(f"  Found {total} results:")
                for idx, res in enumerate(payload.get('results', []), 1):
                    score = res.get('score', 0)
                    doc_name = os.path.basename(res.get('doc_path', 'unknown'))
                    content = res.get('content', '')[:120]
                    
                    self.logger.info(f"\n  {idx}. {doc_name} (similarity: {score:.4f})")
                    self.logger.info(f"     {content}...")
                    
        except RuntimeError as e:
            error_msg = str(e)
            if "RediSearch module is not available" in error_msg:
                self.logger.error("  ✗ RediSearch not available")
            elif "openai_api_key parameter is required" in error_msg:
                self.logger.error("  ✗ OpenAI API key not provided")
            elif "does not exist" in error_msg:
                self.logger.error("  ✗ Index not found - run ingestion first")
            else:
                self.logger.error(f"  ✗ Search error: {e}")
        except Exception as e:
            self.logger.error(f"  ✗ Unexpected error: {e}")

    def run(self):
        """Run the RAG demo."""
        try:
            # Step 1: Ingest documents
            result = self.ingest_documents()
            
            if result is None:
                self.logger.error("\nDocument ingestion failed. Fix errors above and try again.")
                return
            
            # Step 2: Perform semantic searches
            self.logger.info("\n=== Semantic Search Examples ===")
            
            queries = [
                "What is natural language processing?",
                "How do robots detect human faces?",
                "Explain social robotics and human-robot interaction"
            ]
            
            for query in queries:
                self.search_documents(query, k=2)
            
            # Step 3: Clean up
            self.logger.info("\n=== Cleanup ===")
            response = self.datastore.request(DeleteNamespaceRequest())
            if isinstance(response, SICSuccessMessage):
                self.logger.info("✓ Demo data cleaned up")
                
        except Exception as e:
            self.logger.error(f"Demo error: {e}")
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = RAGDemo()
    demo.run()
