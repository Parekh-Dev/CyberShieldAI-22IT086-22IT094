import firebase_admin
from firebase_admin import auth, credentials
from fastapi import APIRouter, HTTPException, Depends, Form
from pydantic import BaseModel
import re
from pymongo import MongoClient
from datetime import datetime
import os
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth_phone")

# Initialize Firebase Admin SDK (if not already initialized)
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
        logger.error(traceback.format_exc())
        raise e

router = APIRouter()

# Pydantic models
class UserPhone(BaseModel):
    phone_number: str

class VerifyOTP(BaseModel):
    phone_number: str
    id_token: str  # Firebase ID token after OTP verification

# Phone number validation function (Indian Format)
def is_valid_phone_number(phone: str) -> bool:
    """Validate Indian phone number format (+91XXXXXXXXXX)"""
    return bool(re.fullmatch(r"^\+91[6-9]\d{9}$", phone))

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
        
        # Ensure phone_verifications collection exists
        collections = db.list_collection_names()
        if "phone_verifications" not in collections:
            db.create_collection("phone_verifications")
            logger.info("Created phone_verifications collection")
        
        # Create index on phone_number for faster lookups
        db.phone_verifications.create_index("phone_number")
        
        return db
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# Function to create activity log with robust error handling
def create_phone_log(phone_number, status, reason=None, source=None):
    try:
        # Use a direct connection for logging to minimize middleware issues
        client = MongoClient("mongodb://cybershield-mongodb:27017")
        db = client.cybershield_db
        
        # Ensure login_logs collection exists
        if "phone_logs" not in db.list_collection_names():
            db.create_collection("phone_logs")
        
        # Create log document
        log_doc = {
            "phone_number": phone_number,
            "timestamp": datetime.utcnow(),
            "status": status,
            "source": source or "auth_phone.py"
        }
        
        if reason:
            log_doc["reason"] = reason
        
        # Insert document with write concern
        result = db.phone_logs.insert_one(log_doc, write_concern={"w": 1})
        logger.info(f"Created phone log with ID: {result.inserted_id}")
        
        return result.inserted_id
    except Exception as e:
        logger.error(f"Failed to create phone log: {e}")
        logger.error(traceback.format_exc())
        # Don't raise exception - logging should not interrupt main flow
        return None

# Endpoint to initiate phone verification
@router.post("/send-otp")
async def send_otp(user: UserPhone):
    try:
        phone_number = user.phone_number.strip()
        logger.info(f"OTP request for phone number: {phone_number}")
        
        if not is_valid_phone_number(phone_number):
            logger.warning(f"Invalid phone number format: {phone_number}")
            create_phone_log(phone_number, "invalid_format", "Invalid phone number format")
            raise HTTPException(
                status_code=400, 
                detail="Invalid phone number format. Use Indian format (+91XXXXXXXXXX)."
            )
        
        # Log the OTP request
        create_phone_log(phone_number, "otp_requested", source="send_otp_endpoint")
        
        # In a real implementation, we might integrate with an SMS service here
        # But since we're using Firebase Authentication, this is handled client-side
        
        return {
            "message": "OTP request should be initiated from the frontend using Firebase SDK.",
            "status": "pending"
        }
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        logger.error(f"Error in send_otp: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error sending OTP: {str(e)}")

