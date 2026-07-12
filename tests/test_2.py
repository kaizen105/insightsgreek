import requests
import json

# CONFIGURATION
BASE_URL = "https://insightsgreek.onrender.com"  # Change if deployed elsewhere
# BASE_URL = "https://your-render-app.onrender.com"  # For production

# Test credentials (using your seeded data)
USERNAME = "sales"
PASSWORD = "sales123"
ROLE = "salesperson"

# Test data
TEST_LEAD_TEXT = "Loved the demo, budget approved, wants to start next week. Decision maker is very excited!"
TEST_FEEDBACK_TEXT = "I am extremely happy with the support team, they solved my issue quickly and professionally."

def login():
    """Login and get JWT token"""
    print("\n" + "="*60)
    print("STEP 1: LOGGING IN")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": USERNAME, "password": PASSWORD, "role": ROLE}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"✅ Login successful!")
        print(f"Token (first 20 chars): {token[:20]}...")
        return token
    else:
        print(f"❌ Login failed!")
        print(f"Response: {response.text}")
        return None

def test_sentiment_analysis(token):
    """Test sentiment analysis endpoint"""
    print("\n" + "="*60)
    print("STEP 2: TESTING SENTIMENT ANALYSIS")
    print("="*60)
    print(f"Input Text: '{TEST_FEEDBACK_TEXT}'")
    print("-"*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/analyze-feedback",
        headers=headers,
        json={"text": TEST_FEEDBACK_TEXT}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Raw Response: {response.text}")
    
    if response.status_code == 201:
        data = response.json()
        sentiment_result = data.get('sentiment_result', {})
        print("\n📊 SENTIMENT RESULTS:")
        print(f"  - Score: {sentiment_result.get('score')}")
        print(f"  - Label: {sentiment_result.get('label')}")
        
        # Check for issues
        score = sentiment_result.get('score')
        if score is None:
            print("\n❌ ERROR: Score is None!")
        elif score == 0:
            print("\n⚠️  WARNING: Score is 0 (might be incorrect)")
        elif abs(score) < 0.1:
            print("\n⚠️  WARNING: Score is very close to 0")
        else:
            print(f"\n✅ Score looks valid: {score}")
    else:
        print(f"❌ Request failed!")

def test_lead_prediction(token):
    """Test lead prediction endpoint"""
    print("\n" + "="*60)
    print("STEP 3: TESTING LEAD PREDICTION (via submit-lead)")
    print("="*60)
    print(f"Input Text: '{TEST_LEAD_TEXT}'")
    print("-"*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/submit-lead",
        headers=headers,
        json={"text": TEST_LEAD_TEXT}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Raw Response: {response.text}")
    
    if response.status_code == 201:
        data = response.json()
        ml_result = data.get('ml_result', {})
        print("\n🎯 LEAD PREDICTION RESULTS:")
        print(f"  - Score: {ml_result.get('score')}")
        print(f"  - Label: {ml_result.get('label')}")
        
        # Check for issues
        score = ml_result.get('score')
        if score is None:
            print("\n❌ ERROR: Score is None!")
        elif score == 0:
            print("\n⚠️  WARNING: Score is 0 (ML model might not be loaded)")
        elif score < 0.1:
            print("\n⚠️  WARNING: Score is very low (unexpected for positive text)")
        else:
            print(f"\n✅ Score looks valid: {score}")
    else:
        print(f"❌ Request failed!")

def test_standalone_predict(token):
    """Test standalone predict endpoint"""
    print("\n" + "="*60)
    print("STEP 4: TESTING STANDALONE PREDICT ENDPOINT")
    print("="*60)
    print(f"Input Text: '{TEST_LEAD_TEXT}'")
    print("-"*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/predict-lead",
        headers=headers,
        json={"text": TEST_LEAD_TEXT}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Raw Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n🎯 PREDICTION RESULTS:")
        print(f"  - Score: {data.get('score')}")
        print(f"  - Label: {data.get('label')}")
    else:
        print(f"❌ Request failed!")
        if response.status_code == 503:
            print("💡 ML model is not loaded on the server!")

def check_health():
    """Check health endpoint to see service status"""
    print("\n" + "="*60)
    print("STEP 0: CHECKING HEALTH STATUS")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        services = data.get('services', {})
        print("🏥 SERVICE STATUS:")
        print(f"  - Database: {services.get('database')}")
        print(f"  - ML Model: {services.get('ml_model')}")
        print(f"  - Chatbot: {services.get('chatbot')}")
        
        if services.get('ml_model') == 'not_loaded':
            print("\n❌ CRITICAL: ML model is not loaded!")
            print("   This is likely why lead predictions are 0")
    else:
        print(f"❌ Health check failed!")

def main():
    print("\n" + "🔬" + "="*58 + "🔬")
    print("   DEBUGGING SENTIMENT & LEAD PREDICTION ENDPOINTS")
    print("🔬" + "="*58 + "🔬")
    
    # Check health first
    check_health()
    
    # Login
    token = login()
    if not token:
        print("\n❌ Cannot proceed without valid token. Check your credentials!")
        return
    
    # Test both endpoints
    test_sentiment_analysis(token)
    test_lead_prediction(token)
    test_standalone_predict(token)
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)
    print("\n💡 COMMON ISSUES TO CHECK:")
    print("  1. If lead scores are 0: ML model (predict_today.py) not loading")
    print("  2. If sentiment scores are 0: TextBlob not installed or text too short")
    print("  3. Check server logs for 'ML SUCCESS' or 'ML WARNING' messages")
    print("  4. Verify predict_today.py exists in the 'code' directory")
    print("  5. Check if HF_TOKEN is set (for chatbot, not ML)")

if __name__ == "__main__":
    main()