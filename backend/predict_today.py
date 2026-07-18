import os
import json
from gradio_client import Client
from textblob import TextBlob

# Configuration
HF_SPACE_URL = "Kaizen696/my_lead_model" 
# HF_TOKEN = os.environ.get('HF_TOKEN') # Not needed for public space in this version

# Global client instance (Initially None)
cloud_client = None

def load_model():
    """
    Initializes the Gradio Client for the Hugging Face Space.
    Call this EXPLICITLY from your background thread.
    """
    global cloud_client
    try:
        print(f" Connecting to Hugging Face Space: {HF_SPACE_URL}...")
        # Connect without token (Public Space)
        cloud_client = Client(HF_SPACE_URL)
        print(" Connected to Cloud Model successfully.")
        return (True, True) # Return dummy tuple to satisfy Flask's expectation
    except Exception as e:
        print(f" Warning: Could not connect to HF Space. Using local fallback. Error: {e}")
        return None

def predict_lead_quality(text):
    """
    Predicts lead quality (0.0 - 1.0) using your custom DistilBERT model.
    """
    if not text or not text.strip():
        return 0.5

    # 1. Try Cloud Model (Your DistilBERT)
    if cloud_client:
        try:
            # API call
            result = cloud_client.predict(
                text, 
                api_name="/predict" 
            )
            
            # Handle Gradio API response structure
            label = "Low"
            score = 0.5

            if isinstance(result, dict):
                label = result.get('label', 'Low')
                score = result.get('lead_score', result.get('score', 0.5))
            elif isinstance(result, (list, tuple)) and len(result) > 0:
                if isinstance(result[0], dict):
                    label = result[0].get('label', 'Low')
                    score = result[0].get('lead_score', result[0].get('score', 0.5))
            
            print(f" Cloud Prediction: {label} (Lead Score: {score:.4f})")
            
            return float(score)
                
        except Exception as e:
            print(f" Cloud Inference Failed: {e}")
            print(" Switching to Local Fallback...")

    # 2. Local Fallback (Heuristics)
    text_lower = text.lower()
    base_score = 0.3
    keywords = ['budget', 'urgent', 'approved', 'contract', 'buy', 'sign']
    for word in keywords:
        if word in text_lower: base_score += 0.15
            
    blob = TextBlob(text)
    if blob.sentiment.polarity > 0.3: base_score += 0.1
    return min(base_score, 0.95)

def predict_probability(text):
    """
    Predicts SENTIMENT (Positive/Negative) distinct from Lead Quality.
    Uses TextBlob for speed/robustness.
    """
    try:
        blob = TextBlob(text)
        # Normalize polarity (-1 to 1) -> (0 to 1)
        return (blob.sentiment.polarity + 1) / 2
    except:
        return 0.5

def predict_sentiment_label(text):
    """Returns string label for Lead Quality"""
    score = predict_lead_quality(text)
    if score >= 0.65: return "High Value"
    elif score >= 0.35: return "Medium Priority"
    else: return "Low Priority"

def predict_lead_standalone(text):
    """
    Wrapper that returns the FULL dictionary expected by your frontend.
    """
    try:
        lead_score = predict_lead_quality(text)
        
        # Determine Label based on the NEW thresholds (High > 0.65, Medium > 0.35)
        if lead_score >= 0.65:
            sentiment_label = "High"
        elif lead_score >= 0.35:
            sentiment_label = "Medium"
        else:
            sentiment_label = "Low"

        # Generate Explainability (XAI) string
        text_lower = text.lower()
        reasons = []
        if any(w in text_lower for w in ['budget', 'approved', 'ready', 'sign']):
            reasons.append("strong buying signals")
        if any(w in text_lower for w in ['frustrated', 'cancel', 'expensive', 'competitor']):
            reasons.append("churn indicators or friction")
        if any(w in text_lower for w in ['maybe', 'later', 'six months', 'looking around']):
            reasons.append("low-intent timelines")
        
        blob = TextBlob(text)
        if blob.sentiment.polarity > 0.5:
            reasons.append("highly positive sentiment")
        elif blob.sentiment.polarity < -0.3:
            reasons.append("negative sentiment")

        explanation = "Score influenced by " + ", ".join(reasons) if reasons else "Score based on baseline AI evaluation"

        return {
            'text': text,
            'probability': lead_score,
            'sentiment': sentiment_label,
            'confidence': max(lead_score, 1 - lead_score), # Mock confidence
            'explanation': explanation
        }
    except Exception as e:
        print(f"Error in predict_lead_standalone: {str(e)}")
        return {
            'text': text,
            'probability': 0.5,
            'sentiment': 'Neutral',
            'confidence': 0.5,
            'explanation': 'Fallback rule applied due to inference error'
        }

# --- Test Block ---
if __name__ == "__main__":
    print("--- Testing Manual Connection ---")
    # Manually trigger load because it's not auto-running anymore
    load_model()
    
    sample = "We decided to go with another provider for now."
    print(f"\nTesting: {sample}")
    print(predict_lead_standalone(sample))