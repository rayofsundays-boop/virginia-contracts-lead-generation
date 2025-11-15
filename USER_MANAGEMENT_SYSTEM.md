# User Management System Documentation

## Overview
Comprehensive user management system with dedicated `users` table, role-based access control, session tracking, and activity logging.

---

## Database Tables

### 1. **users** (Main User Accounts)

Primary table for user authentication and profile management.

#### Key Fields:
- **Authentication**: `username`, `email`, `password_hash`
- **Profile**: `first_name`, `last_name`, `full_name`, `phone`, `company_name`
- **Status**: `is_active`, `is_verified`, `is_admin`, `is_superuser`, `is_deleted`
- **Subscription**: `subscription_status`, `subscription_tier`, `credits_balance`
- **Security**: `twofa_enabled`, `twofa_secret`, `failed_login_attempts`, `account_locked_until`
- **Tokens**: `password_reset_token`, `email_verification_token`
- **Preferences**: `email_notifications`, `sms_notifications`, `timezone`, `language`
- **Timestamps**: `created_at`, `updated_at`, `deleted_at`, `last_login`

#### Subscription Tiers:
- `free` - Free tier (3 credits)
- `beta` - Beta tester
- `premium` - Paid subscription
- `enterprise` - Enterprise plan

### 2. **user_roles** (Role-Based Access Control)

Manage user permissions and roles.

#### Fields:
- `user_id` - Foreign key to users table
- `role_name` - Role identifier (admin, moderator, premium_user, etc.)
- `granted_at` - When role was assigned
- `granted_by` - User ID who granted the role
- `expires_at` - Optional expiration date
- `is_active` - Whether role is currently active

### 3. **user_sessions** (Session Tracking)

Track active user sessions for security and analytics.

#### Fields:
- `user_id` - Foreign key to users table
- `session_token` - Unique session identifier
- `ip_address` - Login IP address
- `user_agent` - Browser/client information
- `created_at` - Session start time
- `last_activity` - Last activity timestamp
- `expires_at` - Session expiration
- `is_active` - Whether session is active

### 4. **user_activity_log** (Audit Trail)

Comprehensive activity logging for security and analytics.

#### Fields:
- `user_id` - Foreign key to users table
- `activity_type` - Type of activity (login, logout, profile_update, etc.)
- `activity_description` - Human-readable description
- `ip_address` - IP address
- `user_agent` - Browser/client info
- `metadata` - Additional JSON data
- `created_at` - Activity timestamp

---

## Setup & Installation

### 1. Create Tables

```bash
python create_users_table.py
```

This creates:
- ✅ `users` table with 42 fields
- ✅ 5 indexes for performance
- ✅ `user_roles` table
- ✅ `user_sessions` table
- ✅ `user_activity_log` table

### 2. Migrate Existing Users (Optional)

If you have users in the `leads` table:

```bash
python migrate_leads_to_users.py
```

This will:
- Copy all user accounts from `leads` to `users`
- Preserve passwords, preferences, and subscription data
- Skip duplicates automatically
- Maintain original creation dates

---

## Usage Examples

### Using UserManager Helper Class

```python
from user_manager import UserManager, log_user_activity

# Create a new user
user_id = UserManager.create_user(
    username='johndoe',
    email='john@example.com',
    password='SecurePassword123!',
    first_name='John',
    last_name='Doe',
    company_name='Acme Corp',
    subscription_tier='premium'
)

# Authenticate user
user = UserManager.authenticate('johndoe', 'SecurePassword123!')
if user:
    print(f"Welcome {user['full_name']}!")
    
    # Log activity
    log_user_activity(
        user_id=user['id'],
        activity_type='login',
        description='User logged in via web',
        ip_address='192.168.1.1'
    )

# Get user by email
user = UserManager.get_user_by_email('john@example.com')

# Update user
UserManager.update_user(
    user_id=user['id'],
    phone='555-1234',
    company_name='New Company Inc'
)

# Change password
UserManager.change_password(user['id'], 'NewPassword456!')

# List all active premium users
premium_users = UserManager.list_users(
    is_active=True,
    subscription_tier='premium',
    limit=50
)
```

### Direct SQL Queries

```python
from sqlalchemy import text
from app import db

# Find user
user = db.session.execute(text("""
    SELECT * FROM users 
    WHERE email = :email AND is_active = 1
"""), {'email': 'user@example.com'}).fetchone()

# Update subscription
db.session.execute(text("""
    UPDATE users 
    SET subscription_tier = 'premium',
        credits_balance = 100,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = :user_id
"""), {'user_id': user_id})
db.session.commit()

# Get user activity log
activities = db.session.execute(text("""
    SELECT * FROM user_activity_log
    WHERE user_id = :user_id
    ORDER BY created_at DESC
    LIMIT 20
"""), {'user_id': user_id}).fetchall()
```

