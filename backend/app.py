from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from models import db, User, Feedback, Product, ActivityLog
from datetime import datetime, timedelta
import jwt
import os
from functools import wraps
import csv
import io
from collections import Counter
import re
import sys
import random
from textblob import TextBlob
import time
import logging
import traceback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- HUGGING FACE SETUP (Mistral 7B) ---
from huggingface_hub import InferenceClient

HF_TOKEN = os.environ.get('HF_TOKEN')
chat_client = None

# Using Mistral-7B-Instruct (Great for chat & logic, and FREE)
MODEL_REPO = "Qwen/Qwen2.5-7B-Instruct"

if HF_TOKEN:
    try:
        chat_client = InferenceClient(model=MODEL_REPO, token=HF_TOKEN)
        # Quick test
        chat_client.chat_completion(messages=[{"role": "user", "content": "hi"}], max_tokens=5)
        print(f"\n✅ SUCCESS: Connected to Hugging Face ({MODEL_REPO})")
    except Exception as e:
        print(f"\n❌ ERROR: Could not connect to Hugging Face: {e}")
        chat_client = None
else:
    print("\nℹ️ NOTICE: HF_TOKEN not set. Chatbot disabled.")
    
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

CODE_DIR = os.path.join(PROJECT_ROOT, 'code')
CURRENT_DIR = BASE_DIR

if PROJECT_ROOT not in sys.path: 
    sys.path.append(PROJECT_ROOT)
if CODE_DIR not in sys.path: 
    sys.path.append(CODE_DIR)

# --- Initialize Flask FIRST (before ML model) ---
app = Flask(__name__, template_folder=os.path.join(CURRENT_DIR, 'templates'), static_folder=os.path.join(CURRENT_DIR, 'static'))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///' + os.path.join(CURRENT_DIR, 'sales_feedback.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
CORS(app)

print("✅ Flask app initialized and ready to bind to port\n")

import threading

# --- Initialize global ML variables ---
sentiment_pipeline = None
zero_shot_pipeline = None
predict_probability = None
predict_lead_quality = None
ml_loading_complete = False

def load_sentiment_model_async():
    """Load pretrained models (Sentiment + Lead Quality) in background thread"""
    global sentiment_pipeline, zero_shot_pipeline, predict_probability, predict_lead_quality, ml_loading_complete
    
    print("\n⏳ Background: Loading pretrained models from Hugging Face...")
    try:
        from predict_today import load_model, predict_probability as predict_func, predict_lead_quality as lead_quality_func
        print("✅ Background: Module imported")
        
        ml_components = load_model()
        if ml_components:
            sentiment_pipeline, zero_shot_pipeline = ml_components
            predict_probability = predict_func
            predict_lead_quality = lead_quality_func
            print("✅ Background: Sentiment model loaded successfully")
            print("✅ Background: Lead quality model loaded successfully")
            logging.info("Models loaded in background: Sentiment (DistilBERT) + Lead Quality (BART)")
        else:
            print("⚠️  Background: Models returned None")
            
    except Exception as e:
        print(f"⚠️  Background: Model load failed: {str(e)}")
        logging.error(f"Model loading failed: {str(e)}")
    finally:
        ml_loading_complete = True
        print("✅ Background: Model loading complete\n")

# Start loading model in background immediately (non-blocking)
print("\n" + "="*60)
print("🚀 Starting sentiment model load in background thread...")
print("="*60)
bert_thread = threading.Thread(target=load_sentiment_model_async, daemon=True)
bert_thread.start()
print("✅ Background thread started - app will start immediately\n")

