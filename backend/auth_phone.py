import firebase_admin
from firebase_admin import auth, credentials
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import re
from pymongo import MongoClient
from datetime import datetime

# Initialize Firebase Admin SDK (if not already initialized)
if not firebase_admin._apps:
    cred = credentials.Certificate(r"C:\Users\devpa\Downloads\CyberShield-AI\backend\cybershieldai-firebase-adminsdk-fbsvc-36a8d0d55c.json")
    firebase_admin.initialize_app(cred)

router = APIRouter()

# User Model for OTP
class UserPhone(BaseModel):
    phone_number: str

# Function to validate phone number format (Indian Format)
def is_valid_phone_number(phone: str) -> bool:
    return bool(re.fullmatch(r"^\+91[6-9]\d{9}$", phone))  # Matches +91XXXXXXXXXX

# MongoDB connection function
def get_db():
    MONGO_URI = "mongodb://localhost:27017"
    client = MongoClient(MONGO_URI)
    db = client['cybershield_db']
    return db

# Endpoint to send OTP (Handled by Firebase SDK on Frontend)
@router.post("/send-otp")
def send_otp(user: UserPhone):
    if not is_valid_phone_number(user.phone_number):
        raise HTTPException(status_code=400, detail="Invalid phone number format. Use Indian format (+91XXXXXXXXXX).")

    # No need to send OTP from backend, handled by Firebase SDK on frontend
    # Just return a success message indicating the request should be made from the frontend
    return {"message": "OTP request should be initiated from the frontend using Firebase SDK."}

# Endpoint to verify OTP
class VerifyOTP(BaseModel):
    phone_number: str
    id_token: str  # Firebase ID token after OTP verification

@router.post("/verify-otp")
def verify_otp(user: VerifyOTP, db: MongoClient = Depends(get_db)):
    try:
        decoded_token = auth.verify_id_token(user.id_token)

        # Verify phone number in decoded token matches the provided phone number
        if "phone_number" not in decoded_token or decoded_token["phone_number"] != user.phone_number:
            raise HTTPException(status_code=400, detail="Phone number in ID token does not match provided phone number.")

        # Store phone verification details in MongoDB
        phone_verifications_collection = db["phone_verifications"]
        phone_verifications_collection.insert_one({
            "phone_number": user.phone_number,
            "timestamp": datetime.utcnow(),
            "firebase_uid": decoded_token["uid"]  # Store Firebase UID
        })

        return {"message": "OTP verified successfully"}

    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=400, detail="Invalid ID token.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")