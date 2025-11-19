"""
Sentiment Analysis using Hugging Face Pretrained Models
- No torch, no custom training, no timeouts
- Fast inference with transformers only
"""

from transformers import pipeline

# Global model instances (lazy loaded)
sentiment_pipeline = None

def load_model():
    """
    Load pretrained DistilBERT for sentiment analysis
    Returns: (pipeline, None) - pipeline handles everything
    """
    global sentiment_pipeline
    
    if sentiment_pipeline is None:
        print("⏳ Loading pretrained DistilBERT from Hugging Face...")
        # distilbert-base-uncased-finetuned-sst-2-english is perfect:
        # - Fast (DistilBERT is 40% smaller than BERT)
        # - Accurate (finetuned on SST-2 sentiment task)
        # - Instantly available from Hugging Face hub
        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1  # CPU (device=-1), GPU if available (device=0)
        )
        print("✅ Model loaded successfully")
    
    return (sentiment_pipeline, None)


def predict_probability(model_tuple, text):
    """
    Predict sentiment for given text
    
    Args:
        model_tuple: (pipeline, None) - returned from load_model()
        text: string to analyze
    
    Returns:
        float: 0.0 to 1.0 (0=Negative, 1=Positive)
    """
    pipeline_obj, _ = model_tuple
    
    if pipeline_obj is None:
        print("⚠️  Model not loaded, returning neutral score")
        return 0.5
    
    try:
        # Clean text
        text = str(text).strip()
        if not text:
            return 0.5
        
        # Get prediction
        result = pipeline_obj(text[:512])[0]  # Limit to 512 tokens (BERT max)
        
        # result = {'label': 'POSITIVE' or 'NEGATIVE', 'score': 0.9999}
        label = result['label']
        score = result['score']
        
        # Convert to 0-1 scale: POSITIVE=1, NEGATIVE=0
        if label == 'POSITIVE':
            return float(score)
        else:
            return float(1.0 - score)
            
    except Exception as e:
        print(f"❌ Prediction error: {str(e)}")
        return 0.5


def predict_lead_standalone(text):
    """
    Standalone prediction (for testing)
    Returns: dict with prediction details
    """
    try:
        model_tuple = load_model()
        probability = predict_probability(model_tuple, text)
        
        return {
            'text': text,
            'probability': probability,
            'sentiment': 'Positive' if probability > 0.5 else 'Negative',
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
