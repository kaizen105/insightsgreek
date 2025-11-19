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
        print("⏳ Loading Sentiment Analysis Model (Twitter RoBERTa)...")
        # cardiffnlp/twitter-roberta-base-sentiment-latest:
        # - Trained on tweets (similar to sales feedback: short, informal, slang)
        # - Better at detecting neutral comments in business context
        # - Outputs: 'positive', 'neutral', 'negative'
        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            device=-1  # CPU
        )
        print("✅ Sentiment model loaded")
    
    if zero_shot_pipeline is None:
        print("⏳ Loading Lead Quality Model (DeBERTa v3)...")
        # MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli:
        # - SOTA (State of the Art) for zero-shot classification
        # - Smarter at understanding lead quality vs just "interested"
        # - Better relationship understanding than BART
        zero_shot_pipeline = pipeline(
            "zero-shot-classification",
            model="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
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
        
        # Twitter RoBERTa outputs lowercase labels: 'positive', 'neutral', 'negative'
        # Sometimes outputs Label_0, Label_1, Label_2
        label = result['label'].lower()
        score = result['score']
        
        # Handle different label formats
        if 'positive' in label or 'label_0' in label:
            return float(score)
        elif 'negative' in label or 'label_2' in label:
            return float(1.0 - score)
        else:  # neutral or label_1
            return 0.5
            
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
        float: 0.0 to 1.0 score
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
        
        # Debug: print result structure
        print(f"🔍 Zero-shot result: {result}")
        
        # result = {
        #     'sequence': text,
        #     'labels': ['high-value sales lead', 'medium-quality lead', 'low-priority lead'],
        #     'scores': [0.85, 0.10, 0.05]
        # }
        
        if not result.get('scores') or len(result['scores']) == 0:
            print("⚠️  No scores returned from zero-shot model")
            return 0.5
            
        top_label = result['labels'][0] if result.get('labels') else ""
        top_score = result['scores'][0] if result.get('scores') else 0.5
        
        print(f"📊 Top label: {top_label}, Score: {top_score}")
        
        # Map to 0-1 scale based on label
        if "high" in top_label.lower():
            final_score = float(top_score)
            print(f"✅ High-value lead detected: {final_score}")
            return final_score
        elif "medium" in top_label.lower():
            final_score = float(0.5 + (top_score * 0.25))
            print(f"📌 Medium lead detected: {final_score}")
            return final_score
        else:  # low-priority
            final_score = float(top_score * 0.45)
            print(f"❌ Low-priority lead detected: {final_score}")
            return final_score
            
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

