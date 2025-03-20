"""
Security monitoring API for CyberShield-AI.
Provides endpoints for security monitoring and alerts.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Query
from datetime import datetime, timedelta
import logging
import traceback
from pymongo import MongoClient
from security_logger import security_logger
import time
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("security_monitor_api")

# Create router
router = APIRouter(
    prefix="/security-monitor",
    tags=["security-monitor"],
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

@router.get("/login-attempts")
async def get_login_attempts(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status (success/failed)"),
    email: Optional[str] = Query(None, description="Filter by email"),
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results")
):
    """
    Get login attempts with filtering options.
    """
    start_time = time.time()
    
    try:
        db = get_db()
        
        # Build filter
        filter_criteria = {}
        
        if status:
            filter_criteria["status"] = status
            
        if email:
            filter_criteria["email"] = email.lower()
            
        # Handle date range
        if from_date or to_date:
            filter_criteria["timestamp"] = {}
            
            if from_date:
                try:
                    from_datetime = datetime.strptime(from_date, "%Y-%m-%d")
                    filter_criteria["timestamp"]["$gte"] = from_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid from_date format. Use YYYY-MM-DD")
                    
            if to_date:
                try:
                    to_datetime = datetime.strptime(to_date, "%Y-%m-%d")
                    # Add one day to include the entire end date
                    to_datetime = to_datetime + timedelta(days=1)
                    filter_criteria["timestamp"]["$lt"] = to_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid to_date format. Use YYYY-MM-DD")
        
        # Execute query
        login_logs = list(db.login_logs.find(
            filter_criteria
        ).sort("timestamp", -1).limit(limit))
        
        # Format results
        formatted_logs = []
        for log in login_logs:
            formatted_logs.append({
                "id": str(log["_id"]),
                "email": log.get("email", ""),
                "timestamp": str(log.get("timestamp", "")),
                "status": log.get("status", ""),
                "reason": log.get("reason", ""),
                "source": log.get("source", ""),
                "ip_address": log.get("ip_address", ""),
                "user_agent": log.get("user_agent", "")
            })
        
        # Get total count for pagination
        total_count = db.login_logs.count_documents(filter_criteria)
        
        # Log API access
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-monitor/login-attempts",
            method="GET",
            ip_address=ip_address,
            status_code=200,
            duration_ms=duration_ms
        )
        
        return {
            "total": total_count,
            "returned": len(formatted_logs),
            "login_attempts": formatted_logs
        }
        
    except HTTPException as http_exception:
        # Log API access for HTTP exception
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-monitor/login-attempts",
            method="GET",
            ip_address=ip_address,
            status_code=http_exception.status_code,
            duration_ms=duration_ms
        )
        raise http_exception
        
    except Exception as e:
        logger.error(f"Error getting login attempts: {e}")
        logger.error(traceback.format_exc())
        
        # Log API error
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-monitor/login-attempts",
            method="GET",
            ip_address=ip_address,
            status_code=500,
            duration_ms=duration_ms
        )
        
        raise HTTPException(status_code=500, detail=f"Error retrieving login attempts: {str(e)}")

@router.get("/security-events")
async def get_security_events(
    request: Request,
    severity: Optional[str] = Query(None, description="Filter by severity (low/medium/high/critical)"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results")
):
    """
    Get security events with filtering options.
    """
    start_time = time.time()
    
    try:
        db = get_db()
        
        # Build filter
        filter_criteria = {}
        
        if severity:
            filter_criteria["severity"] = severity
            
        if event_type:
            filter_criteria["event_type"] = event_type
            
        # Handle date range
        if from_date or to_date:
            filter_criteria["timestamp"] = {}
            
            if from_date:
                try:
                    from_datetime = datetime.strptime(from_date, "%Y-%m-%d")
                    filter_criteria["timestamp"]["$gte"] = from_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid from_date format. Use YYYY-MM-DD")
                    
            if to_date:
                try:
                    to_datetime = datetime.strptime(to_date, "%Y-%m-%d")
                    # Add one day to include the entire end date
                    to_datetime = to_datetime + timedelta(days=1)
                    filter_criteria["timestamp"]["$lt"] = to_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid to_date format. Use YYYY-MM-DD")
        
        # Execute query
        security_events = list(db.security_events.find(
            filter_criteria
        ).sort("timestamp", -1).limit(limit))
        
        # Format results
        formatted_events = []
        for event in security_events:
            formatted_events.append({
                "id": str(event["_id"]),
                "timestamp": str(event.get("timestamp", "")),
                "event_type": event.get("event_type", ""),
                "severity": event.get("severity", ""),
                "details": event.get("details", {}),
                "user_id": event.get("user_id", "")
            })
        
        # Get total count for pagination
        total_count = db.security_events.count_documents(filter_criteria)
        
        # Log API access
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-monitor/security-events",
            method="GET",
            ip_address=ip_address,
            status_code=200,
            duration_ms=duration_ms
        )
        
        return {
            "total": total_count,
            "returned": len(formatted_events),
            "security_events": formatted_events
        }
        
    except HTTPException as http_exception:
        # Log API access for HTTP exception
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-monitor/security-events",
            method="GET",
            ip_address=ip_address,
            status_code=http_exception.status_code,
            duration_ms=duration_ms
        )
        raise http_exception
        
    except Exception as e:
        logger.error(f"Error getting security events: {e}")
        logger.error(traceback.format_exc())
        
        # Log API error
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-monitor/security-events",
            method="GET",
            ip_address=ip_address,
            status_code=500,
            duration_ms=duration_ms
        )
        
        raise HTTPException(status_code=500, detail=f"Error retrieving security events: {str(e)}")

@router.get("/active-threats")
async def get_active_threats(request: Request):
    """
    Get currently active security threats that need attention.
    """
    start_time = time.time()
    
    try:
        db = get_db()
        
        # Time thresholds
        now = datetime.utcnow()
        last_hour"""
