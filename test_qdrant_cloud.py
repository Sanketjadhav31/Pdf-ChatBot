"""
Quick test script to verify Qdrant Cloud connection
"""
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

def test_qdrant_cloud():
    """Test connection to Qdrant Cloud"""
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    print("="*80)
    print("🧪 TESTING QDRANT CLOUD CONNECTION")
    print("="*80)
    print(f"URL: {qdrant_url}")
    print(f"API Key: {'*' * 20}{qdrant_api_key[-10:] if qdrant_api_key else 'None'}")
    print("-"*80)
    
    try:
        # Connect to Qdrant Cloud
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        print("✅ Successfully connected to Qdrant Cloud!")
        
        # Get collections
        collections = client.get_collections()
        print(f"\n📚 Collections found: {len(collections.collections)}")
        
        for collection in collections.collections:
            print(f"  - {collection.name}")
            
        print("\n" + "="*80)
        print("✅ QDRANT CLOUD CONNECTION TEST PASSED")
        print("="*80)
        return True
        
    except Exception as e:
        print(f"\n❌ QDRANT CLOUD CONNECTION TEST FAILED")
        print(f"Error: {e}")
        print("="*80)
        return False

if __name__ == "__main__":
    test_qdrant_cloud()
