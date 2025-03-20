"""
Security dashboard module for CyberShield-AI.
Provides visualization and analytics for security data.
"""

from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timedelta
import logging
import traceback
from pymongo import MongoClient
from security_logger import security_logger
import time
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("security_dashboard")

# Create router
router = APIRouter(
    prefix="/security-dashboard",
    tags=["security-dashboard"],
)

def get_db():
    """Get MongoDB connection with error handling."""
    try:
        client = MongoClient("mongodb://cybershield-mongodb:27017")
        db = client.cybershield_db
        return db
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@router.get("/summary")
async def get_security_summary(request: Request):
    """
    Get a summary of security metrics for the dashboard.
    """
    start_time = time.time()
    
    try:
        db = get_db()
        
        # Get time periods for metrics
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)
        
        # Get login metrics
        total_logins = db.login_logs.count_documents({"status": "success"})
        today_logins = db.login_logs.count_documents({
            "status": "success", 
            "timestamp": {"$gte": today_start}
        })
        
        # Get failed login metrics
        total_failed = db.login_logs.count_documents({"status": "failed"})
        today_failed = db.login_logs.count_documents({
            "status": "failed", 
            "timestamp": {"$gte": today_start}
        })
        
        # Get security events by severity
        high_severity = db.security_events.count_documents({"severity": "high"})
        medium_severity = db.security_events.count_documents({"severity": "medium"})
        low_severity = db.security_events.count_documents({"severity": "low"})
        
        # Get user metrics
        total_users = db.users.count_documents({})
        new_users_today = db.users.count_documents({
            "created_at": {"$gte": today_start}
        })
        
        # Login trends by day for the past week
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": week_start}
                }
            },
            {
                "$project": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "status": 1
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": "$date",
                        "status": "$status"
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id.date": 1}
            }
        ]
        
        login_trends = list(db.login_logs.aggregate(pipeline))
        
        # Format login trends for easy charting
        trend_data = {}
        for item in login_trends:
            date = item["_id"]["date"]
            status = item["_id"]["status"]
            count = item["count"]
            
            if date not in trend_data:
                trend_data[date] = {"success": 0, "failed": 0}
                
            if status in ["success", "failed"]:
                trend_data[date][status] = count
        
        # Convert to list of dates and values for charting
        trend_dates = list(trend_data.keys())
        trend_success = [trend_data[date]["success"] for date in trend_dates]
        trend_failed = [trend_data[date]["failed"] for date in trend_dates]
        
        # Get recent security events
        recent_events = list(db.security_events.find().sort("timestamp", -1).limit(10))
        for event in recent_events:
            event["_id"] = str(event["_id"])
            event["timestamp"] = str(event["timestamp"])
        
        # Log API access
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-dashboard/summary",
            method="GET",
            ip_address=ip_address,
            status_code=200,
            duration_ms=duration_ms
        )
        
        return {
            "login_metrics": {
                "total_logins": total_logins,
                "today_logins": today_logins,
                "total_failed": total_failed,
                "today_failed": today_failed,
                "failure_rate": round((total_failed / (total_logins + total_failed)) * 100, 2) if (total_logins + total_failed) > 0 else 0
            },
            "security_events": {
                "high": high_severity,
                "medium": medium_severity,
                "low": low_severity,
                "total": high_severity + medium_severity + low_severity
            },
            "user_metrics": {
                "total_users": total_users,
                "new_users_today": new_users_today
            },
            "login_trends": {
                "dates": trend_dates,
                "success": trend_success,
                "failed": trend_failed
            },
            "recent_events": recent_events
        }
        
    except Exception as e:
        logger.error(f"Error in security dashboard summary: {e}")
        logger.error(traceback.format_exc())
        
        # Log API error
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-dashboard/summary",
            method="GET",
            ip_address=ip_address,
            status_code=500,
            duration_ms=duration_ms
        )
        
        raise HTTPException(status_code=500, detail=f"Error generating security summary: {str(e)}")

