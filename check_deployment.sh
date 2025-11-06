#!/bin/bash
# Deployment Status Checker
# Checks if the latest fixes are deployed to Render

echo "🔍 Checking deployment status..."
echo ""

# Check homepage
echo "1️⃣ Homepage:"
HOMEPAGE=$(curl -s -o /dev/null -w "%{http_code}" https://virginia-contracts-lead-generation.onrender.com/)
if [ "$HOMEPAGE" = "200" ]; then
    echo "   ✅ HTTP $HOMEPAGE - Homepage is live"
else
    echo "   ❌ HTTP $HOMEPAGE - Homepage issue"
fi

# Check local procurement
echo ""
echo "2️⃣ Local Procurement:"
LOCAL=$(curl -s -o /dev/null -w "%{http_code}" https://virginia-contracts-lead-generation.onrender.com/local-procurement)
if [ "$LOCAL" = "200" ]; then
    echo "   ✅ HTTP $LOCAL - Local procurement is live"
else
    echo "   ❌ HTTP $LOCAL - Local procurement issue"
fi

# Check URL Manager (requires auth, expect redirect)
echo ""
echo "3️⃣ URL Manager:"
URLMGR=$(curl -s -o /dev/null -w "%{http_code}" https://virginia-contracts-lead-generation.onrender.com/admin/url-manager)
if [ "$URLMGR" = "302" ] || [ "$URLMGR" = "200" ]; then
    echo "   ✅ HTTP $URLMGR - URL Manager route exists"
else
    echo "   ❌ HTTP $URLMGR - URL Manager not found"
fi

# Check admin panel (requires auth, expect redirect)
echo ""
echo "4️⃣ Admin Panel:"
ADMIN=$(curl -s -o /dev/null -w "%{http_code}" https://virginia-contracts-lead-generation.onrender.com/admin-enhanced)
if [ "$ADMIN" = "302" ] || [ "$ADMIN" = "200" ]; then
    echo "   ✅ HTTP $ADMIN - Admin panel route exists"
else
    echo "   ❌ HTTP $ADMIN - Admin panel issue"
fi

# Check git status
echo ""
echo "5️⃣ Local Git Status:"
cd "/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE"
LATEST=$(git log --oneline -1)
echo "   Latest commit: $LATEST"

# Get deployed commit from Render
echo ""
echo "6️⃣ Deployed Version:"
DEPLOY_TIME=$(curl -s https://virginia-contracts-lead-generation.onrender.com/ | grep -o "<!-- Built: [^>]*" | head -1)
if [ -n "$DEPLOY_TIME" ]; then
    echo "   $DEPLOY_TIME"
else
    echo "   ℹ️  Deployment timestamp not available"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Summary:"
echo "   • Latest local commit: f702a48 (division fix)"
echo "   • Previous commit: 0d7f5a9 (URL manager)"
echo ""
echo "⏰ If you're seeing the old error, Render is still deploying."
echo "   Typical deployment time: 5-8 minutes"
echo "   Started: ~2-3 minutes ago"
echo "   ETA: ~2-5 minutes remaining"
echo ""
echo "🔄 To check again in 2 minutes:"
echo "   bash check_deployment.sh"
echo ""
