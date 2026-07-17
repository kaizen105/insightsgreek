import pytest
import sys
import os
import jwt
from datetime import datetime, timedelta, timezone

# Add the parent directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User

@pytest.fixture
def client():
    # Configure app for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Clear any existing users created by app.py on import
            User.query.delete()
            
            # Seed test users
            sales = User(username='test_sales', role='salesperson')
            sales.set_password('pass123')
            
            mgr = User(username='test_manager', role='manager')
            mgr.set_password('pass123')
            
            dev = User(username='test_dev', role='dev')
            dev.set_password('pass123')
            
            db.session.add_all([sales, mgr, dev])
            db.session.commit()
            
            yield client
            
            db.session.remove()
            db.drop_all()

def generate_test_token(user_id, role):
    return jwt.encode({
        'user_id': user_id,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm="HS256")


def test_missing_token_rejected(client):
    """Test that requests without a token are rejected with 401"""
    response = client.get('/api/users')
    assert response.status_code == 401
    assert b"Token is missing" in response.data

def test_invalid_token_rejected(client):
    """Test that requests with an invalid/forged token are rejected with 401"""
    response = client.get('/api/users', headers={
        'Authorization': 'Bearer a.b.c'
    })
    assert response.status_code == 401
    assert b"Invalid token" in response.data

def test_salesperson_cannot_access_manager_routes(client):
    """Test that a Salesperson token cannot access Manager-only analytics"""
    sales_token = generate_test_token(1, 'salesperson')
    
    response = client.get('/api/analytics', headers={
        'Authorization': f'Bearer {sales_token}'
    })
    
    # 403 Forbidden is expected for RBAC rejection
    assert response.status_code == 403
    assert b"Unauthorized access" in response.data

def test_salesperson_cannot_access_dev_routes(client):
    """Test that a Salesperson token cannot access Dev-only product deletion"""
    sales_token = generate_test_token(1, 'salesperson')
    
    response = client.delete('/api/products/1', headers={
        'Authorization': f'Bearer {sales_token}'
    })
    
    assert response.status_code == 403
    assert b"Unauthorized access" in response.data

def test_manager_can_access_manager_routes(client):
    """Test that a Manager token CAN access Manager-only analytics"""
    mgr_token = generate_test_token(2, 'manager')
    
    response = client.get('/api/analytics', headers={
        'Authorization': f'Bearer {mgr_token}'
    })
    
    # 200 OK because the route succeeded
    assert response.status_code == 200
