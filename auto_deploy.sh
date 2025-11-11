#!/bin/bash

# Auto-commit and deploy script
# Watches for changes and automatically commits/pushes to GitHub

cd "$(dirname "$0")"

echo "🔍 Auto-deploy watcher started..."
echo "📁 Watching directory: $(pwd)"
echo "🚀 Changes will be automatically committed and pushed"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Function to commit and push
deploy() {
    echo ""
    echo "📝 Changes detected at $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Add all changes
    git add .
    
    # Check if there are changes to commit
    if git diff-index --quiet HEAD --; then
        echo "✅ No changes to commit"
    else
        # Commit with timestamp
        git commit -m "Auto-deploy: $(date '+%Y-%m-%d %H:%M:%S')"
        
        # Push to remote
        echo "🚀 Pushing to GitHub..."
        if git push origin main; then
            echo "✅ Successfully deployed!"
        else
            echo "❌ Push failed - check your connection"
        fi
    fi
    echo ""
}

# Install fswatch if not present (macOS)
if ! command -v fswatch &> /dev/null; then
    echo "⚠️  fswatch not found. Install it with: brew install fswatch"
    echo "📝 Falling back to manual deploy mode"
    echo "💡 Run this script again after installing fswatch for auto-watch"
    echo ""
    read -p "Press Enter to deploy current changes and exit..."
    deploy
    exit 0
fi

# Watch for changes (exclude .git, node_modules, __pycache__, etc.)
fswatch -o \
    --exclude=".git" \
    --exclude="node_modules" \
    --exclude="__pycache__" \
    --exclude=".venv" \
    --exclude="*.pyc" \
    --exclude=".DS_Store" \
    --exclude="*.log" \
    --exclude="leads.db" \
    --exclude="leads_backup_*.db" \
    . | while read change; do
    deploy
done
