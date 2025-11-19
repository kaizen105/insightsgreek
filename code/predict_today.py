"""
Sentiment Analysis & Lead Quality Prediction using Hugging Face Pretrained Models
- distilbert-base-uncased-finetuned-sst-2-english: General sentiment (customer feedback)
- facebook/bart-large-mnli: Zero-shot classification (lead quality detection)
- Fast inference, no torch, no timeouts
"""

from transformers import pipeline

# Global model instances (lazy loaded)
sentiment_pipeline = None
zero_shot_pipeline = None

def load_model():
    """
    Load pretrained models for sentiment and lead quality analysis
    Returns: (sentiment_pipeline, zero_shot_pipeline)
    """
    global sentiment_pipeline, zero_shot_pipeline
    
    if sentiment_pipeline is None:
        print("⏳ Loading Sentiment Analysis Model (DistilBERT)...")
        # distilbert-base-uncased-finetuned-sst-2-english:
        # - Fast (DistilBERT is 40% smaller than BERT)
        # - Accurate for general sentiment (customer feedback)
        # - Finetuned on SST-2 (movie reviews)
        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1  # CPU
        )
        print("✅ Sentiment model loaded")
    
    if zero_shot_pipeline is None:
        print("⏳ Loading Lead Quality Model (BART Zero-Shot)...")
        # facebook/bart-large-mnli:
        # - Zero-shot classification (no need to retrain)
        # - Excellent for lead quality detection
        # - Can classify: "high-value lead", "sales-ready", "nurture", "low-priority"
        zero_shot_pipeline = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1  # CPU
        )
        print("✅ Lead quality model loaded")
    
    return (sentiment_pipeline, zero_shot_pipeline)


def predict_probability(model_tuple, text):
    """
    Predict sentiment for given text (feedback analysis)
    
    Args:
        model_tuple: (sentiment_pipeline, zero_shot_pipeline)
        text: string to analyze
    
    Returns:
        float: 0.0 to 1.0 (0=Negative, 1=Positive)
    """
    sentiment_pipe, _ = model_tuple
    
    if sentiment_pipe is None:
        print("⚠️  Model not loaded, returning neutral score")
        return 0.5
    
    try:
        # Clean text
        text = str(text).strip()
        if not text:
            return 0.5
        
        # Get sentiment prediction
        result = sentiment_pipe(text[:512])[0]  # Limit to 512 tokens
        
        # result = {'label': 'POSITIVE' or 'NEGATIVE', 'score': 0.9999}
        label = result['label']
        score = result['score']
        
        # Convert to 0-1 scale: POSITIVE=1, NEGATIVE=0
        if label == 'POSITIVE':
            return float(score)
        else:
            return float(1.0 - score)
            
    except Exception as e:
        print(f"❌ Sentiment prediction error: {str(e)}")
        return 0.5


def predict_lead_quality(model_tuple, text):
    """
    Predict lead quality using zero-shot classification
    Perfect for sales lead scoring
    
    Args:
        model_tuple: (sentiment_pipeline, zero_shot_pipeline)
        text: lead description
    
    Returns:
        dict: {'score': 0-1, 'label': 'High'/'Medium'/'Low', 'confidence': 0-1}
    """
    _, zero_shot_pipe = model_tuple
    
    if zero_shot_pipe is None:
        print("⚠️  Lead quality model not loaded, returning neutral")
        return 0.5
    
    try:
        text = str(text).strip()
        if not text:
            return 0.5
        
        # Define candidate labels for lead quality
        candidate_labels = ["high-value sales lead", "medium-quality lead", "low-priority lead"]
        
        # Zero-shot classification
        result = zero_shot_pipe(text[:512], candidate_labels)
        
        # result = {
        #     'sequence': text,
        #     'labels': ['high-value sales lead', 'medium-quality lead', 'low-priority lead'],
        #     'scores': [0.85, 0.10, 0.05]
        # }
        
        top_label = result['labels'][0]
        top_score = result['scores'][0]
        
        # Map to 0-1 scale
        if "high" in top_label.lower():
            return float(top_score)  # 0.75-1.0
        elif "medium" in top_label.lower():
            return float(0.5 + (top_score * 0.25))  # 0.45-0.75
        else:
            return float(top_score * 0.45)  # 0.0-0.45
            
    except Exception as e:
        print(f"❌ Lead quality prediction error: {str(e)}")
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

