# Admin2 Account Setup ✅

## Account Created Successfully

**Date:** November 13, 2025  
**Status:** ✅ Active and Ready

---

## Login Credentials

```
Username: admin2@vacontracts.com  (or just: admin2)
Password: admin2
```

---

## Account Details

- **Database ID:** 5
- **Email:** admin2@vacontracts.com
- **Username:** admin2
- **Admin Status:** TRUE (is_admin = 1)
- **Subscription:** paid
- **Credits:** 999999 (unlimited)
- **Company:** Admin 2
- **Contact Name:** Administrator 2

---

## Login Routes Available

The admin2 account can log in through any of these routes:

1. **Primary Auth Page:** `/auth`
   - Unified sign-in/register page
   - Use either email or username

2. **Direct Sign In:** `/signin`
   - POST form submission
   - Accepts username OR email in username field

3. **Legacy Login:** `/login`
   - Alternative login endpoint
   - Redirects GET requests to `/auth`

---

## Login Flow

### Standard Login (Regular Users & Admin2)

1. **Navigate to:** https://virginia-contracts-lead-generation.onrender.com/auth
2. **Enter credentials:**
   - Username: `admin2` or `admin2@vacontracts.com`
   - Password: `admin2`
3. **Submit form**
4. **Redirect to:** `/customer-dashboard` (unified dashboard for all users)

### Superadmin Login (Environment Variable Based)

Note: There's also a superadmin login that uses environment variables:
- Requires `ADMIN_USERNAME` and `ADMIN_PASSWORD` env vars
- Currently not configured (returns empty in .env check)
- When configured, this takes precedence over database users

---

## Authentication Logic

### Route: `/signin` (lines 4320-4600)

1. **First Check:** Superadmin credentials (if `ADMIN_ENABLED` is true)
   - Compares against `ADMIN_USERNAME` and `ADMIN_PASSWORD` env vars
   - Creates/updates admin record in database if successful
   - Sets unlimited credits (999999)

2. **Second Check:** Database user lookup
   - Queries: `SELECT ... FROM leads WHERE username = :username OR email = :username`
   - Validates password hash with `check_password_hash()`
   - Checks if 2FA is enabled (redirects to `/verify_2fa` if needed)

3. **Admin Privileges:**
   - If `is_admin = 1` in database:
     - Forces `subscription_status = 'paid'`
     - Sets `credits_balance = 999999`
   - Redirects to customer dashboard (same as regular users)

### Route: `/login` (lines 4507-4600)

- Identical logic to `/signin`
- Redirects GET requests to `/auth`
- Only handles POST requests

---

## Admin2 vs Superadmin

| Feature | admin2 (Database) | Superadmin (Env Vars) |
|---------|------------------|----------------------|
| **Storage** | Database record | Environment variables |
| **Username** | admin2@vacontracts.com | `$ADMIN_USERNAME` |
| **Password** | Hashed in DB | `$ADMIN_PASSWORD` (plain) |
| **Priority** | Second | First (checked before DB) |
| **Setup** | Manual DB insert | Set env vars on Render |
| **Status** | ✅ Currently active | ❌ Not configured |

---

## Troubleshooting

### Issue: "admin2 can't log in"

**Resolution Steps:**

