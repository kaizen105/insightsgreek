import os
import torch
import torch.nn.functional as F
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

# 1. Define path to your local model folder
# This assumes your folder structure is: root/models/my_lead_model
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "my_lead_model")

_tokenizer = None
_model = None

def load_model():
    """
    Loads the Fine-Tuned BERT model and Tokenizer from the local folder.
    """
    global _tokenizer, _model
    
    # If already loaded, return it (Singleton pattern)
    if _model is not None:
        return _model

    print(f"🤖 Loading Custom BERT Model from: {MODEL_PATH}...")
    
    if not os.path.exists(MODEL_PATH):
        print(f"❌ ERROR: Model folder not found at {MODEL_PATH}")
        print("   Did you unzip 'my_lead_model.zip' correctly?")
        return None

    try:
        # Load Tokenizer and Model
        _tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
        _model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
        _model.eval() # Set to evaluation mode (faster, no training)
        print("✅ Custom Deep Learning Model Loaded Successfully!")
        return _model
    except Exception as e:
        print(f"❌ CRITICAL: Failed to load DL model: {e}")
        return None

def predict_probability(model, text):
    """
    Runs the text through the BERT model and returns a score (0.0 to 1.0).
    """
    # Safety check: ensure model and tokenizer are loaded
    if model is None or _tokenizer is None:
        if not load_model():
            return 0.0

    try:
        # 1. Tokenize input
        inputs = _tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            padding=True, 
            max_length=512
        )

        # 2. Run Inference (No Gradients = Faster/Less RAM)
        with torch.no_grad():
            outputs = model(**inputs)

        # 3. Get Probabilities using Softmax
        # output.logits is raw numbers. Softmax turns them into %
        probs = F.softmax(outputs.logits, dim=-1)
        
        # 4. Get the score for the "Positive/High" class (Index 1)
        # Assuming your training was: 0=Low, 1=High
        positive_score = probs[0][1].item()
        
        return float(positive_score)

    except Exception as e:
        print(f"❌ Prediction Error: {e}")
        return 0.0