---

## Security Features

### 1. **Account Locking**
- Locks account after 5 failed login attempts
- 30-minute lockout period
- Automatic unlock after timeout

### 2. **Password Hashing**
- Uses Werkzeug's `generate_password_hash`
- Industry-standard bcrypt/pbkdf2 algorithms
- Never stores plain text passwords

### 3. **Two-Factor Authentication**
- `twofa_enabled` flag
- `twofa_secret` stores TOTP secret
- Compatible with Google Authenticator, Authy

### 4. **Password Reset Tokens**
- Secure token generation
- Expiration tracking
- One-time use validation

### 5. **Session Management**
- Track all active sessions
- IP address logging
- Automatic session expiration
- Device tracking via user agent

### 6. **Activity Logging**
- Complete audit trail
- IP address tracking
- Metadata support for context
- Compliance-ready

---

## Integration with Existing App

### Update Authentication Routes

Replace `leads` table queries with `users` table:

**Before:**
```python
result = db.session.execute(text("""
    SELECT * FROM leads WHERE email = :email
"""), {'email': email}).fetchone()
```

**After:**
```python
from user_manager import UserManager

user = UserManager.get_user_by_email(email)
# or
user = UserManager.authenticate(email, password)
```

### Update Session Management

**Before:**
```python
session['user_id'] = lead_id
```

**After:**
```python
user = UserManager.authenticate(identifier, password)
if user:
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['email'] = user['email']
    session['is_admin'] = user['is_admin']
    
    # Log the login
    log_user_activity(
        user_id=user['id'],
        activity_type='login',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
```

---

## API Endpoints (Recommended)

### User Management Routes

```python
@app.route('/api/users', methods=['GET'])
@login_required
@admin_required
def list_users():
    """List all users (admin only)"""
    users = UserManager.list_users(limit=100)
    return jsonify({'users': users})

@app.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """Get user profile"""
    if session['user_id'] != user_id and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = UserManager.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Remove sensitive fields
    user.pop('password_hash', None)
    user.pop('twofa_secret', None)
    
    return jsonify({'user': user})

@app.route('/api/users/<int:user_id>', methods=['PATCH'])
@login_required
def update_user_profile(user_id):
    """Update user profile"""
    if session['user_id'] != user_id and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    allowed_fields = ['first_name', 'last_name', 'phone', 'company_name', 
                     'email_notifications', 'sms_notifications', 'timezone']
    
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    
    if UserManager.update_user(user_id, **updates):
        log_user_activity(user_id, 'profile_update', f'Updated: {", ".join(updates.keys())}')
        return jsonify({'success': True})
    
    return jsonify({'error': 'Update failed'}), 500
```

---

## Migration Checklist

- [ ] Run `create_users_table.py`
- [ ] Run `migrate_leads_to_users.py`
- [ ] Update authentication routes to use `users` table
- [ ] Update session management
- [ ] Test login/logout flow
- [ ] Test password reset
- [ ] Test user profile updates
- [ ] Add activity logging to key actions
- [ ] Consider keeping `leads` for non-user lead tracking
- [ ] Update admin dashboard to show `users` table
- [ ] Deploy to production

---

## Files Created

1. **create_users_table.py** - Table creation script
2. **migrate_leads_to_users.py** - Data migration script
3. **user_manager.py** - Helper utilities
4. **USER_MANAGEMENT_SYSTEM.md** - This documentation

---

## Benefits Over `leads` Table

| Feature | leads Table | users Table |
|---------|------------|-------------|
| Purpose | Lead management | User authentication |
| Structure | Mixed purpose | Dedicated user mgmt |
| Security | Basic | Advanced (lockout, 2FA) |
| Sessions | None | Full tracking |
| Activity Log | Limited | Comprehensive |
| Roles | Single flag | RBAC system |
| Soft Delete | No | Yes |
| Audit Trail | No | Yes |
| Scalability | Limited | Enterprise-ready |

---

## Next Steps

1. **Test locally**: Verify all functionality works
2. **Update production**: Run scripts on Render
3. **Monitor**: Check logs for any migration issues
4. **Optimize**: Add additional indexes if needed
5. **Enhance**: Add more roles, permissions as needed

For questions or issues, check the migration logs or activity log table.
