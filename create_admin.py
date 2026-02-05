import pymongo
import hashlib
import os
import logging
from dotenv import load_dotenv

# Load environment
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "cfdi_db")
SECRET_KEY = os.getenv("SECRET_KEY", "default-salt-if-missing")

def hash_password(password):
    """Hash a password using SHA-256 with a salt."""
    salted_pass = password + SECRET_KEY
    return hashlib.sha256(salted_pass.encode()).hexdigest()

def create_admin():
    if not MONGO_URI:
        print("Error: MONGO_URI not found in environment.")
        return
    
    # Hide password in logs but check if it's correct
    logging.info(f"Connecting to MongoDB...")

    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    users_col = db["users"]

    # Define the first Company and Admin
    company_id = "TENANT_001"
    username = "admin"
    password = "admin123" # Admin password
    role = "admin"
    active_modules = ["kpis", "categorias", "tendencias", "riesgos"]

    password_hash = hash_password(password)

    user_doc = {
        "company_id": company_id,
        "username": username,
        "password_hash": password_hash,
        "role": role,
        "active_modules": active_modules
    }

    # Use update_one with upsert to avoid duplicates
    result = users_col.update_one(
        {"username": username, "company_id": company_id},
        {"$set": user_doc},
        upsert=True
    )

    if result.upserted_id:
        print(f"✅ User '{username}' created successfully for Company '{company_id}'.")
    else:
        print(f"ℹ️ User '{username}' already exists for Company '{company_id}'. Updated profile.")

    # Create a secondary test user with limited modules
    limited_user = "user01"
    limited_pass = "user123"
    limited_doc = {
        "company_id": company_id,
        "username": limited_user,
        "password_hash": hash_password(limited_pass),
        "role": "user",
        "active_modules": ["kpis", "riesgos"] # KPIs and Risks only
    }
    
    users_col.update_one(
        {"username": limited_user, "company_id": company_id},
        {"$set": limited_doc},
        upsert=True
    )
    print(f"✅ Limited user '{limited_user}' created for testing.")

if __name__ == "__main__":
    print("🚀 Initializing Multi-tenant Bootstrap...")
    create_admin()
