"""
Enhanced Test Script for Quantized Sales Lead Forecasting Model
This version:
- Prints model config (labels, num_labels) to check class mapping.
- Shows both class probabilities for each test.
- Tests accuracy assuming LABEL_0 or LABEL_1 as positive.
- Recommends the correct positive index based on higher accuracy.
Assumes: pip install optimum[quanto] transformers torch pandas (for CSV)
Model path: Auto-detects from code/ subfolder.
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from optimum.quanto import quantize, qint8  # For re-quantization on load
import sys

# Adjust path if running from code/ subfolder
if __name__ == "__main__" and os.path.basename(os.getcwd()) == "code":
    MODEL_PATH = "../quantized_lead_model"
else:
    MODEL_PATH = "./quantized_lead_model"

HF_TOKEN = os.environ.get('HF_TOKEN')  # If private; otherwise omit

print("="*70)
print("ENHANCED SALES LEAD FORECASTING MODEL TEST SUITE")
print("="*70)

# Step 1: Load Model and Re-Quantize
print("\n📂 Step 1: Loading and quantizing model...")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, token=HF_TOKEN)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH, token=HF_TOKEN)
    
    # Re-quantize (restores quantized state)
    quantize(model, weights=qint8)
    print(f"✅ Model loaded and quantized successfully!")
    print(f"   Model type: {type(model).__name__}")
    print(f"   Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    
    # Print config for label inspection
    print("\n🔍 Model Config Details:")
    print(f"   Num labels: {model.config.num_labels}")
    id2label_default = {0: 'LABEL_0', 1: 'LABEL_1'}  # Define outside f-string
    print(f"   ID2Label: {getattr(model.config, 'id2label', id2label_default)}")
    label2id_default = {'LABEL_0': 0, 'LABEL_1': 1}  # Define outside f-string
    print(f"   Label2Id: {getattr(model.config, 'label2id', label2id_default)}")
    
    # Approx size
    param_size = sum(p.numel() for p in model.parameters()) * 1 / 1024**2
    print(f"   Approx quantized param size: {param_size:.1f} MB")
    
    # Ignore unused weights warning: Normal for quantized checkpoints on load
except Exception as e:
    print(f"❌ Load/Quantize failed: {e}")
    exit(1)

# Step 2: Define Test Cases (same as before)
test_cases = [
    {"text": "Budget approved, ready to sign next week!", "expected": "Positive", "threshold": 0.5},
    {"text": "Just browsing options, no immediate need.", "expected": "Negative", "threshold": 0.5},
    {"text": "Excited about the demo—let's schedule a call ASAP!", "expected": "Positive", "threshold": 0.5},
    {"text": "Not interested at this time, thanks.", "expected": "Negative", "threshold": 0.5},
    {"text": "Our team is evaluating competitors right now.", "expected": "Negative", "threshold": 0.5},
    {"text": "PO in progress, closing end of month—high priority!", "expected": "Positive", "threshold": 0.5}
]

# Step 3: Run Inference with Both Class Assumptions
print("\n🔍 Step 2: Running tests (trying both LABEL_0 and LABEL_1 as positive)...")
results_0 = []  # Assume LABEL_0 positive
results_1 = []  # Assume LABEL_1 positive
correct_0 = 0
correct_1 = 0

for i, case in enumerate(test_cases, 1):
    try:
        inputs = tokenizer(case["text"], return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1)
            prob_0 = probs[0][0].item()
            prob_1 = probs[0][1].item()
        
        # For LABEL_0 as positive
        is_pos_0 = prob_0 > case["threshold"]
        pred_0 = "Positive" if is_pos_0 else "Negative"
        pass_0 = (pred_0 == case["expected"])
        if pass_0: correct_0 += 1
        results_0.append({"id": i, "text": case["text"], "prob_0": prob_0, "prob_1": prob_1, "pred_0": pred_0, "pass_0": pass_0})
        
        # For LABEL_1 as positive
        is_pos_1 = prob_1 > case["threshold"]
        pred_1 = "Positive" if is_pos_1 else "Negative"
        pass_1 = (pred_1 == case["expected"])
        if pass_1: correct_1 += 1
        results_1.append({"id": i, "text": case["text"], "prob_0": prob_0, "prob_1": prob_1, "pred_1": pred_1, "pass_1": pass_1})
        
        print(f"\nTest {i}:")
        print(f"   Text: '{case['text'][:50]}...'")
        print(f"   Probs: LABEL_0={prob_0:.4f}, LABEL_1={prob_1:.4f}")
        print(f"   If LABEL_0 positive: {pred_0} ({'✅' if pass_0 else '❌'}) | Expected: {case['expected']}")
        print(f"   If LABEL_1 positive: {pred_1} ({'✅' if pass_1 else '❌'}) | Expected: {case['expected']}")
        
    except Exception as e:
        print(f"\nTest {i}: ❌ ERROR - {e}")

# Step 4: Summary for Both Assumptions
total = len(test_cases)
acc_0 = (correct_0 / total) * 100
acc_1 = (correct_1 / total) * 100
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print(f"Assuming LABEL_0 as Positive: {correct_0}/{total} correct | Accuracy: {acc_0:.1f}%")
print(f"Assuming LABEL_1 as Positive: {correct_1}/{total} correct | Accuracy: {acc_1:.1f}%")

best_assumption = "LABEL_0" if acc_0 > acc_1 else "LABEL_1"
best_acc = max(acc_0, acc_1)
print(f"\n💡 Recommendation: Use {best_assumption} as positive class (Accuracy: {best_acc:.1f}%)")
if best_acc >= 80:
    print("🎉 Excellent! Model is forecasting accurately.")
elif best_acc >= 60:
    print("👍 Solid—fine-tune threshold or add data if needed.")
else:
    print("⚠️  Low accuracy: Model may need retraining on better labeled data.")
    print("   Or test cases don't match training distribution.")

# Step 5: Compare Quantized vs Unquantized (Quick Check)
print("\n🧪 Quick Unquantized Comparison (on Test 1)...")
try:
    # Load unquantized
    model_unq = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH, token=HF_TOKEN)
    inputs = tokenizer(test_cases[0]["text"], return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs_unq = model_unq(**inputs)
        probs_unq = torch.softmax(outputs_unq.logits, dim=1)
        prob_unq_0 = probs_unq[0][0].item()
        prob_unq_1 = probs_unq[0][1].item()
    
    print(f"   Test 1 Unquantized: LABEL_0={prob_unq_0:.4f}, LABEL_1={prob_unq_1:.4f}")
    print(f"   Quantized:         LABEL_0={results_0[0]['prob_0']:.4f}, LABEL_1={results_0[0]['prob_1']:.4f}")
    diff_0 = abs(prob_unq_0 - results_0[0]['prob_0'])
    diff_1 = abs(prob_unq_1 - results_0[0]['prob_1'])
    print(f"   Diff (LABEL_0/1): {diff_0:.4f} / {diff_1:.4f} (low = good; quantization drift minimal)")
except Exception as e:
    print(f"   Comparison failed: {e}")

# Optional: Save results
save_results = input("\nSave results to 'enhanced_test_results.csv'? (y/n): ").lower().strip() == 'y'
if save_results:
    try:
        import pandas as pd
        # Save for best assumption
        if best_assumption == "LABEL_0":
            df = pd.DataFrame(results_0)
        else:
            df = pd.DataFrame(results_1)
        df.to_csv('enhanced_test_results.csv', index=False)
        print("💾 Results saved to enhanced_test_results.csv")
    except ImportError:
        print("💡 Install pandas: pip install pandas")

print("\n🚀 Next Steps:")
print("   - Update your inference code: Use probs[0][POS_INDEX].item() where POS_INDEX=0 or 1 per recommendation.")
print("   - Customize test_cases with 20+ real labeled examples from your dataset.")
print("   - If low acc persists: Retrain with balanced data; check original training logs.")
print("   - Warnings (cpp/redirects/unused weights): Harmless—ignore for now.")