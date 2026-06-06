import asyncio
import sys
import os
import uuid
from loguru import logger

# Set PYTHONPATH
sys.path.append(os.getcwd())

from app.core.config import settings
from app.infrastructure.persistence.mongodb.database import init_database, close_connections

# Import Dependency Resolvers
from app.infrastructure.web.dependencies import (
    get_embedding_port,
    get_vector_db_port,
    get_conversation_repository,
    get_message_repository,
    get_llm_port,
    get_retriever_service,
    get_memory_service,
    get_rag_service,
    get_agent_nodes,
    get_agent_use_case
)

async def main():
    logger.info("Initializing database...")
    await init_database()
    
    logger.info("Resolving Agent dependencies...")
    embedding_port = get_embedding_port()
    vector_db_port = get_vector_db_port()
    
    # Verify singleton reuse
    logger.info(f"Embedding Port Class: {embedding_port.__class__.__name__}")
    logger.info(f"Vector DB Port Class: {vector_db_port.__class__.__name__}")
    
    retriever_service = get_retriever_service(embedding_port, vector_db_port)
    memory_service = get_memory_service(
        get_conversation_repository(),
        get_message_repository()
    )
    rag_service = get_rag_service()
    llm_port = get_llm_port()
    
    agent_nodes = get_agent_nodes(
        retriever_service,
        memory_service,
        rag_service,
        llm_port
    )
    
    use_case = get_agent_use_case(agent_nodes)
    
    # Start a test session with a custom non-UUID session string
    session_id = "custom_shivam_test_session"
    logger.info(f"Starting test chat session with custom session_id: {session_id}")
    
    # Query 0: Greeting test
    query0 = "Hello there!"
    logger.info(f"Query 0: '{query0}'")
    result0 = await use_case.execute(session_id, query0)
    
    print("\n" + "="*50)
    print("RESPONSE 0 (Greeting):")
    print("="*50)
    print(result0["response"])
    print(f"Confidence: {result0['confidence_score']}")
    print(f"Time Taken: {result0['elapsed_time_seconds']:.4f}s")
    print("="*50 + "\n")
    
    # Query 1: Semantic search test
    query1 = "Tell me about Shivam. What are his main skills?"
    logger.info(f"Query 1: '{query1}'")
    result1 = await use_case.execute(session_id, query1)
    
    print("\n" + "="*50)
    print("RESPONSE 1:")
    print("="*50)
    print(result1["response"])
    print(f"Confidence: {result1['confidence_score']}")
    print(f"Time Taken: {result1['elapsed_time_seconds']:.4f}s")
    print(f"Sources: {result1['sources']}")
    print("="*50 + "\n")
    
    # Query 2: Memory/Context tracking test (uses "he" which requires loading session memory)
    query2 = "What projects has he built?"
    logger.info(f"Query 2: '{query2}'")
    result2 = await use_case.execute(session_id, query2)
    
    print("\n" + "="*50)
    print("RESPONSE 2 (With memory context):")
    print("="*50)
    print(result2["response"])
    print(f"Confidence: {result2['confidence_score']}")
    print(f"Time Taken: {result2['elapsed_time_seconds']:.4f}s")
    print(f"Sources: {result2['sources']}")
    print("="*50 + "\n")
    
    # Query 3: Hallucination prevention test (asks about something completely out-of-context)
    query3 = "Who won the FIFA World Cup in 2022?"
    logger.info(f"Query 3: '{query3}'")
    result3 = await use_case.execute(session_id, query3)
    
    print("\n" + "="*50)
    print("RESPONSE 3 (Out of context, should trigger default fallback):")
    print("="*50)
    print(result3["response"])
    print(f"Confidence: {result3['confidence_score']}")
    print(f"Time Taken: {result3['elapsed_time_seconds']:.4f}s")
    print(f"Sources: {result3['sources']}")
    print("="*50 + "\n")

    # Query 4: Scheduling availability lookup test
    query4 = "tell me when i schedule your interview"
    logger.info(f"Query 4: '{query4}'")
    result4 = await use_case.execute(session_id, query4)
    
    print("\n" + "="*50)
    print("RESPONSE 4 (Interview slots):")
    print("="*50)
    print(result4["response"])
    print(f"Confidence: {result4['confidence_score']}")
    print(f"Time Taken: {result4['elapsed_time_seconds']:.4f}s")
    print("="*50 + "\n")
    
    close_connections()

if __name__ == "__main__":
    asyncio.run(main())