# Endpoint to verify OTP
@router.post("/verify-otp")
async def verify_otp(user: VerifyOTP, db = Depends(get_db)):
    try:
        phone_number = user.phone_number.strip()
        id_token = user.id_token
        
        logger.info(f"Verifying OTP for phone number: {phone_number}")
        
        if not is_valid_phone_number(phone_number):
            logger.warning(f"Invalid phone number format in verification: {phone_number}")
            create_phone_log(phone_number, "verification_failed", "Invalid phone number format")
            raise HTTPException(
                status_code=400,
                detail="Invalid phone number format. Use Indian format (+91XXXXXXXXXX)."
            )
        
        try:
            # Verify the Firebase token
            decoded_token = auth.verify_id_token(id_token)
            
            # Check if the phone number matches
            if "phone_number" not in decoded_token:
                logger.warning(f"Token does not contain phone number: {decoded_token}")
                create_phone_log(phone_number, "verification_failed", "Token missing phone number")
                raise HTTPException(
                    status_code=400, 
                    detail="Phone number not found in token. Authentication failed."
                )
                
            token_phone = decoded_token["phone_number"]
            if token_phone != phone_number:
                logger.warning(f"Phone number mismatch: {token_phone} != {phone_number}")
                create_phone_log(
                    phone_number, 
                    "verification_failed", 
                    f"Phone number mismatch: token has {token_phone}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="Phone number in token does not match the provided phone number."
                )
                
            # Store phone verification in MongoDB
            phone_verifications_collection = db["phone_verifications"]
            
            # Check if this phone has been verified before
            existing_verification = phone_verifications_collection.find_one({"phone_number": phone_number})
            
            verification_data = {
                "phone_number": phone_number,
                "firebase_uid": decoded_token["uid"],
                "verified_at": datetime.utcnow(),
                "auth_time": datetime.fromtimestamp(decoded_token["auth_time"]),
                "ip_address": decoded_token.get("ip_address", "unknown")
            }
            
            if existing_verification:
                # Update existing verification
                phone_verifications_collection.update_one(
                    {"phone_number": phone_number},
                    {"$set": verification_data}
                )
                logger.info(f"Updated verification for phone number: {phone_number}")
            else:
                # Create new verification record
                verification_data["created_at"] = datetime.utcnow()
                phone_verifications_collection.insert_one(verification_data)
                logger.info(f"New verification for phone number: {phone_number}")
            
            # Log the successful verification
            create_phone_log(phone_number, "verification_success", source="verify_otp_endpoint")
            
            return {
                "message": "Phone number verified successfully",
                "verified_at": verification_data["verified_at"].isoformat(),
                "firebase_uid": decoded_token["uid"]
            }
            
        except auth.InvalidIdTokenError as token_error:
            logger.warning(f"Invalid token: {token_error}")
            create_phone_log(phone_number, "verification_failed", f"Invalid token: {str(token_error)}")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
            
        except auth.ExpiredIdTokenError:
            logger.warning(f"Expired token for phone: {phone_number}")
            create_phone_log(phone_number, "verification_failed", "Expired token")
            raise HTTPException(status_code=401, detail="Token has expired. Please authenticate again.")
            
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        logger.error(f"Error in verify_otp: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error verifying OTP: {str(e)}")

# Endpoint to check verification status
@router.get("/verification-status/{phone_number}")
async def verification_status(phone_number: str, db = Depends(get_db)):
    try:
        if not is_valid_phone_number(phone_number):
            raise HTTPException(
                status_code=400,
                detail="Invalid phone number format. Use Indian format (+91XXXXXXXXXX)."
            )
        
        # Check if the phone number has been verified
        phone_verifications_collection = db["phone_verifications"]
        verification = phone_verifications_collection.find_one({"phone_number": phone_number})
        
        if not verification:
            return {
                "phone_number": phone_number,
                "is_verified": False,
                "message": "Phone number has not been verified."
            }
        
        return {
            "phone_number": phone_number,
            "is_verified": True,
            "verified_at": verification["verified_at"].isoformat(),
            "firebase_uid": verification["firebase_uid"]
        }
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        logger.error(f"Error in verification_status: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error checking verification status: {str(e)}")

# Check phone logs
@router.get("/check-logs", tags=["logs"])
async def check_phone_logs():
    """View phone authentication logs."""
    try:
        # Use direct MongoDB connection
        client = MongoClient("mongodb://cybershield-mongodb:27017")
        db = client.cybershield_db
        
        # Ensure phone_logs collection exists
        collections = db.list_collection_names()
        if "phone_logs" not in collections:
            db.create_collection("phone_logs")
            
            # Insert a test document
            test_doc = {
                "phone_number": "+911234567890",
                "timestamp": datetime.utcnow(),
                "status": "test",
                "source": "check_phone_logs_endpoint"
            }
            db.phone_logs.insert_one(test_doc)
            logger.info("Created phone_logs collection with test document")
        
        # Get all logs
        phone_logs = list(db.phone_logs.find().sort("timestamp", -1))
        logger.info(f"Found {len(phone_logs)} phone log documents")
        
        # Format response
        formatted_logs = [
            {
                "id": str(log.get("_id")),
                "phone_number": log.get("phone_number", ""),
                "timestamp": str(log.get("timestamp", "")),
                "status": log.get("status", ""),
                "reason": log.get("reason", ""),
                "source": log.get("source", "")
            }
            for log in phone_logs
        ]
        
        # Get verifications for reference
        verifications = list(db.phone_verifications.find({}, {"phone_number": 1}))
        verified_phones = [v.get("phone_number") for v in verifications]
        
        return {
            "message": "Phone logs retrieved",
            "phone_logs_count": len(phone_logs),
            "verification_count": len(verifications),
            "verified_phones": verified_phones,
            "phone_logs": formatted_logs
        }
    except Exception as e:
        logger.error(f"Error in check_phone_logs: {e}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }