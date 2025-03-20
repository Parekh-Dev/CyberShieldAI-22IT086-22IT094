from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from datetime import datetime
import os
import traceback

router = APIRouter()

def get_direct_db():
    """Get a direct database connection bypassing any middlewares."""
    try:
        # Use the environment variable first, fallback to direct container name
        mongo_uri = os.environ.get("MONGO_URI", "mongodb://cybershield-mongodb:27017/cybershield_db")
        print(f"Connecting directly to MongoDB at: {mongo_uri}")
        
        client = MongoClient(mongo_uri)
        db = client.get_database()
        
        # Test connection
        client.admin.command('ping')
        print("Direct MongoDB connection successful")
        
        return db
    except Exception as e:
        print(f"Direct MongoDB connection error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@router.get("/view-all-logs")
async def view_all_logs():
    """View all logs in the database."""
    try:
        db = get_direct_db()
        
        # Check if collections exist
        collections = db.list_collection_names()
        
        # Get user data
        users = []
        if "users" in collections:
            user_docs = db.users.find({}, {"email": 1, "created_at": 1})
            for user in user_docs:
                users.append({
                    "id": str(user.get("_id")),
                    "email": user.get("email"),
                    "created_at": str(user.get("created_at", ""))
                })
        
        # Get login logs
        login_logs = []
        if "login_logs" in collections:
            log_docs = db.login_logs.find().sort("timestamp", -1)
            for log in log_docs:
                login_logs.append({
                    "id": str(log.get("_id")),
                    "email": log.get("email", ""),
                    "timestamp": str(log.get("timestamp", "")),
                    "status": log.get("status", ""),
                    "reason": log.get("reason", ""),
                    "source": log.get("source", "")
                })
        
        # Insert a test log to verify write access
        test_log = {
            "email": "admin-test@example.com",
            "timestamp": datetime.utcnow(),
            "status": "admin-test",
            "source": "db_admin_endpoint"
        }
        
        test_result = None
        if "login_logs" in collections:
            test_result = db.login_logs.insert_one(test_log)
        else:
            db.create_collection("login_logs")
            test_result = db.login_logs.insert_one(test_log)
        
        return {
            "message": "Database report generated",
            "test_log_id": str(test_result.inserted_id) if test_result else None,
            "database_name": db.name,
            "collections": collections,
            "user_count": len(users),
            "users": users,
            "login_logs_count": len(login_logs),
            "login_logs": login_logs
        }
    except Exception as e:
        print(f"Error in view_all_logs: {str(e)}")
        print(traceback.format_exc())
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }

@router.get("/test-db-connection")
async def test_db_connection():
    """Test database connection and operations."""
    try:
        # Try direct MongoDB connection (container networking)
        direct_client = MongoClient("mongodb://cybershield-mongodb:27017")
        direct_db = direct_client.cybershield_db
        
        # Try localhost connection
        local_client = MongoClient("mongodb://localhost:27017")
        local_db = local_client.cybershield_db
        
        # Try env var connection
        env_uri = os.environ.get("MONGO_URI", "none")
        env_client = None
        env_db = None
        
        if env_uri != "none":
            env_client = MongoClient(env_uri)
            env_db = env_client.get_database()
        
        # Test write to each connection
        direct_result = None
        local_result = None
        env_result = None
        direct_error = None
        local_error = None
        env_error = None
        
        try:
            direct_result = direct_db.login_logs.insert_one({
                "email": "direct@test.com",
                "timestamp": datetime.utcnow(),
                "status": "test",
                "source": "direct_connection"
            })
        except Exception as e1:
            direct_error = str(e1)
        
        try:
            local_result = local_db.login_logs.insert_one({
                "email": "local@test.com",
                "timestamp": datetime.utcnow(),
                "status": "test",
                "source": "local_connection"
            })
        except Exception as e2:
            local_error = str(e2)
        
        if env_client:
            try:
                env_result = env_db.login_logs.insert_one({
                    "email": "env@test.com",
                    "timestamp": datetime.utcnow(),
                    "status": "test",
                    "source": "env_connection"
                })
            except Exception as e3:
                env_error = str(e3)
        
        return {
            "message": "Connection tests completed",
            "direct_connection": {
                "success": direct_result is not None,
                "inserted_id": str(direct_result.inserted_id) if direct_result else None,
                "error": direct_error if not direct_result else None
            },
            "local_connection": {
                "success": local_result is not None,
                "inserted_id": str(local_result.inserted_id) if local_result else None,
                "error": local_error if not local_result else None
            },
            "env_connection": {
                "success": env_result is not None,
                "inserted_id": str(env_result.inserted_id) if env_result else None,
                "error": env_error if not env_result else None,
                "env_uri": env_uri
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }