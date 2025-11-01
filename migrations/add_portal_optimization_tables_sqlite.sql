-- Portal Optimization Tables for SQLite
-- Add tables for saved searches, alerts, user preferences, activity tracking, etc.

-- User preferences and settings
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL UNIQUE,
    dashboard_layout TEXT DEFAULT 'default',
    favorite_lead_types TEXT, -- JSON array of lead types
    preferred_locations TEXT, -- JSON array of cities
    notification_enabled INTEGER DEFAULT 1,
    email_alerts_enabled INTEGER DEFAULT 1,
    push_notifications_enabled INTEGER DEFAULT 0,
    theme TEXT DEFAULT 'light',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Saved searches
CREATE TABLE IF NOT EXISTS saved_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    search_name TEXT NOT NULL,
    search_filters TEXT NOT NULL, -- Store filter criteria as JSON
    alert_enabled INTEGER DEFAULT 0,
    alert_frequency TEXT DEFAULT 'daily', -- instant, daily, weekly
    last_alerted DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User activity tracking
CREATE TABLE IF NOT EXISTS user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    activity_type TEXT NOT NULL, -- viewed_lead, saved_lead, applied, searched
    lead_type TEXT,
    lead_id INTEGER,
    details TEXT, -- JSON for additional context
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Saved/bookmarked leads
CREATE TABLE IF NOT EXISTS saved_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    lead_type TEXT NOT NULL, -- contract, supply_contract, commercial, etc.
    lead_id INTEGER NOT NULL,
    notes TEXT,
    reminder_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_email, lead_type, lead_id)
);

-- Lead comparisons
CREATE TABLE IF NOT EXISTS lead_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    comparison_name TEXT,
    lead_ids TEXT NOT NULL, -- JSON array of {type, id} objects
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    notification_type TEXT NOT NULL, -- new_lead, saved_search_alert, system
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    link_url TEXT,
    is_read INTEGER DEFAULT 0,
    read_at DATETIME,
    priority TEXT DEFAULT 'normal', -- low, normal, high
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User onboarding progress
CREATE TABLE IF NOT EXISTS user_onboarding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL UNIQUE,
    completed_profile INTEGER DEFAULT 0,
    completed_preferences INTEGER DEFAULT 0,
    completed_first_search INTEGER DEFAULT 0,
    completed_first_save INTEGER DEFAULT 0,
    completed_tour INTEGER DEFAULT 0,
    skipped INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Dashboard cache
CREATE TABLE IF NOT EXISTS dashboard_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT NOT NULL UNIQUE,
    cache_value TEXT NOT NULL, -- JSON data
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_user_prefs_email ON user_preferences(user_email);
CREATE INDEX IF NOT EXISTS idx_saved_searches_email ON saved_searches(user_email);
CREATE INDEX IF NOT EXISTS idx_user_activity_email ON user_activity(user_email);
CREATE INDEX IF NOT EXISTS idx_user_activity_created ON user_activity(created_at);
CREATE INDEX IF NOT EXISTS idx_saved_leads_email ON saved_leads(user_email);
CREATE INDEX IF NOT EXISTS idx_notifications_email_read ON notifications(user_email, is_read);
CREATE INDEX IF NOT EXISTS idx_dashboard_cache_key ON dashboard_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_dashboard_cache_expires ON dashboard_cache(expires_at);
