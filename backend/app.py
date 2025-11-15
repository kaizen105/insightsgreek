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
# ========== NLTK RUNTIME PATH FIX ==========
import nltk
from textblob import TextBlob

# This is the directory our build script downloads to
NLTK_DATA_DIR = '/opt/render/nltk_data'

# (Find the old NLTK fix you added and replace it with this)

# Get the path to the 'backend' folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Get the path to the project root (one level up)
PROJECT_ROOT = os.path.dirname(BASE_DIR)
# Define the path to our new data folder
NLTK_DATA_DIR = os.path.join(PROJECT_ROOT, 'nltk_data')

# Check if the path exists
if os.path.exists(NLTK_DATA_DIR):
    # Force NLTK to add this path to its search list
    nltk.data.path.append(NLTK_DATA_DIR)
    print(f"✅ SUCCESS: NLTK data path manually set to: {NLTK_DATA_DIR}")
else:
    print(f"❌ FATAL: NLTK data directory NOT FOUND at: {NLTK_DATA_DIR}")
# ============================================

# --- ROBUST GEMINI (CHATBOT) SETUP ---
import google.generativeai as genai
GENAI_KEY = os.environ.get('GOOGLE_API_KEY')
chat_model = None

if GENAI_KEY:
    genai.configure(api_key=GENAI_KEY)
    # UPDATED: List of models your key actually supports
    POSSIBLE_MODELS = [
        'gemini-2.5-flash',
        'gemini-2.0-flash-exp',
        'gemini-1.5-flash',
        'gemini-pro'
    ]
    
    print("\n🤖 Connecting to AI...")
    for model_name in POSSIBLE_MODELS:
        try:
            # Try to initialize and run a quick test
            temp_model = genai.GenerativeModel(model_name)
            # A dummy generation to ensure it actually works
            temp_model.generate_content("test", request_options={'timeout': 10}) 
            chat_model = temp_model
            print(f"✅ SUCCESS: Connected to Gemini using model: '{model_name}'\n")
            break
        except Exception:
             continue

    if not chat_model:
        print("\n❌ ERROR: Still could not connect to any Gemini model.")
        print("Please check your API key and internet connection.\n")
else:
    print("ℹ️ NOTICE: GOOGLE_API_KEY not set. Chatbot disabled.\n")

# ========== CRITICAL: FIX IMPORTS FOR SIBLING FOLDERS ==========
# 1. Get the path to the 'backend' folder where this file lives
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# 2. Get the path to the project root (one level up)
PROJECT_ROOT = os.path.dirname(BASE_DIR)
# 3. Get the path to the 'code' folder
CODE_DIR = os.path.join(PROJECT_ROOT, 'code')
CURRENT_DIR = BASE_DIR  # ADD THIS LINE
# 4. FORCE Python to look in these folders (APPEND to avoid conflicts with stdlib 'code')
if PROJECT_ROOT not in sys.path: sys.path.append(PROJECT_ROOT)
if CODE_DIR not in sys.path: sys.path.append(CODE_DIR)

# 5. Tell ML script where the model file is specifically
os.environ['LEAD_MODEL_PATH'] = os.path.join(PROJECT_ROOT, 'models', 'lead_pipeline.joblib')
# ===============================================================

try:
    from predict_today import load_model, predict_probability
    ml_model = load_model()
    if ml_model:
        print(f"ML SUCCESS: Model loaded from {os.environ['LEAD_MODEL_PATH']}")
    else:
        print("ML WARNING: Imported modules, but model file failed to load.")
except ImportError as e:
    print(f"ML CRITICAL: Could not find 'predict_today.py' in {CODE_DIR}")
    print(f"Python is looking in: {sys.path}")
    ml_model, predict_probability = None, None
# ---------------------

app = Flask(__name__, template_folder=os.path.join(CURRENT_DIR, 'templates'), 
            static_folder=os.path.join(CURRENT_DIR, 'static'))

