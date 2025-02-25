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

logging.basicConfig(level=logging.DEBUG)

# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(r"C:\Users\devpa\Downloads\CyberShield-AI\backend\cybershieldai-firebase-adminsdk-fbsvc-36a8d0d55c.json")
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")

router = APIRouter()

# Password validation function
def validate_password(password: str) -> bool:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    if len(password) > 64:
        raise HTTPException(status_code=400, detail="Password must be at most 64 characters.")
    return True

# MongoDB connection function
def get_db():
    MONGO_URI = "mongodb://localhost:27017"
    client = MongoClient(MONGO_URI)
    db = client['cybershield_db']
    return db

# ✅ Register User Endpoint
@router.post("/register")
async def register_user(
    email: str = Form(...),
    password: str = Form(...),
    db: MongoClient = Depends(get_db)
):
    allowed_domains = ['gmail.com', 'yahoo.com', 'charusat.edu.in', 'charusat.ac.in']
    domain = email.split('@')[1]

    if domain not in allowed_domains:
        raise HTTPException(status_code=400, detail="Invalid email domain.  Please use gmail.com, yahoo.com, charusat.edu.in, or charusat.ac.in")
    validate_password(password)

    try:
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert user data into MongoDB
        try:
            user_data = {
                "email": email,
                "hashed_password": hashed_password.decode('utf-8'),
            }
            users_collection = db["users"]
            users_collection.insert_one(user_data)
            return JSONResponse(content={"message": "Registration successful"}, status_code=200)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"MongoDB: {str(e)}")
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Login User Endpoint
@router.post("/login")
async def login_user(
    email: str = Form(...),
    password: str = Form(...),
    db: MongoClient = Depends(get_db)
):
    try:
        # Retrieve user from MongoDB
        users_collection = db["users"]
        user = users_collection.find_one({"email": email})

        # Get the login_logs collection
        login_logs_collection = db["login_logs"]

        if user:
            # Fetch hashed password from database
            hashed_password = user["hashed_password"]

            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                # Authentication successful
                # Log the successful login attempt
                login_logs_collection.insert_one({
                    "email": email,
                    "timestamp": datetime.utcnow(),
                    "status": "success"
                })
                return JSONResponse(content={"message": "Login successful"}, status_code=200)
            else:
                # Log the failed login attempt (incorrect password)
                login_logs_collection.insert_one({
                    "email": email,
                    "timestamp": datetime.utcnow(),
                    "status": "failed",
                    "reason": "incorrect_password"
                })
                raise HTTPException(status_code=401, detail="Incorrect password")
        else:
            # Log the failed login attempt (user not found)
            login_logs_collection.insert_one({
                "email": email,
                "timestamp": datetime.utcnow(),
                "status": "failed",
                "reason": "user_not_found"
            })
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        # Log any other errors
        login_logs_collection.insert_one({
            "email": email,
            "timestamp": datetime.utcnow(),
            "status": "error",
            "reason": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))