# Admin2 Login Fix - Render Configuration Required

## Problem
The admin2 account exists locally but not in production, or has the wrong password.

## Solution Deployed ✅
The app now automatically provisions/updates admin2 on every startup with `force_password_reset=True`.

## ACTION REQUIRED: Set Render Environment Variables

**You MUST add these environment variables to your Render service:**

1. Go to: https://dashboard.render.com/
2. Select your service: `virginia-contracts-lead-generation`
3. Click **"Environment"** in the left sidebar
4. Add these variables:

```
ADMIN2_SEED_USERNAME=admin2
ADMIN2_SEED_EMAIL=admin2@vacontracts.com
ADMIN2_SEED_PASSWORD=Admin2!Secure123
ADMIN2_AUTO_PROVISION=true
```

5. Click **"Save Changes"**
6. Wait for the service to restart (automatic)

## Login Credentials

**Production:**
- URL: https://virginia-contracts-lead-generation.onrender.com/signin
- Username: admin2
- Password: Admin2!Secure123

---
Last Updated: November 14, 2025
