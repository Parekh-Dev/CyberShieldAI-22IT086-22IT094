import pymongo
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import APIRouter, HTTPException, Depends, Form
from pydantic import BaseModel, EmailStr, validator
from pymongo import MongoClient
import bcrypt
from datetime import datetime
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Optional
import logging
import re
import os
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("auth_email")

# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    try:
        cred_path = os.environ.get('FIREBASE_CREDENTIALS')
        if not cred_path:
            raise ValueError("FIREBASE_CREDENTIALS environment variable not set")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Firebase Admin SDK: {e}")
        raise e

router = APIRouter()

# Password strength evaluation function
def evaluate_password_strength(password: str) -> int:
    strength = 0
    if len(password) >= 8:
        strength += 1
    if re.search(r"[a-z]", password) and re.search(r"[A-Z]", password):
        strength += 1
    if re.search(r"[0-9]", password):
        strength += 1
    if re.search(r"[^a-zA-Z0-9]", password):
        strength += 1
    return strength

# Password validation function
def validate_password(password: str) -> bool:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    if len(password) > 64:
        raise HTTPException(status_code=400, detail="Password must be at most 64 characters.")
    return True

# MongoDB connection function with better error handling
def get_db():
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://cybershield-mongodb:27017/cybershield_db")
    logger.info(f"Connecting to MongoDB at: {MONGO_URI}")
    
    try:
        # Create a client with explicit timeouts
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,  # 5 second timeout for server selection
            connectTimeoutMS=5000,          # 5 second timeout for initial connection
            socketTimeoutMS=30000           # 30 second timeout for operations
        )
        
        # Determine database name
        if MONGO_URI.endswith("/cybershield_db"):
            db_name = MONGO_URI.split("/")[-1]
        else:
            db_name = 'cybershield_db'
            
        db = client[db_name]
        
        # Test the connection
        client.admin.command('ping')
        logger.info("MongoDB connection successful")
        
        # Ensure critical collections exist
        collections = db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        if "users" not in collections:
            db.create_collection("users")
            logger.info("Created users collection")
            
        if "login_logs" not in collections:
            db.create_collection("login_logs")
            logger.info("Created login_logs collection")
            
        return db
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# Function to create login log with robust error handling
def create_login_log(email, status, reason=None, source=None):
    try:
        # Use a direct connection for logging to minimize middleware issues
        client = MongoClient("mongodb://cybershield-mongodb:27017")
        db = client.cybershield_db
        
        # Ensure login_logs collection exists
        if "login_logs" not in db.list_collection_names():
            db.create_collection("login_logs")
        
        # Create log document
        log_doc = {
            "email": email,
            "timestamp": datetime.utcnow(),
            "status": status,
            "source": source or "auth_email.py"
        }
        
        if reason:
            log_doc["reason"] = reason
        
        # Insert document with write concern
        result = db.login_logs.insert_one(log_doc, write_concern={"w": 1})
        logger.info(f"Created login log with ID: {result.inserted_id}")
        
        return result.inserted_id
    except Exception as e:
        logger.error(f"Failed to create login log: {e}")
        logger.error(traceback.format_exc())
        # Don't raise exception - logging should not interrupt main flow
        return None

