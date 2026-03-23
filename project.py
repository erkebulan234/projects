
from db.transactions import db_fetch_all_transactions
from db.users import create_user_with_defaults, verify_user_credentials, get_current_user_id
import hashlib

def hash_password(password):
    
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, email, password):
    
    password_hash = hash_password(password)
    user_id, error = create_user_with_defaults(username, email, password_hash)
    
    if error:
        return None, error
    return {"user_id": user_id, "username": username}, None

def verify_user(username, password):
    
    password_hash = hash_password(password)
    user_id, error = verify_user_credentials(username, password_hash)
    
    if error:
        return None, error
    return {"user_id": user_id, "username": username}, None

def db_fetch_user_transactions(username):
    
    return db_fetch_all_transactions(username)