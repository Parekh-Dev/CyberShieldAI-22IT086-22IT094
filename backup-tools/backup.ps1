# CyberShield AI - Database Backup Script (PowerShell version)

# Configuration
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$BACKUP_DIR = "./backups/${TIMESTAMP}"
$MONGODB_CONTAINER = "cybershield-mongodb"
$DB_NAME = "cybershield_db"

# Create backup directories
New-Item -ItemType Directory -Force -Path "$BACKUP_DIR/mongodb" | Out-Null
New-Item -ItemType Directory -Force -Path "$BACKUP_DIR/config" | Out-Null

Write-Host "=== CyberShield AI Backup Process ===" -ForegroundColor Green
Write-Host "Starting backup at 03/27/2025 14:23:02" -ForegroundColor Yellow
Write-Host "Backup location: $BACKUP_DIR" -ForegroundColor Yellow

# 1. Database Backup
Write-Host ""
Write-Host "=== Backing up MongoDB database ===" -ForegroundColor Green
docker exec $MONGODB_CONTAINER mongodump --db $DB_NAME --out /data/backup/
docker cp "${MONGODB_CONTAINER}:/data/backup/${DB_NAME}" "${BACKUP_DIR}/mongodb/"
Write-Host "MongoDB backup completed" -ForegroundColor Green

# 2. Configuration Backup
Write-Host ""
Write-Host "=== Backing up configuration files ===" -ForegroundColor Green
# Copy environment files
if (Test-Path ".env") {
    Copy-Item ".env" -Destination "$BACKUP_DIR/config/"
    Write-Host "Backed up .env file" -ForegroundColor Yellow
}

# Copy docker-compose file
if (Test-Path "docker-compose.yml") {
    Copy-Item "docker-compose.yml" -Destination "$BACKUP_DIR/config/"
    Write-Host "Backed up docker-compose.yml" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Backup completed successfully at 03/27/2025 14:23:02" -ForegroundColor Green
Write-Host "=== Backup Summary ===" -ForegroundColor Green
Write-Host "Database: $DB_NAME" -ForegroundColor Yellow
Write-Host "Backup directory: $BACKUP_DIR" -ForegroundColor Yellow
