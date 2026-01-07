from app.ai.gemini_client import generate_embedding, generate_text
from app.core.qdrant import get_qdrant_client, create_collection_if_not_exists
from qdrant_client.models import PointStruct
import logging
import uuid

logger = logging.getLogger(__name__)

COLLECTION_NAME = "test_travel_guides"


def setup_test_collection():
    """
    Create a test collection and insert sample travel data
    """
    # Create collection (768 dimensions for Gemini embeddings)
    create_collection_if_not_exists(COLLECTION_NAME, vector_size=768)
    
    # Sample travel guide texts
    sample_texts = [
        "Paris is known for the Eiffel Tower, Louvre Museum, and delicious pastries. Best time to visit is spring or fall.",
        "Tokyo offers amazing sushi, beautiful temples, and vibrant street culture. Don't miss Shibuya Crossing and Senso-ji Temple.",
        "New York City has iconic landmarks like Times Square, Central Park, and the Statue of Liberty. Great pizza and bagels!",
        "Bali is perfect for beach lovers with stunning sunsets, rice terraces, and Hindu temples. Try local Nasi Goreng.",
    ]
    
    client = get_qdrant_client()
    
    # Embed and insert each text
    points = []
    for idx, text in enumerate(sample_texts):
        logger.info(f"Embedding text {idx + 1}/{len(sample_texts)}...")
        embedding = generate_embedding(text)
        
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"text": text, "index": idx}
        )
        points.append(point)
    
    # Upsert all points
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info(f"✅ Inserted {len(points)} sample travel guides into Qdrant")


def search_travel_guides(query: str, top_k: int = 2):
    """
    Search for relevant travel guides using semantic search
    
    Args:
        query: User's search query
        top_k: Number of results to return
        
    Returns:
        List of relevant texts
    """
    # Embed the query
    query_embedding = generate_embedding(query)
    
    # Search in Qdrant
    client = get_qdrant_client()
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding,
        limit=top_k
    )
    
    # Extract texts
    retrieved_texts = [hit.payload["text"] for hit in results]
    return retrieved_texts


def rag_query(user_question: str) -> str:
    """
    Answer a question using RAG (Retrieval-Augmented Generation)
    
    Args:
        user_question: User's question about travel
        
    Returns:
        AI-generated answer grounded in retrieved context
    """
    logger.info(f"RAG Query: {user_question}")
    
    # Step 1: Retrieve relevant context
    retrieved_docs = search_travel_guides(user_question, top_k=2)
    context = "\n\n".join(retrieved_docs)
    
    logger.info(f"Retrieved {len(retrieved_docs)} documents")
    
    # Step 2: Generate answer using Gemini with context
    prompt = f"""You are a helpful travel assistant. Answer the user's question using ONLY the information provided in the context below. If the context doesn't contain enough information, say so.

Context:
{context}

Question: {user_question}

Answer:"""
    
    answer = generate_text(prompt)
    return answer
