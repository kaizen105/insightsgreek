import os
from huggingface_hub import InferenceClient

# --- CONFIGURATION ---
# 1. Get your token from: https://huggingface.co/settings/tokens
# 2. Set it here OR in your terminal: export HF_TOKEN="hf_..."
HF_TOKEN = os.environ.get('HF_TOKEN')

# TRY THIS MODEL FIRST (It is extremely reliable on the free tier)
# Change this line:
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
# Alternative if you want a bigger brain: "HuggingFaceH4/zephyr-7b-beta"

if not HF_TOKEN:
    print("❌ Error: HF_TOKEN environment variable is not set.")
    print("   Run: export HF_TOKEN='your_token_here' (Linux/Mac)")
    print("   Or:  set HF_TOKEN='your_token_here' (Windows)")
    exit(1)

print(f"🤖 Connecting to Hugging Face Inference API...")
print(f"   Model: {MODEL_ID}")

try:
    client = InferenceClient(model=MODEL_ID, token=HF_TOKEN)
    
    # --- TEST 1: CHATBOT LOGIC (Sales Coach) ---
    print("\n🧪 TEST 1: Sales Chatbot Logic...")
    
    chat_messages = [
        {"role": "system", "content": "You are an expert Sales Coach. Be concise and aggressive."},
        {"role": "user", "content": "Context: Customer says price is too high. Question: What do I say?"}
    ]
    
    response = client.chat_completion(
        messages=chat_messages, 
        max_tokens=150, 
        temperature=0.7
    )
    
    print("✅ Chat Response Received:")
    print("-" * 40)
    print(response.choices[0].message.content)
    print("-" * 40)


    # --- TEST 2: GRAMMAR CHECKER ---
    print("\n🧪 TEST 2: Grammar Correction...")
    
    grammar_messages = [
        {"role": "system", "content": "Fix grammar and spelling. Output ONLY the corrected text."},
        {"role": "user", "content": "me want to buy this product yesterday but price to high"}
    ]
    
    grammar_response = client.chat_completion(
        messages=grammar_messages, 
        max_tokens=100, 
        temperature=0.1
    )
    
    print("✅ Grammar Result:")
    print("-" * 40)
    print(grammar_response.choices[0].message.content)
    print("-" * 40)

    print("\n🎉 SUCCESS: The model is working perfectly! You can use this in your app.")

except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    print("\nTROUBLESHOOTING:")
    print("1. Check if your HF_TOKEN is correct.")
    print("2. If it says 'model not supported', try changing MODEL_ID to 'HuggingFaceH4/zephyr-7b-beta'")