"""
Demo script to show Redis cache in action
Run this after starting the server to see cache behavior
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000/api/v1"

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def register_and_login():
    """Register and login to get token"""
    print_section("STEP 1: Authentication")
    
    # Register
    register_data = {
        "email": "redis_test@example.com",
        "username": "redis_test",
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=register_data)
        if response.status_code == 200:
            print("✅ User registered")
        else:
            print("ℹ️  User already exists, logging in...")
    except:
        pass
    
    # Login
    login_data = {
        "username": "redis_test",
        "password": "test123"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Logged in successfully")
        return token
    else:
        print("❌ Login failed")
        return None

def send_message(token, session_id, question, message_num):
    """Send a chat message"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "session_id": session_id,
        "question": question,
        "document_ids": []
    }
    
    print(f"\n📤 Sending message {message_num}: '{question}'")
    start_time = time.time()
    
    response = requests.post(f"{BASE_URL}/chat", json=data, headers=headers)
    
    elapsed = (time.time() - start_time) * 1000  # Convert to ms
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Response received in {elapsed:.0f}ms")
        print(f"💬 Answer: {result['answer'][:100]}...")
        return result["session_id"]
    else:
        print(f"❌ Error: {response.status_code}")
        return None

def main():
    print("\n" + "🚀"*40)
    print("  REDIS CACHE DEMONSTRATION")
    print("🚀"*40)
    print("\nThis demo shows Redis cache in action:")
    print("- First message: CACHE MISS (loads from MongoDB)")
    print("- Second message: CACHE HIT (loads from Redis - much faster!)")
    print("\nWatch the server terminal logs to see Redis cache operations!")
    
    # Step 1: Login
    token = register_and_login()
    if not token:
        print("❌ Failed to authenticate")
        return
    
    # Step 2: Send first message (CACHE MISS expected)
    print_section("STEP 2: First Message (CACHE MISS)")
    print("Expected: Load from MongoDB (~50-100ms)")
    print("Watch server logs for: '❌ REDIS CACHE MISS'")
    
    session_id = send_message(
        token, 
        None, 
        "Hello! How are you?",
        1
    )
    
    if not session_id:
        print("❌ Failed to send message")
        return
    
    print(f"\n📝 Session ID: {session_id}")
    
    # Step 3: Send second message (CACHE HIT expected)
    print_section("STEP 3: Second Message (CACHE HIT)")
    print("Expected: Load from Redis (~1-5ms) - Much faster!")
    print("Watch server logs for: '✅ REDIS CACHE HIT'")
    
    time.sleep(1)  # Small delay
    
    send_message(
        token,
        session_id,
        "Can you help me with something?",
        2
    )
    
    # Step 4: Send third message (CACHE HIT expected)
    print_section("STEP 4: Third Message (CACHE HIT)")
    print("Expected: Load from Redis (~1-5ms)")
    print("Watch server logs for: '✅ REDIS CACHE HIT'")
    
    time.sleep(1)
    
    send_message(
        token,
        session_id,
        "Thank you!",
        3
    )
    
    # Summary
    print_section("SUMMARY")
    print("✅ Demo complete!")
    print("\nWhat happened:")
    print("1. First message: Loaded from MongoDB (slower)")
    print("2. Redis cache was populated with the history")
    print("3. Second & third messages: Loaded from Redis (20-100x faster!)")
    print("\nCheck the server terminal to see:")
    print("- 🔍 REDIS CACHE CHECK sections")
    print("- ❌ CACHE MISS (first message)")
    print("- ✅ CACHE HIT (subsequent messages)")
    print("- 💾 REDIS CACHE UPDATE (after each message)")
    print("\n" + "🎉"*40 + "\n")

if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running: uvicorn main:app --port 5000")
    input("Press Enter to start the demo...")
    main()
