import sys
print(sys.path)

from .auth_email import router as auth_email_router  # Changed import
from .auth_phone import router as auth_phone_router # Changed import
from pymongo import MongoClient
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
from fastapi.responses import JSONResponse # Import JSONResponse

# MongoDB connection function
def get_db():
    MONGO_URI = "mongodb://localhost:27017"
    client = MongoClient(MONGO_URI)
    db = client['cybershield_db']
    return db

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
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
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
async def analyze_text(request: AnalysisRequest, db: MongoClient = Depends(get_db)):
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)