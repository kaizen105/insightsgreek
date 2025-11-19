import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from optimum.quanto import quantize, qint8  # For quantization on load
import time

# Configuration
MODEL_PATH = "./quantized_lead_model"  # Local path to your quantized model
HF_TOKEN = os.environ.get('HF_TOKEN')  # Optional: If model/tokenizer needs it

def load_model():
    """
    Loads the local quantized model and tokenizer.
    Validates setup and returns model/tokenizer pair.
    """
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: Model path '{MODEL_PATH}' not found. Run quantization script first.")
        return None
    
    print(f"✅ Loading local model from: {MODEL_PATH}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, token=HF_TOKEN)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH, token=HF_TOKEN)
        
        # Re-quantize to restore int8 weights (fast, ~1s)
        quantize(model, weights=qint8)
        
        print("✅ Model and tokenizer loaded + quantized successfully!")
        print(f"   Model type: {type(model).__name__}")
        print(f"   Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
        return model, tokenizer
    except Exception as e:
        print(f"❌ Load failed: {e}")
        print("💡 Tip: Ensure pip install transformers optimum[quanto] torch")
        return None

def predict_probability(model_tokenizer, text, max_retries=2):
    """
    Runs local inference on the loaded model.
    Returns probability score for positive class (LABEL_1, per test results).
    """
    model, tokenizer = model_tokenizer
    if model is None:
        print("❌ No model loaded")
        return 0.0
    
    if not text or len(text.strip()) == 0:
        print("⚠️  Empty text provided")
        return 0.0
    
    for attempt in range(max_retries):
        try:
            # Tokenize input
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            # Inference
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=1)
                score = probs[0][1].item()  # LABEL_1 as positive (66.7% acc from tests)
            
            print(f"✅ Score: {score:.4f}")
            return score
            
        except torch.cuda.OutOfMemoryError:
            print("⏱️  OOM error—falling back to CPU")
            model.to('cpu')
            time.sleep(1)
            continue
        except Exception as e:
            print(f"❌ Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return 0.0
    
    return 0.0

# Test function
def test_prediction():
    print("\n" + "="*60)
    print("Testing Local Quantized Model Inference")
    print("="*60)
    
    model_tokenizer = load_model()
    if not model_tokenizer:
        print("❌ Setup failed")
        return
    
    test_texts = [
        "Budget approved, ready to sign next week!",
        "Just browsing, not interested right now.",
        "CEO loves the demo, wants to schedule implementation call."
    ]
    
    for text in test_texts:
        print(f"\n{'='*60}")
        print(f"Text: '{text}'")
        print("-"*60)
        score = predict_probability(model_tokenizer, text)
        label = "High" if score >= 0.75 else "Medium" if score >= 0.45 else "Low"
        print(f"Final: {score:.4f} | {label}")

if __name__ == "__main__":
    test_prediction()