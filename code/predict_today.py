"""
Zero Local Models - Pure Hugging Face API Inference
- No torch, no transformers, no RAM usage
- All models run on HF servers
- Fast, scalable, perfect for Render free tier
"""

import os
import json
from huggingface_hub import InferenceClient
from textblob import TextBlob

HF_TOKEN = os.environ.get('HF_TOKEN')

# Zero-shot classification API for lead quality
LEAD_QUALITY_API = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

def load_model():
    """
    Dummy function - returns True so Flask thinks model is loaded
    Actually uses cloud APIs, not local models
    """
    print("✅ Using Cloud APIs (Zero local models, zero RAM usage)")
    return (True, True)


def predict_lead_quality(mock_tuple_ignored, text):
    """
    Predict lead quality using Hugging Face API.
    No local RAM usage - runs on HF servers.
    
    Args:
        mock_tuple_ignored: Ignored (for compatibility)
        text: Lead description
    
    Returns:
        float: 0.0 to 1.0 score
    """
    if not text or not text.strip():
        return 0.5
    
    # Try API first
    if HF_TOKEN:
        try:
            client = InferenceClient(token=HF_TOKEN)
            response = client.post(
                json={
                    "inputs": text,
                    "parameters": {"candidate_labels": ["high value sales deal", "medium quality lead", "low priority inquiry"]}
                },
                model=LEAD_QUALITY_API
            )
            
            # Response format:
            # {'labels': ['high value sales deal', 'medium quality lead', 'low priority inquiry'], 
            #  'scores': [0.85, 0.10, 0.05]}
            data = json.loads(response.decode())
            
            top_label = data['labels'][0]
            score = data['scores'][0]
            
            print(f"🔍 Lead Quality API result: {top_label} ({score:.2f})")
            
            # Map to 0-1 scale
            if "high" in top_label.lower():
                return float(score)
            elif "medium" in top_label.lower():
                return float(0.5 + (score * 0.25))
            else:  # low priority
                return float(score * 0.45)
                
        except Exception as e:
            print(f"⚠️  Lead Quality API Error: {e}. Falling back to heuristics.")
    
    # Fallback: Keyword + sentiment heuristics
    text_lower = text.lower()
    keywords = ['budget', 'urgent', 'approved', 'contract', 'buy', 'sign', 'deal', 'purchase', 'decision', 'ready']
    
    base_score = 0.3
    for word in keywords:
        if word in text_lower:
            base_score += 0.15
    
    # Sentiment boost (excited people = better leads)
    try:
        analysis = TextBlob(text)
        if analysis.sentiment.polarity > 0.3:
            base_score += 0.1
    except:
        pass
    
    return min(base_score, 0.95)


def predict_probability(mock_tuple_ignored, text):
    """
    Predict sentiment using Hugging Face API.
    No local RAM usage - runs on HF servers.
    
    Args:
        mock_tuple_ignored: Ignored (for compatibility)
        text: Feedback text
    
    Returns:
        float: 0.0 to 1.0 (0=Negative, 1=Positive)
    """
    if not text or not text.strip():
        return 0.5
    
    # Try API for sentiment
    if HF_TOKEN:
        try:
            client = InferenceClient(token=HF_TOKEN)
            response = client.post(
                json={
                    "inputs": text,
                    "parameters": {"candidate_labels": ["positive sentiment", "negative sentiment"]}
                },
                model=LEAD_QUALITY_API  # BART can do sentiment too
            )
            
            data = json.loads(response.decode())
            top_label = data['labels'][0]
            score = data['scores'][0]
            
            print(f"🔍 Sentiment API result: {top_label} ({score:.2f})")
            
            # Return positive score if positive, else invert
            if "positive" in top_label.lower():
                return float(score)
            else:
                return float(1.0 - score)
                
        except Exception as e:
            print(f"⚠️  Sentiment API Error: {e}. Falling back to TextBlob.")
    
    # Fallback: TextBlob (fast, no ML required)
    try:
        blob = TextBlob(text)
        # Normalize -1 to 1 -> 0 to 1
        normalized = (blob.sentiment.polarity + 1) / 2
        print(f"🔍 TextBlob sentiment: {normalized:.2f}")
        return normalized
    except:
        return 0.5


def predict_lead_standalone(text):
    """
    Standalone prediction for lead quality (for testing)
    Uses API, no local model needed.
    
    Returns: dict with prediction details
    """
    try:
        probability = predict_lead_quality((True, True), text)
        
        return {
            'text': text,
            'probability': probability,
            'sentiment': 'High-Value' if probability > 0.7 else 'Medium' if probability > 0.4 else 'Low',
            'confidence': max(probability, 1 - probability)
        }
    except Exception as e:
        print(f"Error in predict_lead_standalone: {str(e)}")
        return {
            'text': text,
            'probability': 0.5,
            'sentiment': 'Neutral',
            'confidence': 0.5
        }


