import pymongo
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import APIRouter, HTTPException, Depends, Form, Request
from pydantic import BaseModel, EmailStr, validator
from pymongo import MongoClient
from security_logger import security_logger
import bcrypt
from datetime import datetime
import pytz  # Add this import for timezone conversion
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Optional
import logging
import re
import os
import traceback
import time


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
# This function is kept for backward compatibility but uses the security_logger internally
def create_login_log(email, status, reason=None, source=None):
    try:
        return security_logger.log_login_attempt(
            email=email,
            status=status,
            reason=reason,
            source=source or "auth_email.py"
        )
    except Exception as e:
        logger.error(f"Failed to create login log through security_logger: {e}")
        logger.error(traceback.format_exc())
        
        # Fallback to direct MongoDB connection
        try:
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
        except Exception as inner_e:
            logger.error(f"Failed to create login log with direct MongoDB: {inner_e}")
            logger.error(traceback.format_exc())
            # Don't raise exception - logging should not interrupt main flow
            return None

# Helper method to extract request info for logging
def _extract_request_info(request: Request):
    """Extract IP and user agent from request object safely."""
    if not request:
        return None, None
    
    ip_address = None
    user_agent = None
    
    try:
        ip_address = request.client.host if request.client else None
    except Exception:
        pass
        
    try:
        user_agent = request.headers.get("user-agent", "")
    except Exception:
        pass
        
    return ip_address, user_agent

