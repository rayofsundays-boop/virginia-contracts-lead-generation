# How to Fix Environment Variables for PayPal

## Quick Start (Recommended)

### Option 1: Interactive Setup Script
```bash
./setup_paypal_env.sh
```
This script will guide you through setting up all PayPal credentials.

---

## Manual Setup

### Step 1: Get PayPal Credentials

#### For Testing (Sandbox):
1. Go to https://developer.paypal.com/
2. Log in with your PayPal account
3. Go to **Dashboard** → **My Apps & Credentials**
4. Under **Sandbox**, click **Create App**
5. Copy your **Client ID** and **Secret**

#### For Production (Live):
1. Switch to **Live** tab in PayPal Dashboard
2. Create a live app
3. Copy **Client ID** and **Secret**

### Step 2: Create Subscription Plans

1. In PayPal Dashboard, go to **Products** → **Subscriptions**
2. Click **Create Plan**
3. Create two plans:
   - **Monthly**: $29.99/month
   - **Annual**: $287.88/year (20% discount)
4. Copy both **Plan IDs**

### Step 3: Create .env File

Create a file named `.env` in your project root:

```bash
# PayPal Configuration
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=your_client_id_here
PAYPAL_SECRET=your_secret_here
PAYPAL_MONTHLY_PLAN_ID=P-MONTHLY-PLAN-ID
PAYPAL_ANNUAL_PLAN_ID=P-ANNUAL-PLAN-ID

# Optional: Database URL (defaults to leads.db)
DATABASE_URL=sqlite:///leads.db

# Optional: Flask secret key
SECRET_KEY=your-random-secret-key-here
```

### Step 4: Verify Setup

Test your configuration:
```bash
python3 test_payment.py
```

You should see:
```
✅ Client ID: Set
✅ Client Secret: Set
✅ PayPal API connection successful
```

---

## Alternative: Export in Terminal

If you don't want to use a .env file, you can export variables directly:

```bash
# Sandbox (Testing)
export PAYPAL_MODE=sandbox
export PAYPAL_CLIENT_ID='your_client_id'
export PAYPAL_SECRET='your_secret'
export PAYPAL_MONTHLY_PLAN_ID='P-1234567890'
export PAYPAL_ANNUAL_PLAN_ID='P-0987654321'
```

**Note:** These will only last for the current terminal session.

---

## For Production Deployment (Render.com)

### In Render Dashboard:
1. Go to your app → **Environment**
2. Add these variables:
   - `PAYPAL_MODE` = `live`
   - `PAYPAL_CLIENT_ID` = `your_live_client_id`
   - `PAYPAL_SECRET` = `your_live_secret`
   - `PAYPAL_MONTHLY_PLAN_ID` = `P-YOUR-MONTHLY-ID`
   - `PAYPAL_ANNUAL_PLAN_ID` = `P-YOUR-ANNUAL-ID`
3. Save and redeploy

---

## Security Best Practices

### ✅ DO:
- Use `.env` file for local development
- Add `.env` to `.gitignore` (already done)
- Use different credentials for sandbox vs production
- Rotate secrets regularly

### ❌ DON'T:
- Commit `.env` file to git
- Share credentials in chat/email
- Use sandbox credentials in production
- Hardcode secrets in code

---

## Troubleshooting

### Problem: "Client ID not set"
**Solution:** Make sure `.env` file exists and contains `PAYPAL_CLIENT_ID`

### Problem: "401 Unauthorized"
**Solution:** Verify your Client ID and Secret are correct

### Problem: "Module dotenv not found"
**Solution:** Install python-dotenv:
```bash
pip install python-dotenv
```

### Problem: ".env not loading"
**Solution:** Make sure `.env` file is in project root:
```bash
pwd  # Should show: ...Lead Generartion for Cleaning Contracts (VA) ELITE
ls -la .env  # Should exist
```

### Problem: "Plan ID not working"
**Solution:** Double-check Plan IDs in PayPal Dashboard under Subscriptions

---

## Testing Your Setup

### 1. Test Configuration
```bash
python3 test_payment.py
```

### 2. Test Payment Flow
```bash
python3 test_payment_flow.py
```

### 3. Test with Flask
```bash
flask run
# Visit: http://127.0.0.1:5000/subscription
```

---

## What Each Variable Does

| Variable | Purpose | Example |
|----------|---------|---------|
| `PAYPAL_MODE` | Sandbox or live environment | `sandbox` or `live` |
| `PAYPAL_CLIENT_ID` | Your PayPal app's public ID | `AeB3xC...` |
| `PAYPAL_SECRET` | Your PayPal app's secret key | `EPxY2z...` |
| `PAYPAL_MONTHLY_PLAN_ID` | Monthly subscription plan | `P-12345...` |
| `PAYPAL_ANNUAL_PLAN_ID` | Annual subscription plan | `P-67890...` |

---

## Current Status

✅ python-dotenv installed
✅ app.py configured to load .env
✅ .gitignore includes .env
✅ Setup script created
✅ Test scripts ready

⚠️  Need to add: Your actual PayPal credentials

---

## Next Steps

1. Run setup script: `./setup_paypal_env.sh`
2. Or manually create `.env` file
3. Test configuration: `python3 test_payment.py`
4. Start Flask: `flask run`
5. Test payment flow: Visit `/subscription` page

Need help? Check PAYMENT_TEST_RESULTS.md for more details.
