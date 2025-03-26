import sys
print(sys.path)

from auth_email import router as auth_email_router  # Changed import
from auth_phone import router as auth_phone_router # Changed import
from pymongo import MongoClient
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
from fastapi.responses import JSONResponse # Import JSONResponse
import traceback

# MongoDB connection function
def get_db():
    # Use the container name for Docker networking
    MONGO_URI = "mongodb://cybershield-mongodb:27017"
    print(f"Connecting to MongoDB at: {MONGO_URI}")
    
    try:
        client = MongoClient(MONGO_URI)
        db = client['cybershield_db']
        
        # Test the connection
        client.admin.command('ping')
        print("MongoDB connection successful in main.py")
        
        return db
    except Exception as e:
        print(f"MongoDB connection error in main.py: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

app = FastAPI()

# Configure CORS
origins = [
     "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:5000",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5000",
    "http://localhost:5500",
    "null",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routers
app.include_router(auth_email_router, prefix="/auth/email", tags=["email_auth"])
app.include_router(auth_phone_router, prefix="/auth/phone", tags=["phone_auth"])

# Define a model for the incoming text
class AnalysisRequest(BaseModel):
    text: str

# Define a model for the analysis response
class AnalysisResponse(BaseModel):
    isHateSpeech: bool

# Mock implementation of hate speech detection (replace with your actual logic)
def detect_hate_speech(text: str) -> bool:
    # This is a placeholder - replace with your actual hate speech detection logic
    # For example, you could use a machine learning model or a rule-based system
    hate_keywords = ["hate", "kill", "stupid"]  # Example keywords
    text = text.lower()
    for keyword in hate_keywords:
        if keyword in text:
            return True
    return False

# New endpoint for text analysis
@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest, db = Depends(get_db)):
    try:
        is_hate_speech = detect_hate_speech(request.text)

        # Store the analysis result in MongoDB (optional)
        analysis_collection = db["analysis_results"]
        analysis_collection.insert_one({
            "text": request.text,
            "is_hate_speech": is_hate_speech,
            "timestamp": datetime.utcnow()
        })

        return AnalysisResponse(isHateSpeech=is_hate_speech)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "Welcome to CyberShield AI"}

# Add a direct logs checking endpoint
@app.get("/direct-check-logs")
async def direct_check_logs():
    try:
        # Connect directly to MongoDB in the container
        client = MongoClient("mongodb://cybershield-mongodb:27017")
        db = client['cybershield_db']
        
        # List all collections
        collections = db.list_collection_names()
        
        # Check if login_logs exists
        if "login_logs" not in collections:
            db.create_collection("login_logs")
            print("Created login_logs collection")
        
        login_logs_collection = db["login_logs"]
        
        # Insert a test document
        test_doc = {
            "email": "direct-test@example.com",
            "timestamp": datetime.utcnow(),
            "status": "test",
            "source": "direct_endpoint"
        }
        
        result = login_logs_collection.insert_one(test_doc)
        
        # Count documents
        log_count = login_logs_collection.count_documents({})
        
        # Find logs
        logs = list(login_logs_collection.find().sort("timestamp", -1).limit(10))
        
        # Format for response
        formatted_logs = []
        for log in logs:
            formatted_log = {
                "id": str(log.get("_id")),
                "email": log.get("email", ""),
                "timestamp": str(log.get("timestamp", "")),
                "status": log.get("status", ""),
                "reason": log.get("reason", ""),
                "source": log.get("source", "")
            }
            formatted_logs.append(formatted_log)
        
        return {
            "message": "Direct logs check completed",
            "mongodb_uri": "mongodb://cybershield-mongodb:27017",
            "database": "cybershield_db",
            "collections": collections,
            "login_logs_count": log_count,
            "test_document_id": str(result.inserted_id),
            "logs": formatted_logs
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/logs", tags=["logs"])
async def view_logs():
    """Simple endpoint to view all logs."""
    try:
        # Connect directly to MongoDB
        client = MongoClient("mongodb://cybershield-mongodb:27017")
        db = client['cybershield_db']
        
        # Check if login_logs exists
        collections = db.list_collection_names()
        if "login_logs" not in collections:
            return {"message": "No login_logs collection found", "collections": collections}
        
        # Get all logs
        logs = list(db.login_logs.find().sort("timestamp", -1))
        
        # Format logs for response
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "id": str(log.get("_id")),
                "email": log.get("email", ""),
                "timestamp": str(log.get("timestamp", "")),
                "status": log.get("status", ""),
                "reason": log.get("reason", ""),
                "source": log.get("source", "")
            })
        
        return {
            "message": "Logs retrieved",
            "count": len(formatted_logs),
            "logs": formatted_logs
        }
    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/health")
def health_check():
    """Health check endpoint for Docker."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)