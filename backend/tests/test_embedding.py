"""
Unit tests for embedding service
"""
from app.services.embedding_service import embedding_service

def test_query_embedding():
    """Test embedding a single query"""
    print("=" * 60)
    print("🧪 Test: Query Embedding")
    print("=" * 60)
    
    query = "best restaurants in Paris"
    embedding = embedding_service.embed_query(query)
    
    print(f"✅ Query: {query}")
    print(f"✅ Embedding dimension: {len(embedding)}")
    print(f"✅ First 5 values: {embedding[:5]}")
    
    assert len(embedding) == 3072, "Embedding should be 3072 dimensions"
    assert all(isinstance(x, float) for x in embedding), "All values should be floats"
    
    print("✅ Test passed!")

def test_chunk_embedding():
    """Test embedding multiple chunks"""
    print("\n" + "=" * 60)
    print("🧪 Test: Chunk Embedding")
    print("=" * 60)
    
    test_chunks = [
        {"content": "The Eiffel Tower is a famous landmark in Paris."},
        {"content": "French cuisine is known for its pastries and wines."},
        {"content": "The Louvre Museum houses thousands of artworks."}
    ]
    
    embedded = embedding_service.embed_chunks(test_chunks)
    
    print(f"✅ Input chunks: {len(test_chunks)}")
    print(f"✅ Embedded chunks: {len(embedded)}")
    
    for i, chunk in enumerate(embedded):
        print(f"   Chunk {i+1}: {len(chunk['embedding'])} dimensions")
        assert 'embedding' in chunk, "Chunk should have embedding field"
        assert len(chunk['embedding']) == 3072, "Embedding should be 3072 dimensions"
    
    print("✅ Test passed!")

if __name__ == "__main__":
    print("\n🧪 Embedding Service Tests\n")
    
    try:
        test_query_embedding()
        test_chunk_embedding()
        
        print("\n" + "=" * 60)
        print("✅ All embedding tests passed!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
