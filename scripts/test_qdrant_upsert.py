import asyncio
import sys
from loguru import logger

# Set PYTHONPATH
import os
sys.path.append(os.getcwd())

from app.infrastructure.persistence.qdrant.qdrant_adapter import QdrantAdapter

async def main():
    logger.info("Initializing Qdrant Adapter...")
    adapter = QdrantAdapter()
    
    logger.info("Ensuring collection...")
    await adapter.ensure_collection('shivam_knowledge_base', 384)
    
    # Generate 194 mock chunks
    logger.info("Generating 194 mock chunks...")
    chunks = []
    for i in range(194):
        chunks.append({
            'hash': f'test_hash_{i}',
            'vector': [0.1] * 384,
            'text': f'This is chunk number {i} mock text content for testing bulk upsert to Qdrant Cloud cluster in AI Shivam digital twin application.',
            'metadata': {
                'source_type': 'test',
                'source_id': 'test_id',
                'repository_name': 'test_repo',
                'content_hash': 'test_content_hash'
            }
        })
        
    logger.info("Running upsert for 194 points...")
    try:
        await adapter.upsert_chunks(
            'shivam_knowledge_base',
            chunks,
            '9b0a9ed8-2783-49cb-8c32-97355accfd15'
        )
        logger.info("✅ Bulk upsert completed successfully!")
    except Exception as e:
        logger.error(f"❌ Upsert failed!")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