# UPDATED CONFIGURATION FOR PRODUCTION
# Use the environment variable if it exists, otherwise fallback to dev key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Use Postgres if available (for platforms like Render), otherwise fallback to local SQLite
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1) # Fix for SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///' + os.path.join(CURRENT_DIR, 'sales_feedback.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
CORS(app)
with app.app_context():
    db.create_all()
    print("🌱 Checking database status...")

    # 1. Seed Users
    if not User.query.first():
        print("👤 No users found. Seeding default users...")
        dev = User(username='dev', role='dev'); dev.set_password('dev123')
        mgr = User(username='manager', role='manager'); mgr.set_password('manager123')
        sls = User(username='sales', role='salesperson'); sls.set_password('sales123')
        db.session.add_all([dev, mgr, sls])
        db.session.commit()
        print("✅ Users seeded.")

    # 2. Seed Products
    if not Product.query.first():
        print("📦 No products found. Seeding samples...")
        db.session.add_all([
            Product(name='Enterprise AI Suite', description='Full AI integration platform', details='Unlimited API calls, dedicated support', catalogue_info='SKU: AI-ENT-001'),
            Product(name='Startup Starter Pack', description='Essential tools for small teams', details='Basic AI features, email support', catalogue_info='SKU: ST-BAS-101'),
            Product(name='Consulting Services', description='Expert implementation help', details='Hourly rate, onsite available', catalogue_info='SKU: SRV-CON-999')
        ])
        db.session.commit()
        print("✅ Products seeded.")

    # 3. Seed Dashboard Data (Feedback)
    if not Feedback.query.first():
        print("📊 No feedback found. Seeding dashboard data...")
        sales_user = User.query.filter_by(role='salesperson').first()
        
        if sales_user:
            # --- 1. SEED 20 SAMPLE LEADS ---
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
            for _ in range(2): # Loop 2 times
                for text, score, label in lead_samples: # 10 samples
                    days_ago = random.randint(0, 9)
                    fb = Feedback(
                        salesperson_id=sales_user.id, 
                        text=text, 
                        lead_score=score,    # <-- Use lead columns
                        lead_label=label,    # <-- Use lead columns
                        status='lead',       # <-- Set status
                        timestamp=datetime.utcnow() - timedelta(days=days_ago)
                    )
                    db.session.add(fb)

            # --- 2. SEED 20 SAMPLE FEEDBACK (with sentiment) ---
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
            for _ in range(2): # Loop 2 times
                for text, score, label in feedback_samples: # 10 samples
                    days_ago = random.randint(0, 9)
                    fb = Feedback(
                        salesperson_id=sales_user.id, 
                        text=text, 
                        sentiment_score=score, # <-- Use sentiment columns
                        sentiment_label=label, # <-- Use sentiment columns
                        status='feedback',     # <-- Set status
                        timestamp=datetime.utcnow() - timedelta(days=days_ago)
                    )
                    db.session.add(fb)

            db.session.commit()
            print("✅ Dashboard data (40 entries) seeded!")
        else:
            print("❌ ERROR: 'salesperson' user not found. Cannot seed data.")
# =======================================================
# --- LOAD ML MODEL AT STARTUP ---
ml_model = None
if load_model:
    ml_model = load_model()
    if ml_model:
        print("SUCCESS: Lead prediction model loaded.")
    else:
        print("WARNING: Lead prediction model failed to load.")
