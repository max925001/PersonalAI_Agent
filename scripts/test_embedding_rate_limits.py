import asyncio
import sys
import time
from loguru import logger

# Set PYTHONPATH
import os
sys.path.append(os.getcwd())

from app.infrastructure.web.dependencies import get_embedding_port
from app.application.profile.embedding_service import EmbeddingService

async def main():
    logger.info("Initializing HuggingFace/configured Embedding Adapter...")
    adapter = get_embedding_port()
    
    logger.info("Initializing Embedding Service...")
    service = EmbeddingService(adapter, batch_size=20)
    
    # Generate 193 mock chunks to simulate a real profile ingestion payload
    logger.info("Generating 193 mock chunks...")
    chunks = []
    for i in range(193):
        chunks.append({
            "id": i,
            "text": f"This is chunk number {i}. We are testing the local embedding adapter speed and batching logic in AI Shivam digital twin application. Text needs to be somewhat realistic to represent standard resume or github sync text content.",
            "metadata": {
                "source_type": "test",
                "source_id": "test_id"
            }
        })
        
    start_time = time.time()
    logger.info("Starting embedding generation for 193 chunks...")
    
    try:
        embedded_chunks = await service.embed_chunks(chunks)
        duration = time.time() - start_time
        logger.info(f"✅ Success! Embedded {len(embedded_chunks)} chunks successfully in {duration:.2f} seconds.")
        
        # Verify a few vectors
        for idx in [0, 50, 100, 150, 192]:
            vector = embedded_chunks[idx].get("vector")
            if vector and len(vector) == 384:
                logger.info(f"Chunk {idx} vector verified: length={len(vector)}, type={type(vector)}")
            else:
                logger.error(f"❌ Chunk {idx} vector verification failed! Vector={vector}")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
