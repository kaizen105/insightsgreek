"""
Script to download, quantize, and prepare your model for Render deployment
This will reduce model size from 268MB to ~70MB using weight-only int8 quantization
(Requires: pip install optimum[quanto])
"""
import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from optimum.quanto import quantize, qint8  # HF's quantization toolkit

# Configuration
SOURCE_MODEL = "kaizen696/my_lead_model"
OUTPUT_DIR = "./quantized_lead_model"
HF_TOKEN = os.environ.get('HF_TOKEN')

print("="*70)
print("MODEL QUANTIZATION FOR RENDER DEPLOYMENT")
print("="*70)

# Step 1: Download original model
print("\n📥 Step 1: Downloading original model...")
try:
    tokenizer = AutoTokenizer.from_pretrained(SOURCE_MODEL, token=HF_TOKEN)
    model = AutoModelForSequenceClassification.from_pretrained(SOURCE_MODEL, token=HF_TOKEN)
    print(f"✅ Model downloaded")
    print(f"   Original size: ~268 MB")
    print(f"   Model type: {type(model).__name__}")
except Exception as e:
    print(f"❌ Failed: {e}")
    exit(1)

# Step 2: Quantize the model (weight-only int8, like dynamic for Linears)
print("\n🔧 Step 2: Quantizing model (this may take 1-2 minutes)...")
try:
    quantize(model, weights=qint8)  # Applies inplace, targets Linear/Embedding layers
    print("✅ Model quantized")
    print("   Expected size: ~70 MB (75% reduction)")
except Exception as e:
    print(f"❌ Quantization failed: {e}")
    exit(1)

# Step 3: Save quantized model locally (HF handles quantized save seamlessly)
print(f"\n💾 Step 3: Saving to {OUTPUT_DIR}...")
try:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
   
    # Save model and tokenizer (quanto enables proper serialization)
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
   
    print("✅ Saved locally")
    print(f"   Location: {os.path.abspath(OUTPUT_DIR)}")
except Exception as e:
    print(f"❌ Save failed: {e}")
    exit(1)

# Step 4: Test quantized model
print("\n🧪 Step 4: Testing quantized model...")
test_text = "Budget approved, ready to sign next week!"
try:
    inputs = tokenizer(test_text, return_tensors="pt", truncation=True, max_length=512)
   
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=1)
   
    score = probs[0][0].item()  # LABEL_0 is your positive class
    print(f"✅ Test prediction: {score:.4f}")
    print(f"   Text: '{test_text}'")
   
    if score < 0.1:
        print("⚠️  WARNING: Score seems too low. Model might have issues.")
    else:
        print("✅ Model works correctly!")
         
except Exception as e:
    print(f"❌ Test failed: {e}")
    exit(1)

# Deployment Note
print("\n🚀 For Render deployment: Load with...")
print("from transformers import AutoTokenizer, AutoModelForSequenceClassification")
print("from optimum.quanto import load_quantized_model")
print("model = load_quantized_model('path/to/quantized_lead_model')  # Auto-dequantizes if needed")
print("tokenizer = AutoTokenizer.from_pretrained('path/to/quantized_lead_model')")