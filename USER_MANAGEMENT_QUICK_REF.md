# User Management System - Quick Reference

## 🚀 Quick Start

### Create Tables
```bash
python create_users_table.py
```

### Migrate Existing Users
```bash
python migrate_leads_to_users.py
```

---

## 📊 Tables Created

| Table | Purpose | Records |
|-------|---------|---------|
| `users` | User accounts & auth | Your users |
| `user_roles` | Role-based permissions | RBAC |
| `user_sessions` | Active sessions | Security |
| `user_activity_log` | Audit trail | Compliance |

---

## 💻 Code Examples

### Create User
```python
from user_manager import UserManager

user_id = UserManager.create_user(
    username='john',
    email='john@example.com',
    password='SecurePass123!',
    first_name='John',
    company_name='Acme Corp'
)
```

### Authenticate
```python
user = UserManager.authenticate('john@example.com', 'SecurePass123!')
if user:
    session['user_id'] = user['id']
```

### Get User
```python
user = UserManager.get_user_by_email('john@example.com')
user = UserManager.get_user_by_id(123)
```

### Update User
```python
UserManager.update_user(
    user_id=123,
    phone='555-1234',
    company_name='New Corp'
)
```

### Change Password
```python
UserManager.change_password(user_id, 'NewPassword456!')
```

### List Users
```python
users = UserManager.list_users(
    is_active=True,
    subscription_tier='premium',
    limit=50
)
```

### Log Activity
```python
from user_manager import log_user_activity

log_user_activity(
    user_id=123,
    activity_type='login',
    description='User logged in',
    ip_address='192.168.1.1'
)
```

---

## 🔐 Security Features

✅ **Password Hashing** - Werkzeug bcrypt  
✅ **Account Locking** - 5 failed attempts = 30min lock  
✅ **2FA Support** - TOTP compatible  
✅ **Session Tracking** - IP & device logging  
✅ **Activity Audit** - Complete trail  
✅ **Password Reset** - Secure tokens  
✅ **Soft Delete** - Data retention  

---

## 🗂️ User Fields

### Authentication
- `username`, `email`, `password_hash`

### Profile
- `first_name`, `last_name`, `full_name`
- `phone`, `company_name`

### Status Flags
- `is_active`, `is_verified`, `is_admin`, `is_superuser`

### Subscription
- `subscription_status`: free/paid
- `subscription_tier`: free/beta/premium/enterprise
- `credits_balance`, `credits_used`

### Security
- `twofa_enabled`, `twofa_secret`
- `failed_login_attempts`, `account_locked_until`
- `password_reset_token`, `email_verification_token`

### Timestamps
- `created_at`, `updated_at`, `deleted_at`, `last_login`

---

## 📝 Common Queries

### Find Active Users
```sql
SELECT * FROM users 
WHERE is_active = 1 AND is_deleted = 0
ORDER BY created_at DESC;
```

### Premium Subscribers
```sql
SELECT * FROM users 
WHERE subscription_tier = 'premium'
AND is_active = 1;
```

### Recent Activity
```sql
SELECT u.username, u.email, a.*
FROM user_activity_log a
JOIN users u ON a.user_id = u.id
WHERE a.created_at > datetime('now', '-7 days')
ORDER BY a.created_at DESC;
```

### Failed Login Attempts
```sql
SELECT username, email, failed_login_attempts, account_locked_until
FROM users
WHERE failed_login_attempts > 0
ORDER BY failed_login_attempts DESC;
```

---

## 🎯 Integration Steps

1. ✅ Run `create_users_table.py`
2. ✅ Run `migrate_leads_to_users.py`
3. ⬜ Update `/signin` route to use `UserManager`
4. ⬜ Update `/register` route
5. ⬜ Add activity logging to key actions
6. ⬜ Test authentication flow
7. ⬜ Deploy to production

---

## 📚 Files

- `create_users_table.py` - Setup script
- `migrate_leads_to_users.py` - Migration
- `user_manager.py` - Helper functions
- `USER_MANAGEMENT_SYSTEM.md` - Full docs
- `USER_MANAGEMENT_QUICK_REF.md` - This file

---

## 🆘 Troubleshooting

**Table doesn't exist?**
```bash
python create_users_table.py
```

**Migration failed?**
```bash
# Check leads table
sqlite3 db.sqlite3 "SELECT COUNT(*) FROM leads WHERE username IS NOT NULL;"

# Re-run migration
python migrate_leads_to_users.py
```

**Password not working?**
```python
from werkzeug.security import generate_password_hash
new_hash = generate_password_hash('YourPassword123!')
# Update user's password_hash
```

---

## 🎉 Success Indicators

After setup, you should see:
- ✅ `users` table with 42 columns
- ✅ 5 indexes created
- ✅ 3 supporting tables (roles, sessions, activity)
- ✅ All existing users migrated
- ✅ Authentication working

Run test:
```bash
python -c "from user_manager import UserManager; print(UserManager.list_users())"
```