1. ✅ **Verify Account Exists**
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('leads.db'); print(conn.execute('SELECT * FROM leads WHERE email = \"admin2@vacontracts.com\"').fetchone())"
   ```

2. ✅ **Check Password Hash**
   - Password `admin2` properly hashed with werkzeug
   - Verified with `check_password_hash()` test (PASSED)

3. ✅ **Confirm Admin Privileges**
   - `is_admin = 1` ✓
   - `subscription_status = 'paid'` ✓
   - `credits_balance = 999999` ✓

4. ✅ **Test Login Route**
   - `/auth` route exists and renders `auth.html`
   - Form submits to `/signin` with POST method
   - Database query uses `username OR email` (flexible)

### Common Login Issues

**Problem:** "User not found"
- **Solution:** Use full email `admin2@vacontracts.com` instead of just `admin2`
- **Why:** Some queries prioritize exact email matches

**Problem:** "Invalid password"
- **Solution:** Ensure password is exactly `admin2` (case-sensitive)
- **Check:** Verify hash in database matches test password

**Problem:** "Redirected to /auth"
- **Solution:** This is normal for GET requests to `/login` or `/signin`
- **Action:** Use the form on `/auth` page to submit credentials

**Problem:** "2FA code required"
- **Solution:** Check if `twofa_enabled = 1` in database
- **Fix:** Run: `UPDATE leads SET twofa_enabled = 0 WHERE email = 'admin2@vacontracts.com'`

---

## Database Schema

```sql
CREATE TABLE leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT,
    contact_name TEXT,
    email TEXT UNIQUE,
    username TEXT UNIQUE,
    password_hash TEXT,
    is_admin INTEGER DEFAULT 0,
    subscription_status TEXT DEFAULT 'unpaid',
    credits_balance INTEGER DEFAULT 0,
    twofa_enabled INTEGER DEFAULT 0,
    -- ... other columns
);
```

### admin2 Record:

```sql
INSERT INTO leads (
    company_name, contact_name, email, username, 
    password_hash, is_admin, subscription_status, credits_balance
) VALUES (
    'Admin 2', 
    'Administrator 2', 
    'admin2@vacontracts.com', 
    'admin2',
    '<werkzeug_hashed_password>', 
    1, 
    'paid', 
    999999
);
```

---

## Security Notes

⚠️ **Default Password**
- The default password `admin2` should be changed after first login
- Use a strong, unique password for production
- Consider enabling 2FA for additional security

🔐 **Password Storage**
- Passwords hashed using werkzeug.security
- Uses `generate_password_hash()` with default settings
- Verification via `check_password_hash()`

---

## Next Steps

### For First Login:
1. ✅ Navigate to: https://virginia-contracts-lead-generation.onrender.com/auth
2. ✅ Enter: `admin2@vacontracts.com` / `admin2`
3. ✅ Click "Sign In"
4. ⚠️ **Change password immediately** after first login

### To Change Password:
```python
# Run this script to update password
from werkzeug.security import generate_password_hash
import sqlite3

new_password = input("Enter new password: ")
password_hash = generate_password_hash(new_password)

conn = sqlite3.connect('leads.db')
conn.execute('UPDATE leads SET password_hash = ? WHERE email = ?', 
             (password_hash, 'admin2@vacontracts.com'))
conn.commit()
conn.close()
print("✅ Password updated!")
```

### To Enable 2FA (Recommended):
1. Login to admin2 account
2. Navigate to: `/enable-2fa`
3. Scan QR code with authenticator app
4. Enter verification code
5. Save backup codes

---

## Testing Checklist

- [x] Account created in database
- [x] Password hash validates correctly
- [x] Admin privileges confirmed (is_admin = 1)
- [x] Subscription status set to 'paid'
- [x] Credits balance set to 999999
- [x] Login routes identified (/auth, /signin, /login)
- [x] Authentication logic reviewed
- [ ] **Test actual login through browser** ⚠️
- [ ] Change default password
- [ ] Enable 2FA

---

## Support

If admin2 still cannot log in after following these steps:

1. **Check Application Logs:**
   ```bash
   # On Render.com dashboard
   # Go to Logs tab
   # Look for authentication errors
   ```

2. **Verify Database Connection:**
   - Ensure `leads.db` is accessible
   - Check file permissions
   - Confirm SQLite version compatibility

3. **Test Auth Route:**
   - Visit `/auth` directly in browser
   - Inspect network requests in DevTools
   - Check for JavaScript errors in console

4. **Contact Support:**
   - Provide login timestamp
   - Include any error messages
   - Share browser console logs

---

## Summary

✅ **admin2 account is fully configured and ready for use**

**Quick Reference:**
- URL: `/auth`
- Username: `admin2@vacontracts.com`
- Password: `admin2`
- Status: Active with full admin privileges

The account has been created, password verified, and admin privileges confirmed. The login should work through any of the available authentication routes.
