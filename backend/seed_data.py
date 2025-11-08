from app import app, db
from models import User, Feedback
from datetime import datetime, timedelta
import random

# Sample data that mirrors what your ML model was trained on
SAMPLES = [
    # (Text, Score, Label)
    ("Customer absolutely loved the demo. They have budget approved and want to start next week.", 0.95, "High"),
    ("Not interested at all. Said our pricing is ridiculous compared to competitors.", 0.10, "Low"),
    ("Meeting went okay. They liked Feature A but hated Feature B. Need to nurture.", 0.55, "Medium"),
    ("Very keen! Asked for a custom quote for 500 seats. Hot lead!", 0.98, "High"),
    ("They are stuck in an existing contract for another 6 months. Call back later.", 0.30, "Low"),
    ("Great conversation. Decision maker needs approval from CEO, but looks promising.", 0.75, "High"),
    ("Just looking around, no immediate need. Maybe next year.", 0.20, "Low"),
    ("Had technical issues during the demo, they got frustrated and left early.", 0.15, "Low"),
    ("Wow, they were impressed by the AI features. Wants a follow-up meeting with their CTO.", 0.92, "High"),
    ("Standard inquiry, sent standard pricing sheet. Waiting to hear back.", 0.50, "Medium"),
    # Add duplicates to bulk up data
    ("Customer absolutely loved the demo. They have budget approved and want to start next week.", 0.95, "High"),
    ("Very keen! Asked for a custom quote for 500 seats. Hot lead!", 0.98, "High"),
     ("Just looking around, no immediate need. Maybe next year.", 0.20, "Low"),
]

def seed_database():
    with app.app_context():
        print("🌱 Starting database seed...")
        
        # 1. Find a salesperson to assign this feedback to
        sales_user = User.query.filter_by(role='salesperson').first()
        if not sales_user:
            print("❌ Error: No salesperson found. Please register one first!")
            return

        # 2. Insert sample data spread over the last 10 days
        print(f"👤 Assigning feedback to salesperson: {sales_user.username}")
        count = 0
        for text, score, label in SAMPLES:
            # Randomize time to make charts look realistic
            days_ago = random.randint(0, 9)
            hours_ago = random.randint(0, 23)
            timestamp = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)
            
            fb = Feedback(
                salesperson_id=sales_user.id,
                text=text,
                lead_score=score,
                lead_label=label,
                timestamp=timestamp,
                status='reviewed' if days_ago > 3 else 'new'
            )
            db.session.add(fb)
            count += 1
            
        db.session.commit()
        print(f"✅ Success! Added {count} feedback entries to the database.")
        print("📊 Your dashboard charts will now have data to display.")

if __name__ == '__main__':
    seed_database()
