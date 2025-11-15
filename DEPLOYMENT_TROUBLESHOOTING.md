# Deployment Troubleshooting Guide

## Recent Deployment Failures (Nov 14, 2025)

### Issues Fixed:
1. ✅ **Duplicate route error**: `update_profile()` function name conflict
   - Fixed by renaming `/api/update-profile` handler to `update_client_profile()`
   
2. ✅ **Password reset tokens table**: UNIQUE constraint on email causing failures
   - Fixed by moving UNIQUE constraint from `email` to `token`
   - Added migration to fix existing production tables

### Current Deployment Status:
**Last successful commit**: Awaiting confirmation
**Known issues**: Application exiting with status 1

## Common Render Deployment Errors

### 1. Route/Endpoint Conflicts
**Symptom**: `AssertionError: View function mapping is overwriting an existing endpoint`
**Cause**: Two functions with the same name registered as Flask routes
**Fix**: Rename one of the conflicting functions

**Check for duplicates:**
```bash
grep -n "def update_profile" app.py
grep -n "def client_dashboard" app.py
grep -n "@app.route('/signin'" app.py
```

### 2. Database Table Issues
**Symptom**: `relation "table_name" does not exist`
**Cause**: Table not created in production database
**Fix**: Ensure `init_postgres_db()` runs successfully on startup

**Critical tables:**
- leads (user accounts)
- client_profiles
- password_reset_tokens
- federal_contracts
- supply_contracts
- commercial_opportunities

### 3. Missing Environment Variables
**Symptom**: `KeyError` or unexpected None values
**Required on Render:**
```env
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-password
ADMIN2_SEED_EMAIL=admin2@vacontracts.com
ADMIN2_SEED_USERNAME=admin2
ADMIN2_SEED_PASSWORD=secure-password
ADMIN2_AUTO_PROVISION=true
```

### 4. Import/Dependency Errors
**Symptom**: `ModuleNotFoundError: No module named 'x'`
**Check**: All dependencies in requirements.txt
**Fix**: Ensure requirements.txt is up-to-date

```bash
pip freeze > requirements.txt
```

### 5. Gunicorn Timeout
**Symptom**: Worker timeout errors in logs
**Current timeout**: 120 seconds (gunicorn.conf.py)
**Fix**: Optimize database initialization or increase timeout further

## Admin2 Authentication System

### Current Implementation (app.py):
- **Function**: `ensure_admin2_account()` (line ~303)
- **Features**:
  - Auto-provision if missing
  - Password sync from environment variable
  - Admin privilege elevation
  - Fallback password support
  - Transaction safety with rollback

### Admin2 Credentials:
- **Username**: admin2
- **Email**: admin2@vacontracts.com
- **Password**: Set via `ADMIN2_SEED_PASSWORD` environment variable
- **Auto-provision**: Enabled if `ADMIN2_AUTO_PROVISION=true`

### Emergency Admin Access:
If admin2 login fails:
1. Use emergency route: `/admin-emergency-login?token=<ADMIN_EMERGENCY_TOKEN>`
2. Set `ADMIN_EMERGENCY_TOKEN` in Render environment variables
3. Route automatically provisions admin2 account

## Debugging Render Deployments

### 1. Check Render Logs
```
Dashboard → Your Service → Logs
```
Look for:
- Python/Flask startup errors
- Database connection errors
- Import/module errors
- Route registration errors

### 2. Check Database Connection
Render logs should show:
```
🔧 Initializing database...
📡 Detected PostgreSQL - using init_postgres_db()
✅ PostgreSQL database initialized
```

### 3. Check Route Registration
Search logs for:
```
AssertionError: View function mapping is overwriting
```

### 4. Test Locally
```bash
# Use production environment variables
export DATABASE_URL="your-postgres-url"
python app.py
```

## Quick Fixes

### Reset Database Schema (Use with caution):
```python
# Add to app.py temporarily for one deployment
with app.app_context():
    db.session.execute(text("DROP TABLE IF EXISTS password_reset_tokens CASCADE"))
    db.session.commit()
    init_postgres_db()
```

### Force Admin2 Provisioning:
```python
# Add after database initialization in app.py
with app.app_context():
    ensure_admin2_account(force_password_reset=True)
```

### Clear Failed Transactions:
Already implemented in `client_dashboard` with strategic rollback calls.

## Deployment Checklist

Before each deploy:
- [ ] Run local syntax check: `python -m py_compile app.py`
- [ ] Check for duplicate routes: `grep -n "@app.route" app.py | sort`
- [ ] Check for duplicate function names: `grep -n "^def " app.py | sort`
- [ ] Verify requirements.txt is current
- [ ] Test locally with production DATABASE_URL
- [ ] Check Render environment variables are set

## Contact Information

**Production URL**: https://virginia-contracts-lead-generation.onrender.com
**Repository**: github.com/rayofsundays-boop/virginia-contracts-lead-generation
**Admin Email**: admin2@vacontracts.com

---

*Last Updated: November 14, 2025*
*Recent Fixes: Duplicate route conflict, password reset token migration*
