# Database Migration Guide - Production

## Overview
Two migration scripts have been created to fix remaining database issues:

1. **`add_missing_tables.py`** - Creates 3 missing tables
2. **`add_website_url_column.py`** - Adds missing column to commercial_opportunities

## Tables Created

### 1. user_activity
Tracks user actions and behavior for analytics.

**Columns:**
- `id` - Primary key
- `user_id` - Foreign key to leads table
- `activity_type` - Type of action (login, view_lead, save_lead, etc.)
- `activity_description` - Detailed description
- `ip_address` - User's IP address
- `user_agent` - Browser/device info
- `created_at` - Timestamp

**Use Cases:**
- User engagement tracking
- Audit logs
- Behavior analytics

### 2. user_preferences
Stores user settings and customization options.

**Columns:**
- `id` - Primary key
- `user_id` - Foreign key to leads table (UNIQUE)
- `email_notifications` - Boolean (default: true)
- `sms_notifications` - Boolean (default: false)
- `notification_frequency` - daily/weekly/monthly
- `preferred_locations` - JSON or comma-separated
- `preferred_contract_types` - JSON or comma-separated
- `dark_mode` - Boolean (default: false)
- `created_at` - Timestamp
- `updated_at` - Timestamp

**Use Cases:**
- Personalized experience
- Notification preferences
- Location/contract type filters

### 3. notifications
In-app notification system for user alerts.

**Columns:**
- `id` - Primary key
- `user_id` - Foreign key to leads table
- `notification_type` - Type (new_lead, contract_update, etc.)
- `title` - Notification headline
- `message` - Full notification text
- `link` - URL to related page
- `is_read` - Boolean (default: false)
- `priority` - normal/high/urgent
- `created_at` - Timestamp
- `read_at` - Timestamp when marked as read

**Use Cases:**
- Real-time alerts for new leads
- System announcements
- Contract status updates

### 4. website_url Column
Added to `commercial_opportunities` table.

**Column:**
- `website_url TEXT` - Company website or lead source URL

**Fixes:**
- SELECT query failures on commercial leads page
- Display issues with commercial opportunities

## Running Migrations on Production

### For PostgreSQL on Render:

**Option 1: Via Render Dashboard**
1. Go to your database in Render dashboard
2. Click "Connect" → "External Connection"
3. Use psql command provided
4. Run the SQL manually (see PostgreSQL section below)

**Option 2: Via Python Script (Recommended)**
```bash
# SSH into your Render instance or use their shell
python add_missing_tables.py
python add_website_url_column.py
```

### PostgreSQL Equivalent SQL

If running manually via psql:

```sql
-- Create user_activity table
CREATE TABLE IF NOT EXISTS user_activity (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    activity_description TEXT,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_created_at ON user_activity(created_at);

-- Create user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    email_notifications BOOLEAN DEFAULT TRUE,
    sms_notifications BOOLEAN DEFAULT FALSE,
    notification_frequency VARCHAR(20) DEFAULT 'daily',
    preferred_locations TEXT,
    preferred_contract_types TEXT,
    dark_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    link TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    priority VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);

-- Add website_url column to commercial_opportunities
ALTER TABLE commercial_opportunities 
ADD COLUMN IF NOT EXISTS website_url TEXT;
```

## Verification

After running migrations, verify with:

```sql
-- Check if tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('user_activity', 'user_preferences', 'notifications');

-- Check commercial_opportunities columns
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'commercial_opportunities' 
AND column_name = 'website_url';

-- Count rows (should be 0 for new tables)
SELECT 
    (SELECT COUNT(*) FROM user_activity) as user_activity_count,
    (SELECT COUNT(*) FROM user_preferences) as user_preferences_count,
    (SELECT COUNT(*) FROM notifications) as notifications_count;
```

## Testing After Migration

1. **Check Logs** - Verify no more "table does not exist" errors
2. **Test Commercial Leads** - Visit `/commercial-leads` page
3. **Test Dashboard** - Verify `/customer-dashboard` loads properly
4. **Check Admin Panel** - Ensure no SQL errors in admin section

## Rollback (If Needed)

```sql
DROP TABLE IF EXISTS user_activity CASCADE;
DROP TABLE IF EXISTS user_preferences CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;

ALTER TABLE commercial_opportunities DROP COLUMN IF EXISTS website_url;
```

## Status Tracking

- ✅ Local SQLite migration tested successfully
- ✅ Scripts committed to repository
- ✅ Pushed to GitHub
- ⏳ **NEXT:** Run migrations on production PostgreSQL database

## Expected Impact

**After Migration:**
- ✅ No more "relation does not exist" errors in logs
- ✅ Commercial leads page displays properly
- ✅ User activity tracking enabled (foundation for analytics)
- ✅ User preferences system ready (foundation for personalization)
- ✅ Notification system ready (foundation for alerts)

**Database Growth:**
- +3 new tables (empty initially)
- +1 new column in existing table
- +4 performance indexes
- Minimal storage impact until features are utilized