# Register User Endpoint
@router.post("/register")
async def register_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    start_time = time.time()
    
    # Normalize email
    email = email.strip().lower()
    
    allowed_domains = ['gmail.com', 'yahoo.com', 'charusat.edu.in', 'charusat.ac.in']
    
    try:
        domain = email.split('@')[1]
    except IndexError:
        # Log validation failure
        security_logger.log_security_event(
            event_type="validation_failure",
            severity="medium",
            details={"email": email, "reason": "invalid_format"},
        )
        raise HTTPException(status_code=400, detail="Invalid email format")
        
    if domain not in allowed_domains:
        # Log domain restriction
        security_logger.log_security_event(
            event_type="domain_restriction",
            severity="medium",
            details={"email": email, "domain": domain, "allowed_domains": allowed_domains},
        )
        raise HTTPException(status_code=400, detail="Invalid email domain. Please use gmail.com, yahoo.com, charusat.edu.in, or charusat.ac.in")
    
    validate_password(password)
    
    # Evaluate password strength
    password_strength = evaluate_password_strength(password)
    if password_strength < 4:
        # Log weak password attempt
        security_logger.log_security_event(
            event_type="weak_password",
            severity="medium",
            details={"email": email, "strength": password_strength},
        )
        raise HTTPException(status_code=400, detail="Password is too weak. Please use a stronger password.")

    try:
        # Get database connection
        db = get_db()
        users_collection = db["users"]
        
        # Check if user already exists
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            # Log registration attempt for existing user
            ip_address, user_agent = _extract_request_info(request)
            security_logger.log_login_attempt(
                email=email,
                status="failed",
                reason="user_already_exists",
                source="register_endpoint",
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise HTTPException(status_code=409, detail="User with this email already exists")
            
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert user data into MongoDB
        user_data = {
            "email": email,
            "hashed_password": hashed_password.decode('utf-8'),
            "created_at": datetime.utcnow(),
        }
        
        result = users_collection.insert_one(user_data)
        user_id = str(result.inserted_id)
        
        # Log successful registration using enhanced security logger
        ip_address, user_agent = _extract_request_info(request)
        security_logger.log_login_attempt(
            email=email,
            status="register_success",
            source="register_endpoint",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Log access
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/register",
            method="POST",
            user_id=user_id,
            ip_address=ip_address,
            status_code=200,
            duration_ms=duration_ms
        )
        
        return JSONResponse(content={"message": "Registration successful"}, status_code=200)
        
    except HTTPException as http_exception:
        # Log API access for failed request
        duration_ms = round((time.time() - start_time) * 1000)
        ip_address, user_agent = _extract_request_info(request)
        security_logger.log_access(
            endpoint="/register",
            method="POST",
            ip_address=ip_address,
            status_code=http_exception.status_code,
            duration_ms=duration_ms
        )
        raise http_exception
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        logger.error(traceback.format_exc())
        
        # Log unexpected error
        security_logger.log_security_event(
            event_type="registration_error",
            severity="high",
            details={"email": email, "error": str(e), "traceback": traceback.format_exc()},
        )
        
        # Log API access for failed request
        duration_ms = round((time.time() - start_time) * 1000)
        ip_address, user_agent = _extract_request_info(request)
        security_logger.log_access(
            endpoint="/register",
            method="POST",
            ip_address=ip_address,
            status_code=500,
            duration_ms=duration_ms
        )
        
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

# Login User Endpoint
@router.post("/login")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    start_time = time.time()
    
    # Normalize email
    email = email.strip().lower()
    
    try:
        # Get database connection
        logger.info(f"Login attempt for: {email}")
        db = get_db()
        users_collection = db["users"]
        
        # Retrieve user from MongoDB
        user = users_collection.find_one({"email": email})
        
        # Extract request information for logging
        ip_address, user_agent = _extract_request_info(request)
        
        # Check if user exists
        if not user:
            logger.info(f"Login failed: User not found for email {email}")
            
            # Log failed login attempt with enhanced security logger
            security_logger.log_login_attempt(
                email=email,
                status="failed",
                reason="user_not_found",
                source="login_endpoint",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Log security event for multiple failed attempts (example)
            failed_attempts = db.login_logs.count_documents({
                "email": email,
                "status": "failed",
                "timestamp": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
            })
            
            if failed_attempts >= 3:
                security_logger.log_security_event(
                    event_type="multiple_failed_logins",
                    severity="medium",
                    details={"email": email, "count": failed_attempts, "time_window": "today"}
                )
            
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
            
            # Log failed login with enhanced security logger
            security_logger.log_login_attempt(
                email=email,
                status="failed",
                reason="incorrect_password",
                source="login_endpoint",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Check for multiple failed password attempts
            failed_pwd_attempts = db.login_logs.count_documents({
                "email": email,
                "status": "failed",
                "reason": "incorrect_password",
                "timestamp": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
            })
            
            if failed_pwd_attempts >= 5:
                security_logger.log_security_event(
                    event_type="password_guessing",
                    severity="high",
                    details={
                        "email": email,
                        "attempts": failed_pwd_attempts,
                        "ip_address": ip_address
                    }
                )
            
            raise HTTPException(status_code=401, detail="Incorrect password")
        
        # Password is correct, login successful
        logger.info(f"Login SUCCESS: User {email} authenticated successfully")
        
        # Log successful login with enhanced security logger
        log_id = security_logger.log_login_attempt(
            email=email,
            status="success",
            source="login_endpoint",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Get user ID
        user_id = str(user.get("_id"))
        
        # Log API access
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/login",
            method="POST",
            user_id=user_id,
            ip_address=ip_address,
            status_code=200,
            duration_ms=duration_ms
        )
        
        if not log_id:
            logger.warning(f"Failed to log successful login for {email}")
        
        # Convert UTC time to IST for timestamp
        utc_now = datetime.utcnow()
        ist_timezone = pytz.timezone('Asia/Kolkata')
        ist_time = utc_now.replace(tzinfo=pytz.UTC).astimezone(ist_timezone)
        ist_timestamp = ist_time.strftime('%Y-%m-%d %H:%M:%S.%f')
        
        return JSONResponse(
            content={
                "message": "Login successful",
                "email": email,
                "timestamp": ist_timestamp,  # Now using IST timestamp
                "status": "success"
            }, 
            status_code=200
        )
            
    except HTTPException as http_exception:
        # Log API access for failed request
        duration_ms = round((time.time() - start_time) * 1000)
        ip_address, user_agent = _extract_request_info(request)
        security_logger.log_access(
            endpoint="/login",
            method="POST",
            ip_address=ip_address,
            status_code=http_exception.status_code,
            duration_ms=duration_ms
        )
        raise http_exception
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        logger.error(traceback.format_exc())
        
        # Log unexpected error
        security_logger.log_security_event(
            event_type="login_error",
            severity="high",
            details={"email": email, "error": str(e), "traceback": traceback.format_exc()},
        )
        
        # Log API access for error
        duration_ms = round((time.time() - start_time) * 1000)
        ip_address, user_agent = _extract_request_info(request)
        security_logger.log_access(
            endpoint="/login",
            method="POST",
            ip_address=ip_address,
            status_code=500,
            duration_ms=duration_ms
        )
        
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

# Log viewer endpoints
@router.get("/check-logs", tags=["logs"])
async def check_logs(request: Request):
    """Test endpoint that inserts a record and returns recent logs."""
    start_time = time.time()
    
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
        
        # Use enhanced security logger to get logs
        logs = security_logger.get_security_logs(log_type="login_logs", limit=10)
        
        # Log API access
        duration_ms = round((time.time() - start_time) * 1000)
        ip_address, user_agent = _extract_request_info(request)
        security_logger.log_access(
            endpoint="/check-logs",
            method="GET",
            ip_address=ip_address,
            status_code=200,
            duration_ms=duration_ms
        )
            
        return {
            "message": "Logs check completed",
            "database_name": db.name,
            "login_logs_count": log_count,
            "test_document_id": str(test_result.inserted_id),
            "logs": logs
        }
        
    except Exception as e:
        logger.error(f"Error in check_logs: {e}")
        logger.error(traceback.format_exc())
        
        # Log API error
        duration_ms = round((time.time() - start_time) * 1000)
        ip_address, user_agent = _extract_request_info(request)
        security_logger.log_access(
            endpoint="/check-logs",
            method="GET",
            ip_address=ip_address,
            status_code=500,
            duration_ms=duration_ms
        )
        
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/view-login-logs", tags=["logs"])
async def view_login_logs(request: Request):
    """View all login logs."""
    start_time = time.time()
    
    try:
        # Use security logger to get logs
        login_logs = security_logger.get_security_logs(log_type="login_logs", limit=100)
        
        # Get users for reference
        db = get_db()
        users = list(db.users.find({}, {"email": 1}))
        user_emails = [user.get("email") for user in users]
        
        # Log API access
        duration_ms = round((time.time() - start_time) * 1000)
        ip_address, user_agent = _extract_request_info(request)
        security_logger.log_access(
            endpoint="/view-login-logs",
            method="GET",
            ip_address=ip_address,
            status_code=200,
            duration_ms=duration_ms
        )
        
        return {
            "message": "Login logs retrieved",
            "login_logs_count": len(login_logs),
            "user_count": len(users),
            "user_emails": user_emails,
            "login_logs": login_logs
        }
        
    except Exception as e:
        logger.error(f"Error in view_login_logs: {e}")
        logger.error(traceback.format_exc())
        
        # Log API error
        duration_ms = round((time.time() - start_time) * 1000)
        ip_address, user_agent = _extract_request_info(request)
        security_logger.log_access(
            endpoint="/view-login-logs",
            method="GET",
            ip_address=ip_address,
            status_code=500,
            duration_ms=duration_ms
        )
        
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/direct-logs", tags=["logs"])
async def direct_logs(request: Request):
    """Alternative implementation for viewing logs with test document."""
    start_time = time.time()
    
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
        
        # Get all types of logs using security logger
        login_logs = security_logger.get_security_logs(log_type="login_logs", limit=50)
        security_events = security_logger.get_security_logs(log_type="security_events", limit=20)
        access_logs = security_logger.get_security_logs(log_type="access_logs", limit=20)
        
        # Log API access
        duration_ms = round((time.time() - start_time) * 1000)
        ip_address, user_agent = _extract_request_info(request)
        security_logger.log_access(
            endpoint="/direct-logs",
            method="GET",
            ip_address=ip_address,
            status_code=200,
            duration_ms=duration_ms
        )
        
        return {
            "collections": collections,
            "inserted_id": str(result.inserted_id),
            "login_logs_count": len(login_logs),
            "security_events_count": len(security_events),
            "access_logs_count": len(access_logs),
            "login_logs": login_logs[:10],  # First 10 login logs
            "security_events": security_events,
            "access_logs": access_logs
        }
        
    except Exception as e:
        logger.error(f"Error in direct_logs: {e}")
        logger.error(traceback.format_exc())
        
        # Log API error
        duration_ms = round((time.time() - start_time) * 1000)
        ip_address, user_agent = _extract_request_info(request)
        security_logger.log_access(
            endpoint="/direct-logs",
            method="GET",
            ip_address=ip_address,
            status_code=500,
            duration_ms=duration_ms
        )
        
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }