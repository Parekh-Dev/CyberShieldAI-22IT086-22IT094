# CyberShield AI - Database Restore Script (PowerShell version)

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupDir
)

$MONGODB_CONTAINER = "cybershield-mongodb"
$DB_NAME = "cybershield_db"

# Check if backup directory exists
if (-not (Test-Path "$BackupDir")) {
    Write-Host "Error: Backup directory $BackupDir not found" -ForegroundColor Red
    exit 1
}

Write-Host "=== CyberShield AI Restore Process ===" -ForegroundColor Green
Write-Host "Starting restore from $BackupDir at 03/27/2025 14:23:10" -ForegroundColor Yellow

# Restore MongoDB database
Write-Host ""
Write-Host "=== Restoring MongoDB database ===" -ForegroundColor Green
$DB_BACKUP_DIR = "${BackupDir}/mongodb/${DB_NAME}"

if (-not (Test-Path "$DB_BACKUP_DIR")) {
    Write-Host "Error: Database backup not found in directory" -ForegroundColor Red
    exit 1
}

# Copy backup to container
docker cp "$DB_BACKUP_DIR" "${MONGODB_CONTAINER}:/data/restore"
Write-Host "Copied backup data to container" -ForegroundColor Yellow

# Perform restore
Write-Host "Restoring database..." -ForegroundColor Yellow
docker exec $MONGODB_CONTAINER mongorestore --drop --db $DB_NAME /data/restore/
Write-Host "Database restore completed" -ForegroundColor Green

Write-Host ""
Write-Host "Restore completed successfully at 03/27/2025 14:23:10" -ForegroundColor Green
Write-Host "Please restart your application if necessary" -ForegroundColor Yellow
