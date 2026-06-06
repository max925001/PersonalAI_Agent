import asyncio
import uuid
from datetime import datetime, timezone
from app.core.config import settings
from app.infrastructure.persistence.mongodb.database import init_database, close_connections
from app.infrastructure.web.dependencies import get_vector_db_port, get_embedding_port

async def main():
    print("Initializing MongoDB Atlas connection...")
    await init_database()
    
    vector_db = get_vector_db_port()
    embedding_port = get_embedding_port()
    
    collection_name = settings.QDRANT_COLLECTION_NAME
    vector_size = embedding_port.dimension
    
    print(f"Targeting Qdrant collection: '{collection_name}'")
    print(f"Targeting vector dimension: {vector_size} (local SentenceTransformers)")
    
    # 1. Recreate collection
    print(f"\nEnsuring collection '{collection_name}' exists with size {vector_size}...")
    await vector_db.ensure_collection(collection_name, vector_size)
    
    # 2. Embed dummy data
    dummy_text = (
        "Shivam Pandey is a Senior Staff Backend Engineer who has successfully created the following 5 projects:\n"
        "1. LMS (Learning Management System): A robust system for managing courses, tracking progress, and online education.\n"
        "2. AI Digital Twin (AI Shivam): An advanced agentic digital twin RAG platform using LangGraph, FastAPI, and Qdrant.\n"
        "3. E-Commerce Microservices API: A scalable distributed API system built using FastAPI for e-commerce transactions.\n"
        "4. mern-chat-app: A real-time chat application created using MongoDB, Express, React, and Node.js.\n"
        "5. hacktoberfest2024: A repository of open-source challenges and projects built for Hacktoberfest 2024.\n"
        "All 5 projects highlight Shivam's capabilities in building production-ready scalable backends, full-stack systems, and RAG pipelines."
    )
    
    print("\nGenerating SentenceTransformers embedding locally...")
    embeddings = await embedding_port.generate_embeddings([dummy_text])
    vector = embeddings[0]
    
    # 3. Seed into Qdrant
    profile_id = str(uuid.uuid4())
    chunk_hash = "sample_chunk_hash_384_001"
    
    sample_chunks = [
        {
            "hash": chunk_hash,
            "text": dummy_text,
            "vector": vector,
            "metadata": {
                "source_type": "addition",
                "source_id": profile_id,
                "repository_name": "ai-shivam-core"
            }
        }
    ]
    
    print("\nUpserting sample chunk into Qdrant...")
    await vector_db.upsert_chunks(collection_name, sample_chunks, profile_id)
    print("Seed complete! Qdrant collection is ready for 384-dimensional queries.")
    
    close_connections()

if __name__ == "__main__":
    asyncio.run(main())

