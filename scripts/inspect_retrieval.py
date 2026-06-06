import asyncio
from app.core.config import settings
from app.infrastructure.persistence.mongodb.database import init_database, close_connections
from app.infrastructure.web.dependencies import get_retriever_service, get_rag_service

async def main():
    print("Initializing MongoDB Atlas connection...")
    await init_database()
    
    retriever = get_retriever_service()
    rag = get_rag_service()
    
    query = "tell me the 5 project which is created my shivam "
    print(f"\nRetrieving chunks for query: '{query}'...")
    
    raw_chunks = await retriever.retrieve_context(query)
    print(f"Total raw chunks retrieved: {len(raw_chunks)}")
    
    context_str, sources = rag.build_context(raw_chunks)
    
    # Write to a UTF-8 encoded text file
    output_file = "scripts/retrieval_output.txt"
    print(f"Writing context to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("--- Formatted Context String ---\n")
        f.write(context_str)
        f.write("\n\n--- Sources ---\n")
        f.write(str(sources))
        
    print("Inspection file written successfully!")
    close_connections()

if __name__ == "__main__":
    asyncio.run(main())
