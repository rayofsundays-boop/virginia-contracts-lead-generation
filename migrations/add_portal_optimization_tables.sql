-- Portal Optimization Tables
-- Add tables for saved searches, alerts, user preferences, activity tracking, etc.

-- User preferences and settings
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_email TEXT NOT NULL,
    dashboard_layout TEXT DEFAULT 'default',
    favorite_lead_types TEXT[], -- Array of lead types
    preferred_locations TEXT[], -- Array of cities
    notification_enabled BOOLEAN DEFAULT TRUE,
    email_alerts_enabled BOOLEAN DEFAULT TRUE,
    push_notifications_enabled BOOLEAN DEFAULT FALSE,
    theme TEXT DEFAULT 'light',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_email)
);

-- Saved searches
CREATE TABLE IF NOT EXISTS saved_searches (
    id SERIAL PRIMARY KEY,
    user_email TEXT NOT NULL,
    search_name TEXT NOT NULL,
    search_filters JSONB NOT NULL, -- Store filter criteria as JSON
    alert_enabled BOOLEAN DEFAULT FALSE,
    alert_frequency TEXT DEFAULT 'daily', -- instant, daily, weekly
    last_alerted TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User activity log
CREATE TABLE IF NOT EXISTS user_activity (
    id SERIAL PRIMARY KEY,
    user_email TEXT NOT NULL,
    activity_type TEXT NOT NULL, -- viewed_lead, submitted_bid, saved_search, etc.
    resource_type TEXT, -- contract, supply_contract, commercial_lead, etc.
    resource_id INTEGER,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lead favorites/bookmarks
CREATE TABLE IF NOT EXISTS saved_leads (
    id SERIAL PRIMARY KEY,
    user_email TEXT NOT NULL,
    lead_type TEXT NOT NULL,
    lead_id INTEGER NOT NULL,
    notes TEXT,
    reminder_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_email, lead_type, lead_id)
);

-- Lead comparisons
CREATE TABLE IF NOT EXISTS lead_comparisons (
    id SERIAL PRIMARY KEY,
    user_email TEXT NOT NULL,
    comparison_name TEXT,
    lead_items JSONB NOT NULL, -- Array of {lead_type, lead_id, data}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification queue
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_email TEXT NOT NULL,
    notification_type TEXT NOT NULL, -- new_lead, deadline_reminder, price_drop, etc.
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    link TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    priority TEXT DEFAULT 'normal', -- low, normal, high, urgent
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

-- User onboarding progress
CREATE TABLE IF NOT EXISTS user_onboarding (
    user_email TEXT PRIMARY KEY,
    completed_welcome BOOLEAN DEFAULT FALSE,
    completed_profile BOOLEAN DEFAULT FALSE,
    completed_first_search BOOLEAN DEFAULT FALSE,
    completed_saved_search BOOLEAN DEFAULT FALSE,
    completed_bid BOOLEAN DEFAULT FALSE,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Performance: Dashboard cache
CREATE TABLE IF NOT EXISTS dashboard_cache (
    user_email TEXT PRIMARY KEY,
    stats_data JSONB NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_prefs_email ON user_preferences(user_email);
CREATE INDEX IF NOT EXISTS idx_saved_searches_email ON saved_searches(user_email);
CREATE INDEX IF NOT EXISTS idx_saved_searches_alert ON saved_searches(alert_enabled, last_alerted);
CREATE INDEX IF NOT EXISTS idx_user_activity_email ON user_activity(user_email);
CREATE INDEX IF NOT EXISTS idx_user_activity_created ON user_activity(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_saved_leads_email ON saved_leads(user_email);
CREATE INDEX IF NOT EXISTS idx_notifications_email ON notifications(user_email, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dashboard_cache_expires ON dashboard_cache(expires_at);

-- Success message
SELECT 'Portal optimization tables created successfully!' AS status;