Security monitoring API for CyberShield-AI.
Provides endpoints for security monitoring and alerts.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Query
from datetime import datetime, timedelta
import logging
import traceback
from pymongo import MongoClient
from security_logger import security_logger
import time
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("security_monitor_api")

# Create router
router = APIRouter(
    prefix="/security-monitor",
    tags=["security-monitor"],
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

@router.get("/login-attempts")
async def get_login_attempts(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status (success/failed)"),
    email: Optional[str] = Query(None, description="Filter by email"),
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results")
):
    """
    Get login attempts with filtering options.
    """
    start_time = time.time()
    
    try:
        db = get_db()
        
        # Build filter
        filter_criteria = {}
        
        if status:
            filter_criteria["status"] = status
            
        if email:
            filter_criteria["email"] = email.lower()
            
        # Handle date range
        if from_date or to_date:
            filter_criteria["timestamp"] = {}
            
            if from_date:
                try:
                    from_datetime = datetime.strptime(from_date, "%Y-%m-%d")
                    filter_criteria["timestamp"]["$gte"] = from_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid from_date format. Use YYYY-MM-DD")
                    
            if to_date:
                try:
                    to_datetime = datetime.strptime(to_date, "%Y-%m-%d")
                    # Add one day to include the entire end date
                    to_datetime = to_datetime + timedelta(days=1)
                    filter_criteria["timestamp"]["$lt"] = to_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid to_date format. Use YYYY-MM-DD")
        
        # Execute query
        login_logs = list(db.login_logs.find(
            filter_criteria
        ).sort("timestamp", -1).limit(limit))
        
        # Format results
        formatted_logs = []
        for log in login_logs:
            formatted_logs.append({
                "id": str(log["_id"]),
                "email": log.get("email", ""),
                "timestamp": str(log.get("timestamp", "")),
                "status": log.get("status", ""),
                "reason": log.get("reason", ""),
                "source": log.get("source", ""),
                "ip_address": log.get("ip_address", ""),
                "user_agent": log.get("user_agent", "")
            })
        
        # Get total count for pagination
        total_count = db.login_logs.count_documents(filter_criteria)
        
        # Log API access
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-monitor/login-attempts",
            method="GET",
            ip_address=ip_address,
            status_code=200,
            duration_ms=duration_ms
        )
        
        return {
            "total": total_count,
            "returned": len(formatted_logs),
            "login_attempts": formatted_logs
        }
        
    except HTTPException as http_exception:
        # Log API access for HTTP exception
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-monitor/login-attempts",
            method="GET",
            ip_address=ip_address,
            status_code=http_exception.status_code,
            duration_ms=duration_ms
        )
        raise http_exception
        
    except Exception as e:
        logger.error(f"Error getting login attempts: {e}")
        logger.error(traceback.format_exc())
        
        # Log API error
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-monitor/login-attempts",
            method="GET",
            ip_address=ip_address,
            status_code=500,
            duration_ms=duration_ms
        )
        
        raise HTTPException(status_code=500, detail=f"Error retrieving login attempts: {str(e)}")