# Register User Endpoint
@router.post("/register")
async def register_user(
    email: str = Form(...),
    password: str = Form(...),
):
    # Normalize email
    email = email.strip().lower()
    
    allowed_domains = ['gmail.com', 'yahoo.com', 'charusat.edu.in', 'charusat.ac.in']
    
    try:
        domain = email.split('@')[1]
    except IndexError:
        raise HTTPException(status_code=400, detail="Invalid email format")
        
    if domain not in allowed_domains:
        raise HTTPException(status_code=400, detail="Invalid email domain. Please use gmail.com, yahoo.com, charusat.edu.in, or charusat.ac.in")
    
    validate_password(password)
    
    # Evaluate password strength
    password_strength = evaluate_password_strength(password)
    if password_strength < 4:
        raise HTTPException(status_code=400, detail="Password is too weak. Please use a stronger password.")

    try:
        # Get database connection
        db = get_db()
        users_collection = db["users"]
        
        # Check if user already exists
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            create_login_log(email, "failed", "user_already_exists", "register_endpoint")
            raise HTTPException(status_code=409, detail="User with this email already exists")
            
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert user data into MongoDB
        user_data = {
            "email": email,
            "hashed_password": hashed_password.decode('utf-8'),
            "created_at": datetime.utcnow(),
        }
        
        users_collection.insert_one(user_data)
        
        # Log successful registration
        create_login_log(email, "register_success", source="register_endpoint")
        
        return JSONResponse(content={"message": "Registration successful"}, status_code=200)
        
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        logger.error(f"Registration error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

# Login User Endpoint
# Add these debug statements to your login_user function in auth_email.py

@router.post("/login")
async def login_user(
    email: str = Form(...),
    password: str = Form(...),
):
    # Normalize email
    email = email.strip().lower()
    
    try:
        # Get database connection
        logger.info(f"Login attempt for: {email}") # Add this debug line
        db = get_db()
        users_collection = db["users"]
        
        # Retrieve user from MongoDB
        user = users_collection.find_one({"email": email})
        
        # Check if user exists
        if not user:
            logger.info(f"Login failed: User not found for email {email}")
            logger.info("About to create login log for failed attempt") # Add this debug line
            create_login_log(email, "failed", "user_not_found", "login_endpoint")
            logger.info("Login log created for failed attempt") # Add this debug line
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get the stored hashed password
        stored_hash = user["hashed_password"]
        
        # Verify password
        password_correct = bcrypt.checkpw(
            password.encode('utf-8'),
            stored_hash.encode('utf-8')
        )
        
        if not password_correct:
            logger.info(f"Login failed: Incorrect password for {email}")
            logger.info("About to create login log for incorrect password") # Add this debug line
            create_login_log(email, "failed", "incorrect_password", "login_endpoint")
            logger.info("Login log created for incorrect password") # Add this debug line
            raise HTTPException(status_code=401, detail="Incorrect password")
        
        # Password is correct, login successful
        logger.info(f"Login SUCCESS: User {email} authenticated successfully")
        
        # Log successful login
        logger.info("About to create login log for successful login") # Add this debug line
        log_id = create_login_log(email, "success", source="login_endpoint")
        logger.info(f"Login log created with ID: {log_id}") # Add this debug line
        
        if not log_id:
            logger.warning(f"Failed to log successful login for {email}")
        return JSONResponse(
            content={
                "message": "Login successful",
                "email": email,
                "timestamp": str(datetime.utcnow()),
                "status": "success"
            }, 
            status_code=200
        )
            
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        logger.error(f"Login error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

# Log viewer endpoints
@router.get("/check-logs", tags=["logs"])
async def check_logs():
    """Test endpoint that inserts a record and returns recent logs."""
    try:
        db = get_db()
        login_logs_collection = db["login_logs"]
        
        # Insert a test document
        test_doc = {
            "email": "test@example.com",
            "timestamp": datetime.utcnow(),
            "status": "test",
            "source": "check_logs_endpoint"
        }
        
        test_result = login_logs_collection.insert_one(test_doc)
        logger.info(f"Inserted test document with ID: {test_result.inserted_id}")
        
        # Count documents
        log_count = login_logs_collection.count_documents({})
        
        # Find logs
        logs = list(login_logs_collection.find().sort("timestamp", -1).limit(10))
        
        # Format response
        response_logs = [
            {
                "id": str(log.get("_id")),
                "email": log.get("email"),
                "timestamp": str(log.get("timestamp")),
                "status": log.get("status"),
                "reason": log.get("reason", ""),
                "source": log.get("source", "")
            } 
            for log in logs
        ]
            
        return {
            "message": "Logs check completed",
            "database_name": db.name,
            "login_logs_count": log_count,
            "test_document_id": str(test_result.inserted_id),
            "logs": response_logs
        }
    except Exception as e:
        logger.error(f"Error in check_logs: {e}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/view-login-logs", tags=["logs"])
async def view_login_logs():
    """View all login logs."""
    try:
        # Use direct MongoDB connection
        client = MongoClient("mongodb://cybershield-mongodb:27017")
        db = client.cybershield_db
        
        # Ensure login_logs collection exists
        collections = db.list_collection_names()
        if "login_logs" not in collections:
            db.create_collection("login_logs")
            
            # Insert a test document
            test_doc = {
                "email": "test@example.com",
                "timestamp": datetime.utcnow(),
                "status": "test",
                "source": "view_login_logs_endpoint"
            }
            db.login_logs.insert_one(test_doc)
            logger.info("Created login_logs collection with test document")
        
        # Get all logs
        login_logs = list(db.login_logs.find().sort("timestamp", -1))
        logger.info(f"Found {len(login_logs)} login log documents")
        
        # Format response
        formatted_logs = [
            {
                "id": str(log.get("_id")),
                "email": log.get("email", ""),
                "timestamp": str(log.get("timestamp", "")),
                "status": log.get("status", ""),
                "reason": log.get("reason", ""),
                "source": log.get("source", "")
            }
            for log in login_logs
        ]
        
        # Get users for reference
        users = list(db.users.find({}, {"email": 1}))
        user_emails = [user.get("email") for user in users]
        
        return {
            "message": "Login logs retrieved",
            "login_logs_count": len(login_logs),
            "user_count": len(users),
            "user_emails": user_emails,
            "login_logs": formatted_logs
        }
    except Exception as e:
        logger.error(f"Error in view_login_logs: {e}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/direct-logs", tags=["logs"])
async def direct_logs():
    """Alternative implementation for viewing logs with test document."""
    try:
        # Direct MongoDB connection
        client = MongoClient("mongodb://cybershield-mongodb:27017")
        db = client.cybershield_db
        
        # Check all collections
        collections = db.list_collection_names()
        
        # Ensure login_logs collection exists
        if "login_logs" not in collections:
            db.create_collection("login_logs")
        
        # Insert a test document
        test_doc = {
            "email": "direct-test@example.com",
            "timestamp": datetime.utcnow(),
            "status": "direct-test",
            "source": "direct_logs_endpoint"
        }
        
        result = db.login_logs.insert_one(test_doc)
        logger.info(f"Inserted direct test document with ID: {result.inserted_id}")
        
        # Get logs
        logs = list(db.login_logs.find().sort("timestamp", -1))
        
        # Format logs
        formatted_logs = [
            {
                "id": str(log.get("_id")),
                "email": log.get("email", ""),
                "timestamp": str(log.get("timestamp", "")),
                "status": log.get("status", ""),
                "source": log.get("source", ""),
                "reason": log.get("reason", "")
            }
            for log in logs
        ]
        
        return {
            "collections": collections,
            "inserted_id": str(result.inserted_id),
            "logs_count": len(logs),
            "logs": formatted_logs
        }
    except Exception as e:
        logger.error(f"Error in direct_logs: {e}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }