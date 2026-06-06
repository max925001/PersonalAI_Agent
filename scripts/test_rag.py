import asyncio
import uuid
from app.core.config import settings
from app.infrastructure.persistence.mongodb.database import init_database, close_connections
from app.infrastructure.web.dependencies import get_agent_use_case
from app.application.chat.dtos import ChatRequest

async def main():
    print("Initializing MongoDB Atlas connection...")
    await init_database()
    
    # Instantiate the agent use case via the dependencies provider
    print("Initializing AgentUseCase and nodes...")
    use_case = get_agent_use_case()
    
    # 1. Test case: Query RAG
    session_id = str(uuid.uuid4())
    message = "Tell me about Shivam"
    print(f"\nExecuting chat query for session {session_id}: '{message}'...")
    
    try:
        result = await use_case.execute(session_id=session_id, message=message)
        print("\n--- RAG Response Result ---")
        print(f"Response: {result['response']}")
        print(f"Confidence Score: {result['confidence_score']}")
        print(f"Sources count: {len(result['sources'])}")
        print(f"Elapsed Time: {result['elapsed_time_seconds']:.4f}s")
        print("----------------------------")
    except Exception as e:
        print(f"Test failed with unexpected error: {e}")

    close_connections()

if __name__ == "__main__":
    asyncio.run(main())
