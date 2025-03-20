# CyberShield AI - Security Dashboard

## Overview

The Security Dashboard provides real-time visualizations and analytics for security-related data in the CyberShield AI application. It allows administrators and security analysts to monitor system security, identify potential threats, and track user activities.

## Features

### Security Summary

The `/security-dashboard/summary` endpoint provides a comprehensive overview of system security:

- **Login Metrics:**
  - Total successful logins
  - Today's successful logins
  - Total failed login attempts
  - Today's failed login attempts
  - Failure rate percentage

- **Security Events by Severity:**
  - High severity events
  - Medium severity events
  - Low severity events

- **User Metrics:**
  - Total registered users
  - New users registered today

- **Login Trends:**
  - Success and failure trends by day
  - Week-over-week comparisons

- **Recent Security Events:**
  - Latest security events with details

### User Activity Monitoring

The `/security-dashboard/user-activity/{email}` endpoint provides detailed activity data for specific users:

- **Login History:**
  - Timestamps
  - Success/failure status
  - IP addresses
  - User agents

- **Security Events:**
  - Events related to the user
  - Severity levels
  - Event details

- **Access Logs:**
  - API endpoints accessed
  - Request methods
  - Status codes
  - Response times

### Threats Analysis

The `/security-dashboard/threats-analysis` endpoint identifies and analyzes potential security threats:

- **High Severity Threats:**
  - Counts by threat type
  - Trend analysis

- **Suspicious IP Addresses:**
  - IPs with multiple failed login attempts
  - Number of unique accounts targeted
  - Failed attempt counts

- **Password Guessing Detection:**
  - Accounts with multiple failed password attempts
  - Number of unique IPs used for attempts
  - Attempt frequency analysis

- **Threat Summary:**
  - Overall threat level assessment
  - Most targeted accounts
  - Most suspicious IP addresses

## Implementation

The security dashboard is implemented as a dedicated FastAPI router with MongoDB aggregation pipelines for efficient data analysis. All dashboard access is logged through the security logging system for accountability.

## Future Enhancements

Planned enhancements include:

- Real-time alerting for critical security events
- Email notifications for suspicious activities
- Geolocation tracking for login attempts
- Machine learning for anomaly detection
- Customizable dashboard views