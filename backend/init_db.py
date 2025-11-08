from app import app, db
from models import User, Product, Feedback  # Added Feedback to imports
from datetime import datetime, timedelta

def init_database():
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        # Create default users
        print("Creating default users...")
        dev = User(username='dev', role='dev')
        dev.set_password('dev123')
        db.session.add(dev)
        
        manager = User(username='manager', role='manager')
        manager.set_password('manager123')
        db.session.add(manager)
        
        sales = User(username='sales', role='salesperson')
        sales.set_password('sales123')
        db.session.add(sales)
        
        db.session.commit() # Commit users first so they have IDs

        # Create sample products
        print("Creating sample products...")
        products = [
            Product(name='Product A', description='High-quality product', details='Features: Durable, Eco-friendly', catalogue_info='SKU: PA-001'),
            Product(name='Product B', description='Premium professional solution', details='Features: Advanced, Warranty included', catalogue_info='SKU: PB-002'),
            Product(name='Product C', description='Budget-friendly starter kit', details='Features: Compact, Great value', catalogue_info='SKU: PC-003')
        ]
        for p in products: db.session.add(p)

        # --- NEW: CREATE SAMPLE FEEDBACK WITH ML SCORES ---
        print("Creating sample feedback with ML scores...")
        feedbacks = [
            Feedback(
                salesperson_id=sales.id,
                text="Client loved the demo and wants to sign contract next week. Very excited about standard features.",
                lead_score=0.95,
                lead_label="High",
                timestamp=datetime.utcnow() - timedelta(days=1)
            ),
             Feedback(
                salesperson_id=sales.id,
                text="Customer is interested but worried about the price. Wants to see if we can offer a discount.",
                lead_score=0.65,
                lead_label="Medium",
                timestamp=datetime.utcnow() - timedelta(days=2)
            ),
            Feedback(
                salesperson_id=sales.id,
                text="They are just browsing right now, not ready to buy. Might follow up in 6 months.",
                lead_score=0.15,
                lead_label="Low",
                timestamp=datetime.utcnow() - timedelta(days=3)
            ),
            Feedback(
                salesperson_id=sales.id,
                text="Urgent: Client is ready to move forward with the premium plan. Needs implementation timeline ASAP.",
                lead_score=0.98,
                lead_label="High",
                timestamp=datetime.utcnow() - timedelta(hours=5)
            )
        ]
        for f in feedbacks: db.session.add(f)
        # --------------------------------------------------
        
        db.session.commit()
        print("\n✓ Database initialized successfully with ML data!")

if __name__ == '__main__':
    init_database()