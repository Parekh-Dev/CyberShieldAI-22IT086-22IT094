#!/bin/bash
# CyberShield AI - Database Restore Script

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Error: No backup file specified"
    echo "Usage: $0 <backup_archive.tar.gz>"
    exit 1
fi

BACKUP_ARCHIVE="$1"
MONGODB_CONTAINER="cybershield-mongodb"
DB_NAME="cybershield_db"
RESTORE_DIR="./restore_temp"

# Check if backup file exists
if [ ! -f "$BACKUP_ARCHIVE" ]; then
    echo "Error: Backup file $BACKUP_ARCHIVE not found"
    exit 1
fi

echo "=== CyberShield AI Restore Process ==="
echo "Starting restore from $BACKUP_ARCHIVE at $(date)"

# 1. Extract backup archive
echo ""
echo "=== Extracting backup archive ==="
mkdir -p $RESTORE_DIR
tar -xzf $BACKUP_ARCHIVE -C $RESTORE_DIR
EXTRACTED_DIR=$(ls -d $RESTORE_DIR/*)
echo "Extracted to $EXTRACTED_DIR"

# 2. Restore MongoDB database
echo ""
echo "=== Restoring MongoDB database ==="
DB_BACKUP_DIR="$EXTRACTED_DIR/mongodb/$DB_NAME"

if [ ! -d "$DB_BACKUP_DIR" ]; then
    echo "Error: Database backup not found in archive"
    exit 1
fi

# Copy backup to container
docker cp $DB_BACKUP_DIR $MONGODB_CONTAINER:/data/restore/
echo "Copied backup data to container"

# Perform restore
echo "Restoring database..."
docker exec $MONGODB_CONTAINER mongorestore --drop --db $DB_NAME /data/restore/
echo "Database restore completed"

# 3. Restore configuration if needed
echo ""
echo "=== Configuration files ==="
echo "Configuration files available at: $EXTRACTED_DIR/config/"
echo "Review these files before overwriting your current configuration"

# 4. Clean up
echo ""
echo "=== Cleaning up ==="
rm -rf $RESTORE_DIR
echo "Removed temporary files"

echo ""
echo "Restore completed successfully at $(date)"
echo "Please restart your application if necessary"