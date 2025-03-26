import logging
from datetime import datetime
from pymongo import MongoClient

class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger('security_logger')
        self.client = MongoClient("mongodb://cybershield-mongodb:27017")
        self.db = self.client.cybershield_db

    def log_login_attempt(self, email, status, reason=None, source=None, ip_address=None, user_agent=None):
        log_entry = {
            "email": email,
            "timestamp": datetime.utcnow(),
            "status": status,
            "source": source or "security_logger"
        }
        
        if reason:
            log_entry["reason"] = reason
        if ip_address:
            log_entry["ip_address"] = ip_address
        if user_agent:
            log_entry["user_agent"] = user_agent

        try:
            result = self.db.login_logs.insert_one(log_entry)
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Failed to log login attempt: {e}")
            return None

    def log_security_event(self, event_type, severity="low", details=None):
        try:
            event = {
                "timestamp": datetime.utcnow(),
                "event_type": event_type,
                "severity": severity,
                "details": details or {}
            }
            result = self.db.security_events.insert_one(event)
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")
            return None

    def log_access(self, endpoint, method, user_id=None, ip_address=None, status_code=None, duration_ms=None):
        try:
            access_log = {
                "timestamp": datetime.utcnow(),
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_ms": duration_ms
            }
            
            if user_id:
                access_log["user_id"] = user_id
            if ip_address:
                access_log["ip_address"] = ip_address

            result = self.db.access_logs.insert_one(access_log)
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Failed to log access: {e}")
            return None

    def get_security_logs(self, log_type="login_logs", limit=100):
        try:
            collection = getattr(self.db, log_type)
            return list(collection.find().sort("timestamp", -1).limit(limit))
        except Exception as e:
            self.logger.error(f"Failed to retrieve logs: {e}")
            return []

# Create a single instance
security_logger = SecurityLogger()