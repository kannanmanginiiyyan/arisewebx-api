import requests
import json
import time

def test_search_system():
    """Test the search API"""
    
    base_url = "http://localhost:5001"  # Changed from 5000 to 5001
    
    print("=" * 60)
    print("Testing AriseWebX Search System")
    print("=" * 60)
    
    # First check if server is running
    print("\n1. Checking if server is running...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running!")
        else:
            print(f"   ⚠️ Server returned status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Server is not running!")
        print("   Please start the server first: python api_layer.py")
        return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test health
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Status: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test knowledge summary
    print("\n3. Getting knowledge summary...")
    try:
        response = requests.get(f"{base_url}/knowledge/summary", timeout=5)
        if response.status_code == 200:
            summary = response.json()
            print(f"   ✅ Summary found!")
            print(f"   Total chunks: {summary.get('total_chunks', 0)}")
            print(f"   Total entities: {summary.get('total_entities', 0)}")
            print(f"   Chunk types: {summary.get('chunk_types', {})}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test specific questions
    print("\n4. Testing question answering...")
    
    # Test Instagram question
    print("\n   Q: What is your Instagram?")
    try:
        response = requests.post(f"{base_url}/ask", 
                                json={"question": "What is your Instagram?"},
                                headers={"Content-Type": "application/json"},
                                timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"   A: {result['answer']}")
            print(f"   Confidence: {result['confidence']:.2f}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test contact question
    print("\n   Q: How can I contact AriseWebX?")
    try:
        response = requests.post(f"{base_url}/ask", 
                                json={"question": "How can I contact AriseWebX?"},
                                headers={"Content-Type": "application/json"},
                                timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"   A: {result['answer']}")
            print(f"   Confidence: {result['confidence']:.2f}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test search
    print("\n5. Testing search...")
    try:
        response = requests.post(f"{base_url}/search", 
                                json={"query": "instagram", "type": "hybrid", "top_k": 3},
                                headers={"Content-Type": "application/json"},
                                timeout=5)
        if response.status_code == 200:
            results = response.json()
            print(f"   Found {results['total_results']} results")
            for result in results['results']:
                print(f"   - {result['content'][:100]}...")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")
    print("=" * 60)

if __name__ == "__main__":
    time.sleep(1)
    test_search_system()