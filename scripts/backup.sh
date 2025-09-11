#!/usr/bin/env bash
set -euo pipefail

echo "💾 Creating project backup..."

# Create backup directory with timestamp
BACKUP_DIR="backups/backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📁 Backup directory: $BACKUP_DIR"

# Backup SQLite database if it exists
if [ -f "db.sqlite3" ]; then
    echo "🗄️ Backing up SQLite database..."
    cp db.sqlite3 "$BACKUP_DIR/"
    echo "✅ Database backed up"
else
    echo "ℹ️  No SQLite database found"
fi

# Backup media files if they exist
if [ -d "media" ]; then
    echo "📸 Backing up media files..."
    cp -r media "$BACKUP_DIR/"
    echo "✅ Media files backed up"
else
    echo "ℹ️  No media directory found"
fi

# Backup static files if they exist
if [ -d "staticfiles" ]; then
    echo "📄 Backing up static files..."
    cp -r staticfiles "$BACKUP_DIR/"
    echo "✅ Static files backed up"
else
    echo "ℹ️  No static files directory found"
fi

# Backup environment configuration
if [ -f ".env" ]; then
    echo "⚙️ Backing up environment configuration..."
    cp .env "$BACKUP_DIR/env.backup"
    echo "✅ Environment configuration backed up"
else
    echo "ℹ️  No .env file found"
fi

# Create a summary file
cat > "$BACKUP_DIR/backup-info.txt" << EOF
GitDM Project Backup
==================

Backup Date: $(date)
Backup Directory: $BACKUP_DIR
Hostname: $(hostname)
User: $(whoami)

Contents:
$(ls -la "$BACKUP_DIR")

Git Information:
Branch: $(git branch --show-current 2>/dev/null || echo "Not a git repository")
Commit: $(git rev-parse HEAD 2>/dev/null || echo "Not a git repository")

Python Version: $(python --version 2>/dev/null || echo "Python not available")
Django Version: $(python -c "import django; print(django.get_version())" 2>/dev/null || echo "Django not available")
Node Version: $(node --version 2>/dev/null || echo "Node.js not available")

EOF

# Create archive
ARCHIVE_NAME="gitdm-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
echo "📦 Creating archive: $ARCHIVE_NAME"
tar -czf "$ARCHIVE_NAME" -C backups "$(basename "$BACKUP_DIR")"

echo ""
echo "✅ Backup complete!"
echo "📦 Archive: $ARCHIVE_NAME"
echo "📁 Directory: $BACKUP_DIR"
echo ""
echo "💡 To restore from this backup:"
echo "   tar -xzf $ARCHIVE_NAME"
echo "   cp $BACKUP_DIR/db.sqlite3 ./"
echo "   cp $BACKUP_DIR/env.backup .env"

# Clean up old backups (keep last 5)
echo "🧹 Cleaning up old backups..."
ls -t backups/backup-* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
ls -t gitdm-backup-*.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
echo "✅ Old backups cleaned up"