# --------------------------------
# JWT token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token: return jsonify({'error': 'Token is missing'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user: return jsonify({'error': 'Invalid token'}), 401
        except Exception: return jsonify({'error': 'Invalid token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Role-based access decorator
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if current_user.role not in roles: return jsonify({'error': 'Unauthorized access'}), 403
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator


# ========== ROUTES - Pages ==========

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


# ========== API ROUTES - Authentication ==========

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
    
    token = jwt.encode({
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({'token': token, 'user': user.to_dict()}), 200

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    if not all([username, password, role]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Security: Restrict public registration roles
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

# ========== API ROUTES - Feedback & ML ==========

@app.route('/api/submit-lead', methods=['POST'])
@token_required
@role_required('salesperson')
def submit_lead(current_user):
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'Lead text is required'}), 400
    
    # --- ML SCORING (FOR LEADS) ---
    lead_score = None
    lead_label = None
    if ml_model and predict_probability:
        try:
            lead_score = predict_probability(ml_model, text)
            if lead_score >= 0.7: lead_label = "High"
            elif lead_score >= 0.45: lead_label = "Medium"
            else: lead_label = "Low"
        except Exception as e:
            print(f"ML Prediction failed: {e}")
            lead_score = 0.0
            lead_label = "Error"
    # ------------------

    # Save to the specific LEAD columns
    new_entry = Feedback(
        salesperson_id=current_user.id,
        text=text,
        lead_score=lead_score,   # <-- Saves to lead column
        lead_label=lead_label,   # <-- Saves to lead column
        status='lead'            # <-- Set a status so we can filter
    )
    
    db.session.add(new_entry)
    db.session.add(ActivityLog(user_id=current_user.id, action='lead_submit', details=f'Lead {new_entry.id} submitted (Score: {lead_score})'))
    db.session.commit()
    
    return jsonify({
        'message': 'Lead submitted',
        'ml_result': {
            'score': lead_score,
            'label': lead_label
        }
    }), 201


@app.route('/api/analyze-feedback', methods=['POST'])
@token_required
@role_required('salesperson')
def analyze_feedback(current_user):
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'Feedback text is required'}), 400

    # --- NEW SENTIMENT MODEL LOGIC ---
    blob = TextBlob(text)
    sentiment_score = blob.sentiment.polarity  # Score from -1.0 to 1.0
    
    if sentiment_score > 0.2: sentiment_label = "Positive"
    elif sentiment_score < -0.1: sentiment_label = "Negative"
    else: sentiment_label = "Neutral"
    # -----------------------

    # Save to the specific SENTIMENT columns
    new_entry = Feedback(
        salesperson_id=current_user.id,
        text=text,
        sentiment_score=sentiment_score, # <-- Saves to sentiment column
        sentiment_label=sentiment_label, # <-- Saves to sentiment column
        status='feedback'                # <-- Set a status
    )
    
    db.session.add(new_entry)
    db.session.add(ActivityLog(user_id=current_user.id, action='feedback_submit', details=f'Feedback {new_entry.id} submitted (Sentiment: {sentiment_label})'))
    db.session.commit()
    
    # Return the new sentiment result
    return jsonify({
        'message': 'Feedback submitted',
        'sentiment_result': {
            'score': sentiment_score,
            'label': sentiment_label
        }
    }), 201

# (You can keep your /api/predict-lead and /api/check-grammar routes as they were)
# ========== API: CHATBOT ==========
@app.route('/api/chat', methods=['POST'])
@token_required
def chat(current_user):
    if not chat_model: return jsonify({'error': 'Chatbot not configured'}), 503
    data = request.get_json()
    msg, context = data.get('message'), data.get('context', '')
    if not msg: return jsonify({'error': 'No message'}), 400

    prompt = f"""You are a helpful sales assistant for a {current_user.role}.
    CURRENT TASK CONTEXT: "{context}"
    USER QUESTION: {msg}
    Be concise and action-oriented."""
    
    try:
        response = chat_model.generate_content(prompt)
        return jsonify({'reply': response.text})
    except Exception as e: return jsonify({'error': str(e)}), 500

# ========== API ROUTES - Products ==========

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
    product = Product(
        name=data.get('name'),
        description=data.get('description'),
        details=data.get('details', ''),
        catalogue_info=data.get('catalogue_info', '')
    )
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


# ========== API ROUTES - Feedback & ML ==========
@app.route('/api/predict-lead', methods=['POST'])
@token_required
def predict_lead_standalone(current_user):
    data = request.get_json()
    text = data.get('text')
    if not text: return jsonify({'error': 'No text provided'}), 400
    if not ml_model: return jsonify({'error': 'ML model not loaded'}), 503

    try:
        score = predict_probability(ml_model, text)
        label = "High" if score >= 0.7 else ("Medium" if score >= 0.45 else "Low")
        return jsonify({'score': score, 'label': label}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-grammar', methods=['POST'])
@token_required
@role_required('salesperson')
def check_grammar(current_user):
    data = request.get_json()
    text = data.get('text', '')
    
    corrected = text.strip()
    corrected = re.sub(r'\s+', ' ', corrected)
    corrected = corrected.capitalize()
    
    corrections = {
        ' i ': ' I ', "dont": "don't", "cant": "can't",
        "wont": "won't", "thats": "that's", "its": "it's"
    }
    for mistake, correction in corrections.items():
        corrected = corrected.replace(mistake, correction)
    
    return jsonify({'corrected_text': corrected}), 200


# ========== API ROUTES - Dashboard ==========

# ========== API ROUTES - Dashboard ==========

@app.route('/api/dashboard', methods=['GET'])
@token_required
@role_required('manager')
def get_dashboard(current_user):
    
    # --- General Stats ---
    total_feedbacks = Feedback.query.count()
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_feedbacks = Feedback.query.filter(Feedback.timestamp >= week_ago).count()
    active_sales = User.query.filter_by(role='salesperson').count()
    
    # --- LEAD STATS (For Lead Chart) ---
    high_leads = Feedback.query.filter(Feedback.lead_label == 'High').count()
    medium_leads = Feedback.query.filter(Feedback.lead_label == 'Medium').count()
    low_leads = Feedback.query.filter(Feedback.lead_label == 'Low').count()

    # --- SENTIMENT STATS (For Sentiment Chart) ---
    pos_count = Feedback.query.filter(Feedback.sentiment_label == 'Positive').count()
    neg_count = Feedback.query.filter(Feedback.sentiment_label == 'Negative').count()
    neu_count = Feedback.query.filter(Feedback.sentiment_label == 'Neutral').count()

    # --- Wordcloud (from high-quality LEADS) ---
    high_quality_texts = [f.text for f in Feedback.query.filter(Feedback.lead_label == 'High').all()]
    source_text = ' '.join(high_quality_texts) if len(high_quality_texts) > 5 else ' '.join([f.text for f in Feedback.query.filter(Feedback.lead_label != None).all()])
    words = re.findall(r'\w+', source_text.lower())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'was', 'are', 'were', 'of', 'with', 'it', 'this', 'that', 'we', 'i', 'they'}
    word_counts = Counter(w for w in words if w not in stop_words and len(w) > 2)
    wordcloud_data = [[word, count] for word, count in word_counts.most_common(50)]
    
    # --- Trends Chart (for ALL entries) ---
    trends_labels = []
    trends_data = []
    for i in range(6, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = Feedback.query.filter(Feedback.timestamp >= day_start, Feedback.timestamp < day_end).count()
        trends_labels.append(day.strftime('%m/%d'))
        trends_data.append(count)
    
    # --- Recent Entries (for ALL entries) ---
    recent = Feedback.query.order_by(Feedback.timestamp.desc()).limit(10).all()
    
    return jsonify({
        'stats': {
            'total': total_feedbacks,
            'week': week_feedbacks,
            'active_sales': active_sales,
            'leads': {'high': high_leads, 'medium': medium_leads, 'low': low_leads}
        },
        'sentiment': {'positive': pos_count, 'neutral': neu_count, 'negative': neg_count},
        'wordcloud_data': wordcloud_data,
        'trends': {'labels': trends_labels, 'data': trends_data},
        'recent': [f.to_dict() for f in recent],
    }), 200


@app.route('/api/download-report', methods=['GET'])
@token_required
@role_required('manager')
def download_report(current_user):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['ID', 'Salesperson', 'Feedback', 'Time', 'Status', 'Lead Score', 'Lead Label'])
    for f in Feedback.query.order_by(Feedback.timestamp.desc()).all():
        w.writerow([
            f.id, 
            f.salesperson.username, 
            f.text, 
            f.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 
            f.status, 
            f"{f.lead_score:.2f}" if f.lead_score is not None else "N/A", 
            f.lead_label or "N/A"
        ])
    out.seek(0)
    # CRITICAL FIX: 'utf-8-sig' adds the BOM for Excel compatibility
    return send_file(
        io.BytesIO(out.getvalue().encode('utf-8-sig')), 
        mimetype='text/csv', 
        as_attachment=True, 
        download_name=f'sales_report_{datetime.utcnow().strftime("%Y-%m-%d")}.csv'
    )

# ========== API ROUTES - Dev Management ==========

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)