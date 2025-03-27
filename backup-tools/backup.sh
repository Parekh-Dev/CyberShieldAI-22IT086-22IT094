#!/bin/bash
# CyberShield AI - Database Backup Script

# Configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/${TIMESTAMP}"
RETENTION_DAYS=30
MONGODB_CONTAINER="cybershield-mongodb"
DB_NAME="cybershield_db"

# Create backup directories
mkdir -p $BACKUP_DIR/mongodb
mkdir -p $BACKUP_DIR/config

echo "=== CyberShield AI Backup Process ==="
echo "Starting backup at $(date)"
echo "Backup location: $BACKUP_DIR"

# 1. Database Backup
echo ""
echo "=== Backing up MongoDB database ==="
docker exec $MONGODB_CONTAINER mongodump --db $DB_NAME --out /data/backup/
docker cp $MONGODB_CONTAINER:/data/backup/$DB_NAME $BACKUP_DIR/mongodb/
echo "MongoDB backup completed"

# 2. Configuration Backup
echo ""
echo "=== Backing up configuration files ==="
# Copy environment files
if [ -f ".env" ]; then
    cp .env $BACKUP_DIR/config/
    echo "Backed up .env file"
fi

# Copy docker-compose file
if [ -f "docker-compose.yml" ]; then
    cp docker-compose.yml $BACKUP_DIR/config/
    echo "Backed up docker-compose.yml"
fi

# 3. Compress backup
echo ""
echo "=== Compressing backup ==="
cd backups
tar -czf ${TIMESTAMP}.tar.gz ${TIMESTAMP}/
echo "Created compressed archive: ${TIMESTAMP}.tar.gz"

# 4. Clean old backups
echo ""
echo "=== Cleaning old backups ==="
find . -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
echo "Removed backups older than $RETENTION_DAYS days"

echo ""
echo "Backup completed successfully at $(date)"
echo "=== Backup Summary ==="
echo "Database: $DB_NAME"
echo "Backup archive: backups/${TIMESTAMP}.tar.gz"
echo "Retention policy: $RETENTION_DAYS days"