with app.app_context():
    db.create_all()
    print("\n🌱 Checking database status...")

    if not User.query.first():
        print("👤 No users found. Seeding default users...")
        dev = User(username='dev', role='dev')
        dev.set_password('dev123')
        mgr = User(username='manager', role='manager')
        mgr.set_password('manager123')
        sls = User(username='sales', role='salesperson')
        sls.set_password('sales123')
        db.session.add_all([dev, mgr, sls])
        db.session.commit()
        print("✅ Users seeded.")

    if not Product.query.first():
        print("📦 No products found. Seeding samples...")
        db.session.add_all([
            Product(name='Enterprise AI Suite', description='Full AI integration platform', details='Unlimited API calls, dedicated support', catalogue_info='SKU: AI-ENT-001'),
            Product(name='Startup Starter Pack', description='Essential tools for small teams', details='Basic AI features, email support', catalogue_info='SKU: ST-BAS-101'),
            Product(name='Consulting Services', description='Expert implementation help', details='Hourly rate, onsite available', catalogue_info='SKU: SRV-CON-999')
        ])
        db.session.commit()
        print("✅ Products seeded.")

    if not Feedback.query.first():
        print("📊 No feedback found. Seeding dashboard data...")
        sales_user = User.query.filter_by(role='salesperson').first()
        
        if sales_user:
            print("...Seeding 20 sample leads...")
            lead_samples = [
                ("Loved the demo, budget approved, wants to start next week.", 0.95, "High"),
                ("Very keen! Asked for a custom quote for 500 seats. Hot lead!", 0.98, "High"),
                ("Meeting went okay. They liked Feature A. Need to nurture.", 0.55, "Medium"),
                ("Just looking around, no immediate need. Maybe next year.", 0.20, "Low"),
                ("Stuck in an existing contract for 6 months. Call back later.", 0.30, "Low"),
                ("Great conversation. Decision maker needs approval from CEO.", 0.75, "High"),
                ("Standard inquiry, sent pricing sheet. Waiting to hear back.", 0.50, "Medium"),
                ("Had technical issues during the demo, they got frustrated.", 0.15, "Low"),
                ("Impressed by the AI features. Wants a follow-up with their CTO.", 0.92, "High"),
                ("Their team is too small for the Enterprise plan, pitched Startup pack.", 0.45, "Medium"),
            ]
            for _ in range(2):
                for text, score, label in lead_samples:
                    days_ago = random.randint(0, 9)
                    fb = Feedback(salesperson_id=sales_user.id, text=text, lead_score=score, lead_label=label, status='lead', timestamp=datetime.utcnow() - timedelta(days=days_ago))
                    db.session.add(fb)

            print("...Seeding 20 sample feedback entries...")
            feedback_samples = [
                ("I am extremely happy with the support team, solved my issue in 5 minutes!", 0.9, "Positive"),
                ("The new update is fantastic, everything runs so much faster.", 0.8, "Positive"),
                ("It's an okay product, but it's missing a few key features.", 0.1, "Neutral"),
                ("I am so frustrated. The app crashed and I lost all my work.", -0.8, "Negative"),
                ("The pricing is way too high for what you get.", -0.5, "Negative"),
                ("The documentation is unclear and hard to follow.", -0.4, "Negative"),
                ("I like the product, it does exactly what it says it will do.", 0.6, "Positive"),
                ("The user interface is a bit clunky but it works.", 0.2, "Neutral"),
                ("Your competitor offers the same thing for half the price.", -0.3, "Negative"),
                ("Just wanted to say thanks, this tool saved me hours of work.", 1.0, "Positive"),
            ]
            for _ in range(2):
                for text, score, label in feedback_samples:
                    days_ago = random.randint(0, 9)
                    fb = Feedback(salesperson_id=sales_user.id, text=text, sentiment_score=score, sentiment_label=label, status='feedback', timestamp=datetime.utcnow() - timedelta(days=days_ago))
                    db.session.add(fb)

            db.session.commit()
            print("✅ Dashboard data (40 entries) seeded!")
        else:
            print("❌ ERROR: 'salesperson' user not found. Cannot seed data.")

