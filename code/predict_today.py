import os
from huggingface_hub import InferenceClient

# 1. Setup Client
HF_TOKEN = os.environ.get('HF_TOKEN')
# Using a Zero-Shot Classification model for scoring
# This model is great at saying if text belongs to a label
MODEL_REPO = "facebook/bart-large-mnli" 

def load_model():
    # No local model to load, just check if Token exists
    if not HF_TOKEN:
        print("❌ Error: HF_TOKEN not found.")
        return None
    return True # Signal that we are ready

def predict_probability(model, text):
    """
    Uses Hugging Face API to classify text as 'High Value Lead'.
    Returns probability 0.0 - 1.0
    """
    if not HF_TOKEN: return 0.0

    try:
        client = InferenceClient(token=HF_TOKEN)
        
        # We ask the model: Is this text related to "Buying intent"?
        # It returns scores for labels we provide.
        result = client.zero_shot_classification(
            text,
            candidate_labels=["buying intent", "not interested"],
            model=MODEL_REPO
        )
        
        # result looks like: 
        # {'labels': ['buying intent', 'not interested'], 'scores': [0.95, 0.05]}
        
        # Find score for "buying intent"
        scores = result['scores']
        labels = result['labels']
        
        # Get score for the positive label
        for i, label in enumerate(labels):
            if label == "buying intent":
                return float(scores[i])
                
        return 0.0

    except Exception as e:
        print(f"❌ API Prediction Error: {e}")
        # Fallback to TextBlob if API fails (keeps app alive)
        from textblob import TextBlob
        return (TextBlob(text).sentiment.polarity + 1) / 2