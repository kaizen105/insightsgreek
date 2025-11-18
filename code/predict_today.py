import os
import requests

# 1. Get Token
HF_TOKEN = os.environ.get('HF_TOKEN')

# 2. Point to YOUR Hosted Model
# This is the exact repo from your screenshot
MODEL_REPO = "kaizen696/my_lead_model"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_REPO}"

def load_model():
    # We don't need to load anything locally!
    if not HF_TOKEN:
        print("❌ Error: HF_TOKEN not found.")
        return None
    print(f"✅ Using Hosted Model: {MODEL_REPO}")
    return True 

def predict_probability(model, text):
    """
    Sends text to your hosted Hugging Face model.
    """
    if not HF_TOKEN: return 0.0

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": text}

    try:
        # Call the API
        response = requests.post(API_URL, headers=headers, json=payload)
        result = response.json()

        # Handle model loading state (503 error)
        if 'error' in result and 'loading' in result['error']:
            print("⏳ Model is loading on HF servers... waiting...")
            return 0.0 # Or retry logic

        # Parse the result
        # Your model likely returns: [[{'label': 'LABEL_1', 'score': 0.99}, ...]]
        if isinstance(result, list) and len(result) > 0:
            scores = result[0] 
            
            # Find the Positive Score
            # You trained it, so check if 'LABEL_1' or 'High' is the positive one.
            # Assuming 'LABEL_1' based on standard training.
            for item in scores:
                if item['label'] in ['LABEL_1', 'POSITIVE', 'High']:
                    return float(item['score'])
        
        return 0.0

    except Exception as e:
        print(f"❌ HF API Error: {e}")
        return 0.0