@router.get("/user-activity/{email}")
async def get_user_activity(email: str, request: Request):
    """
    Get activity data for a specific user.
    """
    start_time = time.time()
    
    try:
        db = get_db()
        
        # Normalize email
        email = email.strip().lower()
        
        # Check if user exists
        user = db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"])
        
        # Get user login history
        login_history = list(db.login_logs.find(
            {"email": email}
        ).sort("timestamp", -1).limit(100))
        
        # Format login history
        formatted_history = []
        for log in login_history:
            formatted_history.append({
                "id": str(log["_id"]),
                "timestamp": str(log["timestamp"]),
                "status": log["status"],
                "source": log.get("source", ""),
                "ip_address": log.get("ip_address", ""),
                "user_agent": log.get("user_agent", "")
            })
        
        # Get user's security events
        security_events = list(db.security_events.find(
            {"details.email": email}
        ).sort("timestamp", -1).limit(50))
        
        # Format security events
        formatted_events = []
        for event in security_events:
            formatted_events.append({
                "id": str(event["_id"]),
                "timestamp": str(event["timestamp"]),
                "event_type": event["event_type"],
                "severity": event["severity"],
                "details": event["details"]
            })
        
        # Get user's access logs
        access_logs = list(db.access_logs.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(100))
        
        # Format access logs
        formatted_access = []
        for log in access_logs:
            formatted_access.append({
                "id": str(log["_id"]),
                "timestamp": str(log["timestamp"]),
                "endpoint": log["endpoint"],
                "method": log["method"],
                "status_code": log.get("status_code", 0),
                "duration_ms": log.get("duration_ms", 0),
                "ip_address": log.get("ip_address", "")
            })
        
        # Log API access
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint=f"/security-dashboard/user-activity/{email}",
            method="GET",
            ip_address=ip_address,
            user_id=user_id,
            status_code=200,
            duration_ms=duration_ms
        )
        
        return {
            "user": {
                "email": email,
                "user_id": user_id,
                "created_at": str(user.get("created_at", ""))
            },
            "login_history": formatted_history,
            "security_events": formatted_events,
            "access_logs": formatted_access,
            "metrics": {
                "total_logins": len([log for log in login_history if log["status"] == "success"]),
                "failed_logins": len([log for log in login_history if log["status"] == "failed"]),
                "security_events_count": len(formatted_events),
                "access_logs_count": len(formatted_access)
            }
        }
        
    except HTTPException as http_exception:
        # Log API access for HTTP exception
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint=f"/security-dashboard/user-activity/{email}",
            method="GET",
            ip_address=ip_address,
            status_code=http_exception.status_code,
            duration_ms=duration_ms
        )
        raise http_exception
        
    except Exception as e:
        logger.error(f"Error getting user activity: {e}")
        logger.error(traceback.format_exc())
        
        # Log API error
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint=f"/security-dashboard/user-activity/{email}",
            method="GET",
            ip_address=ip_address,
            status_code=500,
            duration_ms=duration_ms
        )
        
        raise HTTPException(status_code=500, detail=f"Error retrieving user activity: {str(e)}")

@router.get("/threats-analysis")
async def get_threats_analysis(request: Request):
    """
    Get threats analysis and insights.
    """
    start_time = time.time()
    
    try:
        db = get_db()
        
        # Time ranges
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)
        
        # Threats by type
        pipeline = [
            {
                "$match": {
                    "severity": {"$in": ["high", "critical"]},
                    "timestamp": {"$gte": month_start}
                }
            },
            {
                "$group": {
                    "_id": "$event_type",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]
        
        threats_by_type = list(db.security_events.aggregate(pipeline))
        
        # Format threats by type
        formatted_threats = []
        for threat in threats_by_type:
            formatted_threats.append({
                "type": threat["_id"],
                "count": threat["count"]
            })
        
        # Multiple failed logins from same IP
        pipeline = [
            {
                "$match": {
                    "status": "failed",
                    "timestamp": {"$gte": week_start},
                    "ip_address": {"$exists": True, "$ne": None}
                }
            },
            {
                "$group": {
                    "_id": "$ip_address",
                    "count": {"$sum": 1},
                    "emails": {"$addToSet": "$email"}
                }
            },
            {
                "$match": {
                    "count": {"$gte": 5}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]
        
        suspicious_ips = list(db.login_logs.aggregate(pipeline))
        
        # Format suspicious IPs
        formatted_ips = []
        for ip_data in suspicious_ips:
            formatted_ips.append({
                "ip_address": ip_data["_id"],
                "failed_attempts": ip_data["count"],
                "unique_emails_targeted": len(ip_data["emails"]),
                "emails": ip_data["emails"][:5]  # Only return first 5 emails for privacy
            })
        
        # Password guessing attacks (multiple failures for same email)
        pipeline = [
            {
                "$match": {
                    "status": "failed",
                    "reason": "incorrect_password",
                    "timestamp": {"$gte": week_start}
                }
            },
            {
                "$group": {
                    "_id": "$email",
                    "count": {"$sum": 1},
                    "ips": {"$addToSet": "$ip_address"}
                }
            },
            {
                "$match": {
                    "count": {"$gte": 3}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]
        
        password_guessing = list(db.login_logs.aggregate(pipeline))
        
        # Format password guessing data
        formatted_guessing = []
        for guess_data in password_guessing:
            formatted_guessing.append({
                "email": guess_data["_id"],
                "failed_attempts": guess_data["count"],
                "unique_ips": len([ip for ip in guess_data["ips"] if ip])
            })
        
        # Log API access
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-dashboard/threats-analysis",
            method="GET",
            ip_address=ip_address,
            status_code=200,
            duration_ms=duration_ms
        )
        
        return {
            "high_severity_threats": {
                "total": len(formatted_threats),
                "by_type": formatted_threats
            },
            "suspicious_ips": {
                "total": len(formatted_ips),
                "data": formatted_ips
            },
            "password_guessing": {
                "total": len(formatted_guessing),
                "data": formatted_guessing
            },
            "summary": {
                "threat_level": "high" if (len(formatted_ips) > 0 or len(formatted_guessing) > 3) else "medium" if len(formatted_guessing) > 0 else "low",
                "most_targeted_emails": [item["email"] for item in formatted_guessing[:3]],
                "most_suspicious_ips": [item["ip_address"] for item in formatted_ips[:3]]
            }
        }
        
    except Exception as e:
        logger.error(f"Error in threats analysis: {e}")
        logger.error(traceback.format_exc())
        
        # Log API error
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-dashboard/threats-analysis",
            method="GET",
            ip_address=ip_address,
            status_code=500,
            duration_ms=duration_ms
        )
        
        raise HTTPException(status_code=500, detail=f"Error generating threats analysis: {str(e)}")