@router.get("/security-events")
async def get_security_events(
    request: Request,
    severity: Optional[str] = Query(None, description="Filter by severity (low/medium/high/critical)"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results")
):
    """
    Get security events with filtering options.
    """
    start_time = time.time()
    
    try:
        db = get_db()
        
        # Build filter
        filter_criteria = {}
        
        if severity:
            filter_criteria["severity"] = severity
            
        if event_type:
            filter_criteria["event_type"] = event_type
            
        # Handle date range
        if from_date or to_date:
            filter_criteria["timestamp"] = {}
            
            if from_date:
                try:
                    from_datetime = datetime.strptime(from_date, "%Y-%m-%d")
                    filter_criteria["timestamp"]["$gte"] = from_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid from_date format. Use YYYY-MM-DD")
                    
            if to_date:
                try:
                    to_datetime = datetime.strptime(to_date, "%Y-%m-%d")
                    # Add one day to include the entire end date
                    to_datetime = to_datetime + timedelta(days=1)
                    filter_criteria["timestamp"]["$lt"] = to_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid to_date format. Use YYYY-MM-DD")
        
        # Execute query
        security_events = list(db.security_events.find(
            filter_criteria
        ).sort("timestamp", -1).limit(limit))
        
        # Format results
        formatted_events = []
        for event in security_events:
            formatted_events.append({
                "id": str(event["_id"]),
                "timestamp": str(event.get("timestamp", "")),
                "event_type": event.get("event_type", ""),
                "severity": event.get("severity", ""),
                "details": event.get("details", {}),
                "user_id": event.get("user_id", "")
            })
        
        # Get total count for pagination
        total_count = db.security_events.count_documents(filter_criteria)
        
        # Log API access
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-monitor/security-events",
            method="GET",
            ip_address=ip_address,
            status_code=200,
            duration_ms=duration_ms
        )
        
        return {
            "total": total_count,
            "returned": len(formatted_events),
            "security_events": formatted_events
        }
        
    except HTTPException as http_exception:
        # Log API access for HTTP exception
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-monitor/security-events",
            method="GET",
            ip_address=ip_address,
            status_code=http_exception.status_code,
            duration_ms=duration_ms
        )
        raise http_exception
        
    except Exception as e:
        logger.error(f"Error getting security events: {e}")
        logger.error(traceback.format_exc())
        
        # Log API error
        ip_address = request.client.host if request.client else None
        duration_ms = round((time.time() - start_time) * 1000)
        security_logger.log_access(
            endpoint="/security-monitor/security-events",
            method="GET",
            ip_address=ip_address,
            status_code=500,
            duration_ms=duration_ms
        )
        
        raise HTTPException(status_code=500, detail=f"Error retrieving security events: {str(e)}")

@router.get("/active-threats")
async def get_active_threats(request: Request):
    """
    Get currently active security threats that need attention.
    """
    start_time = time.time()
    
    try:
        db = get_db()
        
        # Time thresholds
        now = datetime.utcnow()
        last_hour