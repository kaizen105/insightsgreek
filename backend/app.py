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
import io 

# --- IMPORT DATABASE MODELS ---
try:
    from models import db, User, Feedback, Product, ActivityLog
    print("✅ SUCCESS: Found models.py")
except ImportError as e:
    print(f"❌ FATAL: Could not import models.py: {e}")
    raise e

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

# ========== CRITICAL: DB INIT & SAFE SEED ==========
with app.app_context():
    db.create_all()
    # Check if users exist. If not, SEED them safely.
    if not User.query.first():
        print("🌱 Database empty. Seeding default users...")
        dev = User(username='dev', role='dev'); dev.set_password('dev123')
        mgr = User(username='manager', role='manager'); mgr.set_password('manager123')
        sls = User(username='sales', role='salesperson'); sls.set_password('sales123')
        db.session.add_all([dev, mgr, sls])
        db.session.commit()
        print("✅ SUCCESS: Default users created (dev/manager/sales)")
# ========================

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

@app.route('/api/feedback', methods=['POST'])
@token_required
@role_required('salesperson')
def submit_feedback(current_user):
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({'error': 'Feedback text is required'}), 400
    
    # --- ML SCORING ---
    lead_score = None
    lead_label = None
    if ml_model and predict_probability:
        try:
            lead_score = predict_probability(ml_model, text)
            if lead_score >= 0.7:
                lead_label = "High"
            elif lead_score >= 0.45:
                lead_label = "Medium"
            else:
                lead_label = "Low"
        except Exception as e:
            print(f"ML Prediction failed: {e}")
            lead_score = 0.0
            lead_label = "Error"
    # ------------------

    feedback = Feedback(
        salesperson_id=current_user.id,
        text=text,
        lead_score=lead_score,
        lead_label=lead_label
    )
    
    db.session.add(feedback)
    db.session.add(ActivityLog(user_id=current_user.id, action='feedback_submit', details=f'Feedback {feedback.id} submitted (Score: {lead_score})'))
    db.session.commit()
    
    return jsonify({
        'message': 'Feedback submitted',
        'feedback': feedback.to_dict(),
        'ml_result': {
            'score': lead_score,
            'label': lead_label
        }
    }), 201

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

@app.route('/api/dashboard', methods=['GET'])
@token_required
@role_required('manager')
def get_dashboard(current_user):
    feedbacks = Feedback.query.all()
    total_feedbacks = len(feedbacks)
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_feedbacks = Feedback.query.filter(Feedback.timestamp >= week_ago).count()
    active_sales = User.query.filter_by(role='salesperson').count()
    
    # --- ML STATS ---
    high_leads = Feedback.query.filter(Feedback.lead_label == 'High').count()
    medium_leads = Feedback.query.filter(Feedback.lead_label == 'Medium').count()
    low_leads = Feedback.query.filter(Feedback.lead_label == 'Low').count()

    # Wordcloud from High quality leads only
    high_quality_texts = [f.text for f in feedbacks if f.lead_label == 'High']
    source_text = ' '.join(high_quality_texts) if len(high_quality_texts) > 5 else ' '.join([f.text for f in feedbacks])
    words = re.findall(r'\w+', source_text.lower())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'was', 'are', 'were', 'of', 'with', 'it', 'this', 'that', 'we', 'i', 'they'}
    word_counts = Counter(w for w in words if w not in stop_words and len(w) > 2)
    wordcloud_data = [[word, count] for word, count in word_counts.most_common(50)]
    
    # Trends data
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
    
    # Simple sentiment fallback
    positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'love', 'best', 'happy', 'satisfied'}
    negative_words = {'bad', 'poor', 'terrible', 'worst', 'hate', 'disappointed', 'awful', 'useless'}
    pos_count, neg_count, neu_count = 0, 0, 0
    for f in feedbacks:
        words_in_f = set(re.findall(r'\w+', f.text.lower()))
        if len(words_in_f & positive_words) > len(words_in_f & negative_words): pos_count += 1
        elif len(words_in_f & negative_words) > len(words_in_f & positive_words): neg_count += 1
        else: neu_count += 1

    return jsonify({
        'stats': {
            'total': total_feedbacks,
            'week': week_feedbacks,
            'active_sales': active_sales,
            'leads': {'high': high_leads, 'medium': medium_leads, 'low': low_leads}
        },
        'wordcloud_data': wordcloud_data,
        'trends': {'labels': trends_labels, 'data': trends_data},
        'recent': [f.to_dict() for f in recent],
        'sentiment': {'positive': pos_count, 'neutral': neu_count, 'negative': neg_count}
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