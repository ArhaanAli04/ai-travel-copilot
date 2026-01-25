from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service

# Search for enriched POIs
query = "popular restaurant locals recommend"
query_vector = embedding_service.generate_single_embedding(
    query,
    task_type="RETRIEVAL_QUERY"
)

results = qdrant_service.search(
    collection_name="local_discovery",
    query_vector=query_vector,
    limit=5,
    filter={"must": [{"key": "city", "match": {"value": "mumbai"}}]}
)

print("Search results for 'popular restaurant locals recommend':\n")
for i, result in enumerate(results, 1):
    payload = result['payload']
    print(f"{i}. {payload['name']} (score: {result['score']:.3f})")
    print(f"   Source: {payload['source']}")
    print(f"   Has Foursquare: {payload.get('has_foursquare_data', False)}")
    if payload.get('has_foursquare_data'):
        print(f"   Rating: {payload.get('fsq_rating', 'N/A')}")
    print(f"   Description: {payload['description'][:150]}...")
    print()
