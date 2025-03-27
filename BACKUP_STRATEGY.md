# Backup and Recovery Strategy

## Overview
CyberShield AI implements a comprehensive backup and recovery system to ensure data integrity and business continuity.

## Backup Components
1. **Database**: Complete MongoDB database dumps
2. **Configuration**: Environment and Docker configuration files
3. **Compression**: Backups are compressed to save space

## Implementation

### Backup Script
The system includes a fully functional backup script located at `backup-tools/backup.sh` that:
- Creates timestamped backups
- Dumps MongoDB data
- Backs up configuration files
- Compresses backups into archives
- Implements a 30-day retention policy

### Restore Capability
The restore script at `backup-tools/restore.sh` allows for:
- Complete database restoration
- Recovery of configuration files
- Verification of restored data

## Execution Instructions

### On Linux/Mac
```bash
# Make scripts executable
chmod +x backup-tools/*.sh

# Run backup
./backup-tools/backup.sh

# Restore from backup
./backup-tools/restore.sh backups/20240327_120000.tar.gz

### On Windows

# Run backup using batch file
backup-tools\backup.bat

# For restore, use WSL
wsl bash ./backup-tools/restore.sh backups/20240327_120000.tar.gz

# PowerShell alternative (for systems without WSL)
./backup-tools/backup.ps1

# View the latest backup
$latest_backup = (Get-ChildItem -Path ./backups -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
dir $latest_backup

# Restore from backup with PowerShell
./backup-tools/restore.ps1 -BackupDir $latest_backup

### MongoDB Test Commands

# Create test data in MongoDB
docker exec -it cybershield-mongodb mongosh --eval "use cybershield_db; db.backup_demo.insertOne({name: 'Test Data', timestamp: new Date(), value: 'Original value before backup'}); db.backup_demo.find();"

# Modify data (simulate data loss)
docker exec -it cybershield-mongodb mongosh --eval "use cybershield_db; db.backup_demo.updateOne({name: 'Test Data'}, {\$set: {value: 'CHANGED VALUE - we need to restore!'}}); db.backup_demo.find();"

# Verify the restore
docker exec -it cybershield-mongodb mongosh --eval "use cybershield_db; db.backup_demo.find();"


