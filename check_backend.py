#!/usr/bin/env python3
"""Quick script to check if backend is accessible and CORS is configured"""

import requests

BACKEND_URL = "https://pdf-chatbot-kktm.onrender.com"

print("🔍 Checking backend status...\n")

# Check if backend is up
try:
    print(f"1. Testing backend health: {BACKEND_URL}/docs")
    response = requests.get(f"{BACKEND_URL}/docs", timeout=10)
    if response.status_code == 200:
        print("   ✅ Backend is UP and responding")
    else:
        print(f"   ⚠️  Backend returned status: {response.status_code}")
except requests.exceptions.Timeout:
    print("   ❌ Backend is not responding (timeout)")
    print("   💡 Render free tier may be sleeping - wait 30 seconds and try again")
except requests.exceptions.ConnectionError:
    print("   ❌ Cannot connect to backend")
    print("   💡 Check if backend is deployed on Render")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check CORS with OPTIONS request
print(f"\n2. Testing CORS configuration")
try:
    headers = {
        "Origin": "https://pdfchatbot1.netlify.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    response = requests.options(
        f"{BACKEND_URL}/api/v1/auth/register",
        headers=headers,
        timeout=10
    )
    
    cors_header = response.headers.get("Access-Control-Allow-Origin")
    if cors_header:
        print(f"   ✅ CORS is configured: {cors_header}")
    else:
        print("   ❌ CORS header missing - backend needs to be redeployed")
        print("   💡 Go to Render dashboard and manually deploy")
        
except Exception as e:
    print(f"   ❌ CORS check failed: {e}")

print("\n" + "="*60)
print("NEXT STEPS:")
print("="*60)
print("1. Go to: https://dashboard.render.com")
print("2. Find: pdf-chatbot-backend")
print("3. Click: 'Manual Deploy' → 'Deploy latest commit'")
print("4. Wait: ~5-10 minutes for deployment")
print("5. Run this script again to verify")
print("="*60)
