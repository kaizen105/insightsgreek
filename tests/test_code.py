from gradio_client import Client
import time

# Load your HuggingFace Space
client = Client("Kaizen696/my_lead_model")

# The Torture Test Suite
test_cases = [
    # Category 1: High Intent (The "Shut up and take my money" Leads)
    "Hi, I reviewed your proposal. Let’s move forward this week. Send me the contract.",
    "We have budget approved for Q4. Can we schedule a demo for the implementation team?",
    "Urgent: We need this deployed by Friday. What is the fastest onboarding path?",

    # Category 2: The "Soft No" (The hardest to detect)
    "We decided to go with another provider for now, but let's keep in touch.",
    "This looks interesting, but we don't have budget until next fiscal year.",
    "I'll have to run this by my boss. I'll get back to you if there's interest.",

    # Category 3: Mixed Signals (Sentiment vs. Intent)
    "I love the features, but the price is way too high for us right now.",
    "The demo was a disaster, but we still need a solution like this. Do you have other options?",
    "It's a great tool, but we are happy with our current vendor.",

    # Category 4: Garbage / Noise (Should be Neutral/Low)
    "Please remove my email from your list.",
    "Out of office until Monday.",
    "Hello!!",
    "Unsubscribe.",
]

print(f"{'INPUT TEXT':<80} | {'PREDICTION':<15}")
print("-" * 100)

for text in test_cases:
    try:
        # Add a small delay to avoid rate limiting on free tier
        time.sleep(0.5)
        
        result = client.predict(
            text=text,
            api_name="/predict"
        )
        
        # Clean up the output for display (assuming result returns a label/score)
        # Adjust 'result' indexing based on your exact API return structure
        print(f"{text[:75]:<80} | {str(result)}")
        
    except Exception as e:
        print(f"{text[:75]:<80} | ERROR: {e}")

print("-" * 100)
print("Torture Test Complete.")