"""
Ultra-Lightweight Sentiment & Lead Quality using Hugging Face
- MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33: ~100MB ultra-compact
  Does sentiment AND lead quality classification
- Perfect fit for 512MB Render free tier
"""

from transformers import pipeline

# Global model instance (lazy loaded)
zero_shot_pipeline = None

def load_model():
    """
    Load ultra-lightweight DeBERTa-v3-xsmall for ALL classification tasks
    Returns: (zero_shot_pipeline, None)
    """
    global zero_shot_pipeline
    
    if zero_shot_pipeline is None:
        print("⏳ Loading Classification Model (DeBERTa-v3-xsmall)...")
        # MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33:
        # - Ultra-lightweight (~100MB)
        # - Can handle sentiment, lead quality, any zero-shot task
        # - SOTA quality despite tiny size
        zero_shot_pipeline = pipeline(
            "zero-shot-classification",
            model="MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33",
            device=-1  # CPU
        )
        print("✅ Classification model loaded")
    
    return (zero_shot_pipeline, None)


def predict_probability(model_tuple, text):
    """
    Predict sentiment using zero-shot classification
    
    Args:
        model_tuple: (zero_shot_pipeline, None)
        text: string to analyze
    
    Returns:
        float: 0.0 to 1.0 (0=Negative, 1=Positive)
    """
    zero_shot_pipe, _ = model_tuple
    
    if zero_shot_pipe is None:
        print("⚠️  Model not loaded, returning neutral score")
        return 0.5
    
    try:
        text = str(text).strip()
        if not text:
            return 0.5
        
        # Sentiment classification
        candidate_labels = ["positive sentiment", "negative sentiment"]
        result = zero_shot_pipe(text[:512], candidate_labels)
        
        print(f"🔍 Sentiment result: {result}")
        
        if not result.get('scores'):
            return 0.5
            
        top_label = result['labels'][0]
        top_score = result['scores'][0]
        
        # If top label is positive, return score. If negative, return 1-score
        if "positive" in top_label.lower():
            return float(top_score)
        else:
            return float(1.0 - top_score)
            
    except Exception as e:
        print(f"❌ Sentiment prediction error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0.5


def predict_lead_quality(model_tuple, text):
    """
    Predict lead quality using zero-shot classification
    
    Args:
        model_tuple: (zero_shot_pipeline, None)
        text: lead description
    
    Returns:
        float: 0.0 to 1.0 score
    """
    zero_shot_pipe, _ = model_tuple
    
    if zero_shot_pipe is None:
        print("⚠️  Model not loaded, returning neutral")
        return 0.5
    
    try:
        text = str(text).strip()
        if not text:
            return 0.5
        
        # Lead quality classification
        candidate_labels = ["high-value sales lead", "medium-quality lead", "low-priority lead"]
        result = zero_shot_pipe(text[:512], candidate_labels)
        
        print(f"🔍 Lead quality result: {result}")
        
        if not result.get('scores'):
            return 0.5
            
        top_label = result['labels'][0]
        top_score = result['scores'][0]
        
        # Map to 0-1 scale
        if "high" in top_label.lower():
            return float(top_score)
        elif "medium" in top_label.lower():
            return float(0.5 + (top_score * 0.25))
        else:  # low-priority
            return float(top_score * 0.45)
            
    except Exception as e:
        print(f"❌ Lead quality prediction error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0.5


def predict_lead_standalone(text):
    """
    Standalone prediction for lead quality (for testing)
    Returns: dict with prediction details
    """
    try:
        model_tuple = load_model()
        probability = predict_lead_quality(model_tuple, text)
        
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

