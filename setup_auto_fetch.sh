#!/bin/bash
# Setup cron job for automated daily contract fetching

# Get the absolute path to the project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Python executable (use the one in your environment)
PYTHON_BIN="$(which python3)"

# Cron schedule: Run every day at 3:00 AM EST
CRON_SCHEDULE="0 3 * * *"

# Cron command
CRON_CMD="cd $PROJECT_DIR && $PYTHON_BIN auto_fetch_daily.py >> daily_fetch.log 2>&1"

echo "=================================="
echo "🤖 AUTOMATED DAILY FETCH SETUP"
echo "=================================="
echo ""
echo "Project Directory: $PROJECT_DIR"
echo "Python Binary:     $PYTHON_BIN"
echo "Schedule:          Daily at 3:00 AM EST"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "auto_fetch_daily.py"; then
    echo "⚠️  Cron job already exists!"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "auto_fetch_daily.py"
    echo ""
    read -p "Do you want to replace it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled"
        exit 1
    fi
    
    # Remove old cron job
    crontab -l | grep -v "auto_fetch_daily.py" | crontab -
    echo "✅ Removed old cron job"
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $CRON_CMD") | crontab -

echo ""
echo "✅ Cron job installed successfully!"
echo ""
echo "The system will now automatically:"
echo "  • Fetch new federal contracts from Data.gov daily"
echo "  • Run at 3:00 AM EST every day"
echo "  • Log results to: $PROJECT_DIR/daily_fetch.log"
echo "  • Skip duplicates automatically"
echo ""
echo "To view current cron jobs:"
echo "  crontab -l"
echo ""
echo "To view logs:"
echo "  tail -f $PROJECT_DIR/daily_fetch.log"
echo ""
echo "To test the script manually:"
echo "  cd $PROJECT_DIR"
echo "  python3 auto_fetch_daily.py"
echo ""
echo "=================================="