print("\n🚀 Flask application initialized successfully!\n")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 401
        except Exception:
            return jsonify({'error': 'Invalid token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if current_user.role not in roles:
                return jsonify({'error': 'Unauthorized access'}), 403
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/salesperson')
def salesperson_page():
    return render_template('salesperson.html')

@app.route('/manager')
def manager_page():
    return render_template('manager.html')

@app.route('/dev')
def dev_page():
    return render_template('dev.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    
    if not all([username, password, role]):
        return jsonify({'error': 'Missing credentials'}), 400
    
    user = User.query.filter_by(username=username, role=role).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    user.last_login = datetime.utcnow()
    try:
        db.session.add(ActivityLog(user_id=user.id, action='login', details=f'User logged in as {role}'))
        db.session.commit()
    except:
        db.session.rollback()
    
    token = jwt.encode({'user_id': user.id, 'role': user.role, 'exp': datetime.utcnow() + timedelta(hours=24)}, app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({'token': token, 'user': user.to_dict()}), 200

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    if not all([username, password, role]):
        return jsonify({'error': 'Missing required fields'}), 400

    if role not in ['salesperson', 'manager']:
        return jsonify({'error': 'Invalid role selected for public registration'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    new_user = User(username=username, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    try:
        db.session.add(ActivityLog(user_id=new_user.id, action='register', details=f'New user self-registered: {username} ({role})'))
        db.session.commit()
    except:
        db.session.rollback()

    return jsonify({'message': 'Registration successful! Please login.'}), 201

@app.route('/api/submit-lead', methods=['POST'])
@token_required
@role_required('salesperson')
def submit_lead(current_user):
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'Lead text is required'}), 400
    
    lead_score = None
    lead_label = None
    if sentiment_pipeline and zero_shot_pipeline and predict_lead_quality:
        try:
            print(f"\n🔍 DEBUG: Calling predict_lead_quality with text: {text[:100]}")
            lead_score = predict_lead_quality((sentiment_pipeline, zero_shot_pipeline), text)
            print(f"✅ DEBUG: Got lead_score = {lead_score}")
            
            # Thresholds based on zero-shot lead quality classification
            if lead_score >= 0.7:
                lead_label = "High"
            elif lead_score >= 0.4:
                lead_label = "Medium"
            else:
                lead_label = "Low"
            logging.info(f"Lead scored: {lead_score:.4f} -> {lead_label}")
        except Exception as e:
            print(f"❌ ML Prediction failed: {e}")
            import traceback
            traceback.print_exc()
            logging.error(f"Lead prediction error: {str(e)}")
            lead_score = 0.0
            lead_label = "Error"
    else:
        print(f"⚠️  DEBUG: Models not loaded yet. sentiment_pipeline={bool(sentiment_pipeline)}, zero_shot_pipeline={bool(zero_shot_pipeline)}, predict_lead_quality={bool(predict_lead_quality)}")

    new_entry = Feedback(salesperson_id=current_user.id, text=text, lead_score=lead_score, lead_label=lead_label, status='lead')
    
    db.session.add(new_entry)
    db.session.add(ActivityLog(user_id=current_user.id, action='lead_submit', details=f'Lead {new_entry.id} submitted (Score: {lead_score})'))
    db.session.commit()
    
    return jsonify({'message': 'Lead submitted', 'ml_result': {'score': lead_score, 'label': lead_label}}), 201

@app.route('/api/analyze-feedback', methods=['POST'])
@token_required
@role_required('salesperson')
def analyze_feedback(current_user):
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'Feedback text is required'}), 400

    # --- USING SENTIMENT PIPELINE (AI) ---
    if sentiment_pipeline:
        # Use the global sentiment_pipeline with predict_probability helper
        sentiment_score = predict_probability((sentiment_pipeline, zero_shot_pipeline), text)
        
        # Custom thresholds
        if sentiment_score > 0.6:
            sentiment_label = "Positive"
        elif sentiment_score < 0.4:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
    else:
        # Fallback if AI isn't ready yet
        blob = TextBlob(text)
        sentiment_score = (blob.sentiment.polarity + 1) / 2
        sentiment_label = "Neutral"

    new_entry = Feedback(salesperson_id=current_user.id, text=text, sentiment_score=sentiment_score, sentiment_label=sentiment_label, status='feedback')
    
    db.session.add(new_entry)
    db.session.add(ActivityLog(user_id=current_user.id, action='feedback_submit', details=f'Feedback {new_entry.id} submitted (Sentiment: {sentiment_label})'))
    db.session.commit()
    
    return jsonify({'message': 'Feedback submitted', 'sentiment_result': {'score': sentiment_score, 'label': sentiment_label}}), 201

@app.route('/api/chat', methods=['POST'])
@token_required
def chat(current_user):
    if not chat_client: 
        return jsonify({'error': 'Chatbot not configured (Check HF_TOKEN)'}), 503
    
    data = request.get_json()
    msg = data.get('message', '')
    context = data.get('context', '')
    msg_lower = msg.lower()
    
    if not msg: 
        return jsonify({'error': 'No message'}), 400

    system_role = f"You are an expert Sales Coach for a {current_user.role}. Be helpful, concise, and professional."

    if 'enhance' in msg_lower or 'rewrite' in msg_lower:
        system_role = """You are a CRM Data Analyst. 
        Rewrite these sales notes to be professional, clear, and structured with bullet points. 
        Return ONLY the rewritten notes."""
        
    elif 'suggest' in msg_lower or 'lead' in msg_lower:
        system_role = """You are a Lead Generation Engine.
        The user wants 3 NEW, HIGH-QUALITY mock leads.
        
        CRITICAL: Write the 'Lead Note' using strong buying signals (e.g., 'budget approved', 'ready to sign').
        
        Format each lead EXACTLY like this:
        - Lead 1: [Company Name] | [Role] | [High-Intent Note] | [Hook]
        - Lead 2: [Company Name] | [Role] | [High-Intent Note] | [Hook]
        - Lead 3: [Company Name] | [Role] | [High-Intent Note] | [Hook]"""
        
    else:
        system_role = f"""You are an expert "Closer" and sales coach.
        The user is asking a question about these notes: "{context}"
        Give 2-3 assertive, actionable steps to close the deal."""

    try:
        completion = chat_client.chat_completion(
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": f"Context: {context}\n\nRequest: {msg}"}
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        reply = completion.choices[0].message.content
        return jsonify({'reply': reply})
        
    except Exception as e:
        print(f"HF API Error: {e}")
        return jsonify({'error': f"AI Service Error: {str(e)}"}), 500
    
@app.route('/api/validate-leads', methods=['POST'])
@token_required
def validate_leads(current_user):
    if not sentiment_pipeline or not zero_shot_pipeline or not predict_lead_quality:
        return jsonify({'error': 'ML model unavailable'}), 503

    data = request.get_json()
    leads_text = data.get('leads_text', '')
    
    if not leads_text:
        return jsonify({'error': 'No leads provided'}), 400
    
    lead_matches = re.findall(r'[-•*]\s+(.+)', leads_text)
    validated = []
    
    for lead in lead_matches:
        parts = lead.split('|')
        key_phrase = parts[0].strip() if len(parts) > 0 else lead.strip()
        
        try:
            score = predict_lead_quality((sentiment_pipeline, zero_shot_pipeline), key_phrase)
            label = "High" if score >= 0.7 else "Medium" if score >= 0.4 else "Low"
            logging.info(f"Validated lead snippet scored: {score:.4f} -> {label}")

            validated.append({
                'lead_snippet': lead.strip()[:100] + '...',
                'score': score,
                'label': label,
                'tip': 'Prioritize!' if label == 'High' else 'Nurture carefully' if label == 'Medium' else 'De-prioritize'
            })
        except Exception as e:
            print(f"Error scoring lead segment: {e}")
            logging.error(f"Lead validation error: {str(e)}")
            continue
    
    high_quality = [v for v in validated if v['label'] == 'High']
    
    return jsonify({
        'validated_leads': validated,
        'high_quality_count': len(high_quality),
        'recommendation': f"Focus on {len(high_quality)} strong leads—rerun chat if needed for more."
    }), 200

@app.route('/api/check-grammar', methods=['POST'])
@token_required
@role_required('salesperson')
def check_grammar(current_user):
    data = request.get_json()
    text = data.get('text', '')
    
    if not text: return jsonify({'error': 'No text provided'}), 400
    
    if not chat_client: return jsonify({'error': 'AI not configured'}), 503

    try:
        completion = chat_client.chat_completion(
            messages=[
                {
                    "role": "system", 
                    "content": "Fix grammar and spelling. Output ONLY the corrected text. Do not add any introduction, quotes, or extra words."
                },
                {
                    "role": "user", 
                    "content": text
                }
            ],
            max_tokens=300,
            temperature=0.1
        )
        
        corrected_text = completion.choices[0].message.content.strip().strip('"')
        return jsonify({'corrected_text': corrected_text}), 200
        
    except Exception as e:
        print(f"Grammar check failed: {e}")
        return jsonify({'error': 'Failed to correct grammar'}), 500
    
@app.route('/api/predict-lead', methods=['POST'])
@token_required
def predict_lead_standalone(current_user):
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # --- CHECK CORRECT GLOBAL VARIABLES ---
    if not sentiment_pipeline or not zero_shot_pipeline:
        return jsonify({'error': 'ML models loading...'}), 503

    try:
        # --- USE predict_lead_quality (NOT predict_probability) ---
        score = predict_lead_quality((sentiment_pipeline, zero_shot_pipeline), text)
        
        if score >= 0.7:
            label = "High"
        elif score >= 0.4:
            label = "Medium"
        else:
            label = "Low"
        return jsonify({'score': score, 'label': label}), 200
    except Exception as e:
        print(f"❌ Prediction error: {str(e)}")
        return jsonify({'error': 'Prediction failed. Please try again.'}), 500

@app.route('/api/products', methods=['GET'])
@token_required
def get_products(current_user):
    products = Product.query.all()
    return jsonify({'products': [p.to_dict() for p in products]}), 200

@app.route('/api/products', methods=['POST'])
@token_required
@role_required('dev')
def add_product(current_user):
    data = request.get_json()
    product = Product(name=data.get('name'), description=data.get('description'), details=data.get('details', ''), catalogue_info=data.get('catalogue_info', ''))
    db.session.add(product)
    db.session.add(ActivityLog(user_id=current_user.id, action='product_add', details=f'Added product: {product.name}'))
    db.session.commit()
    return jsonify({'message': 'Product added', 'product': product.to_dict()}), 201

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@token_required
@role_required('dev')
def delete_product(current_user, product_id):
    product = Product.query.get_or_404(product_id)
    product_name = product.name
    db.session.delete(product)
    db.session.add(ActivityLog(user_id=current_user.id, action='product_delete', details=f'Deleted product: {product_name}'))
    db.session.commit()
    return jsonify({'message': 'Product deleted'}), 200

@app.route('/api/dashboard', methods=['GET'])
@token_required
@role_required('manager')
def get_dashboard(current_user):
    total_feedbacks = Feedback.query.count()
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_feedbacks = Feedback.query.filter(Feedback.timestamp >= week_ago).count()
    active_sales = User.query.filter_by(role='salesperson').count()
    
    high_leads = Feedback.query.filter(Feedback.lead_label == 'High').count()
    medium_leads = Feedback.query.filter(Feedback.lead_label == 'Medium').count()
    low_leads = Feedback.query.filter(Feedback.lead_label == 'Low').count()

    pos_count = Feedback.query.filter(Feedback.sentiment_label == 'Positive').count()
    neg_count = Feedback.query.filter(Feedback.sentiment_label == 'Negative').count()
    neu_count = Feedback.query.filter(Feedback.sentiment_label == 'Neutral').count()

    high_quality_texts = [f.text for f in Feedback.query.filter(Feedback.lead_label == 'High').all()]
    source_text = ' '.join(high_quality_texts) if len(high_quality_texts) > 5 else ' '.join([f.text for f in Feedback.query.filter(Feedback.lead_label != None).all()])
    words = re.findall(r'\w+', source_text.lower())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'was', 'are', 'were', 'of', 'with', 'it', 'this', 'that', 'we', 'i', 'they'}
    word_counts = Counter(w for w in words if w not in stop_words and len(w) > 2)
    wordcloud_data = [[word, count] for word, count in word_counts.most_common(50)]
    
    trends_labels = []
    trends_data = []
    for i in range(6, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = Feedback.query.filter(Feedback.timestamp >= day_start, Feedback.timestamp < day_end).count()
        trends_labels.append(day.strftime('%m/%d'))
        trends_data.append(count)
    
    recent = Feedback.query.order_by(Feedback.timestamp.desc()).limit(10).all()
    
    return jsonify({'stats': {'total': total_feedbacks, 'week': week_feedbacks, 'active_sales': active_sales, 'leads': {'high': high_leads, 'medium': medium_leads, 'low': low_leads}}, 'sentiment': {'positive': pos_count, 'neutral': neu_count, 'negative': neg_count}, 'wordcloud_data': wordcloud_data, 'trends': {'labels': trends_labels, 'data': trends_data}, 'recent': [f.to_dict() for f in recent]}), 200

@app.route('/api/download-report', methods=['GET'])
@token_required
@role_required('manager')
def download_report(current_user):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['ID', 'Salesperson', 'Feedback', 'Time', 'Status', 'Lead Score', 'Lead Label', 'Sentiment Score', 'Sentiment Label'])
    
    for f in Feedback.query.order_by(Feedback.timestamp.desc()).all():
        w.writerow([f.id, f.salesperson.username, f.text, f.timestamp.strftime('%Y-%m-%d %H:%M:%S'), f.status or 'N/A', f"{f.lead_score:.2f}" if f.lead_score is not None else "N/A", f.lead_label or "N/A", f"{f.sentiment_score:.2f}" if f.sentiment_score is not None else "N/A", f.sentiment_label or "N/A"])
    
    out.seek(0)
    return send_file(io.BytesIO(out.getvalue().encode('utf-8-sig')), mimetype='text/csv', as_attachment=True, download_name=f'sales_report_{datetime.utcnow().strftime("%Y-%m-%d")}.csv')

@app.route('/api/users', methods=['GET'])
@token_required
@role_required('dev')
def get_users(current_user):
    users = User.query.all()
    return jsonify({'users': [u.to_dict() for u in users]}), 200

@app.route('/api/users', methods=['POST'])
@token_required
@role_required('dev')
def add_user(current_user):
    data = request.get_json()
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(username=data.get('username'), role=data.get('role'))
    user.set_password(data.get('password'))
    db.session.add(user)
    db.session.commit()
    
    db.session.add(ActivityLog(user_id=current_user.id, action='user_add', details=f'Added user: {user.username} ({user.role})'))
    db.session.commit()
    return jsonify({'message': 'User added', 'user': user.to_dict()}), 201

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@token_required
@role_required('dev')
def delete_user(current_user, user_id):
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    db.session.add(ActivityLog(user_id=current_user.id, action='user_delete', details=f'Deleted user: {username}'))
    db.session.commit()
    return jsonify({'message': 'User deleted'}), 200

@app.route('/api/logs', methods=['GET'])
@token_required
@role_required('dev')
def get_logs(current_user):
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(100).all()
    return jsonify({'logs': [l.to_dict() for l in logs]}), 200

@app.route('/', methods=['GET'])
def index():
    """Root endpoint - responds immediately to confirm app is running"""
    return jsonify({
        'status': 'ok',
        'message': 'Sales Feedback System API is running',
        'version': '1.0',
        'ml_model': 'loaded' if ml_model else 'not_loaded',
        'chatbot': 'available' if chat_client else 'unavailable'
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'database': 'connected' if db else 'disconnected',
            'ml_model': 'loaded' if ml_model else 'not_loaded',
            'chatbot': 'available' if chat_client else 'unavailable'
        }
    }
    print(f"✅ Health check requested: {status}")
    return jsonify(status), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Access forbidden'}), 403

print("\n🚀 Flask application initialized successfully!\n")

if __name__ == '__main__':
    try:
        print("\n" + "="*60)
        print("🚀 Starting Flask Application")
        print("="*60)
        
        with app.app_context():
            print("📍 Creating database tables...")
            db.create_all()
            print("✅ Database ready")
        
        port = int(os.environ.get('PORT', 5000))
        debug_mode = os.environ.get('FLASK_ENV') != 'production'
        
        print(f"\n📊 Service Status:")
        print(f"   Environment: {'Production' if not debug_mode else 'Development'}")
        print(f"   Port: {port}")
        print(f"   Database: {'PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'}")
        print(f"   ML Model: {'✅ Loaded (BERT)' if ml_model else '❌ Not Loaded (graceful degradation)'}")
        print(f"   Chatbot: {'✅ Available' if chat_client else '❌ Unavailable (graceful degradation)'}")
        print("="*60 + "\n")
        
        print("✅ READY TO ACCEPT CONNECTIONS")
        print(f"📡 Listening on 0.0.0.0:{port}\n")
        
        app.run(host='0.0.0.0', port=port, debug=debug_mode)
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ FATAL ERROR - Application startup failed")
        print("="*60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("\nFull Traceback:")
        traceback.print_exc()
        print("="*60 + "\n")
        logging.error(f"Application startup failed: {str(e)}")
        logging.error(traceback.format_exc())
        sys.exit(1)