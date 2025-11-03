#!/bin/bash
# PayPal Environment Configuration Script
# This script helps you set up PayPal API credentials for payment processing

echo "=================================================="
echo "PayPal Environment Setup for Virginia Contracts"
echo "=================================================="
echo ""
echo "This script will help you configure PayPal credentials."
echo ""

# Check if .env file exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists. Backing up to .env.backup"
    cp .env .env.backup
fi

# Guide user through setup
echo "📝 You'll need the following from PayPal:"
echo "   1. Client ID"
echo "   2. Client Secret"
echo "   3. Monthly Plan ID"
echo "   4. Annual Plan ID"
echo ""
echo "Get these from: https://developer.paypal.com/dashboard/applications/live"
echo ""
read -p "Press Enter when you're ready to continue..."
echo ""

# Get PayPal mode
echo "1️⃣  Select PayPal Mode:"
echo "   [1] sandbox (for testing)"
echo "   [2] live (for production)"
read -p "Enter choice (1 or 2): " mode_choice

if [ "$mode_choice" = "2" ]; then
    PAYPAL_MODE="live"
else
    PAYPAL_MODE="sandbox"
fi

echo "   Selected: $PAYPAL_MODE"
echo ""

# Get Client ID
echo "2️⃣  Enter PayPal Client ID:"
read -p "Client ID: " CLIENT_ID
echo ""

# Get Client Secret
echo "3️⃣  Enter PayPal Client Secret:"
read -p "Client Secret: " CLIENT_SECRET
echo ""

# Get Monthly Plan ID
echo "4️⃣  Enter Monthly Subscription Plan ID:"
echo "   (From PayPal Dashboard > Subscriptions > Plans)"
read -p "Monthly Plan ID: " MONTHLY_PLAN
echo ""

# Get Annual Plan ID
echo "5️⃣  Enter Annual Subscription Plan ID:"
read -p "Annual Plan ID: " ANNUAL_PLAN
echo ""

# Create .env file
echo "💾 Creating .env file..."
cat > .env << EOF
# PayPal Configuration
PAYPAL_MODE=$PAYPAL_MODE
PAYPAL_CLIENT_ID=$CLIENT_ID
PAYPAL_SECRET=$CLIENT_SECRET
PAYPAL_MONTHLY_PLAN_ID=$MONTHLY_PLAN
PAYPAL_ANNUAL_PLAN_ID=$ANNUAL_PLAN

# Database (optional - defaults to leads.db)
# DATABASE_URL=sqlite:///leads.db

# Flask (optional)
# SECRET_KEY=your-secret-key-here
# FLASK_ENV=development
EOF

echo "✅ .env file created!"
echo ""

# Create .env.example for reference
cat > .env.example << EOF
# PayPal Configuration
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=your_client_id_here
PAYPAL_SECRET=your_secret_here
PAYPAL_MONTHLY_PLAN_ID=P-MONTHLY-PLAN-ID
PAYPAL_ANNUAL_PLAN_ID=P-ANNUAL-PLAN-ID

# Database
DATABASE_URL=sqlite:///leads.db

# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
EOF

echo "✅ .env.example created for reference"
echo ""

# Add to .gitignore if not already there
if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    echo "✅ Added .env to .gitignore"
else
    echo "✅ .env already in .gitignore"
fi

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Your credentials have been saved to .env"
echo ""
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "   • .env file contains sensitive credentials"
echo "   • Never commit .env to git"
echo "   • .env is already in .gitignore"
echo "   • Use .env.example as a template for others"
echo ""
echo "📋 Next Steps:"
echo "   1. Install python-dotenv: pip install python-dotenv"
echo "   2. Test credentials: python3 test_payment.py"
echo "   3. Start Flask: flask run"
echo ""
echo "To load variables manually in terminal:"
echo "   source .env  # or"
echo "   export \$(cat .env | xargs)"
echo ""
