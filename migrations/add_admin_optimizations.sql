-- ========================================
-- ADMIN OPTIMIZATION: DATABASE INDEXES
-- Created: 2025-11-01
-- Purpose: Speed up admin panel queries
-- ========================================

-- Index for admin user lookups (used in authentication)
CREATE INDEX IF NOT EXISTS idx_leads_is_admin ON leads(is_admin);

-- Index for subscription status filtering (used in user management)
CREATE INDEX IF NOT EXISTS idx_leads_subscription_status ON leads(subscription_status);

-- Composite index for admin user queries (filter by admin status and sort by date)
CREATE INDEX IF NOT EXISTS idx_leads_admin_created ON leads(is_admin, created_at DESC);

-- Index for message queries (recipient + read status)
CREATE INDEX IF NOT EXISTS idx_messages_recipient_read ON messages(recipient_id, is_read);

-- Index for recent user activity queries
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);

-- Index for user search by email (used in admin panel search)
CREATE INDEX IF NOT EXISTS idx_leads_email_lower ON leads(LOWER(email));

-- Index for company name search
CREATE INDEX IF NOT EXISTS idx_leads_company_name ON leads(company_name);

-- ========================================
-- ADMIN ACTIONS TABLE (for audit logging)
-- ========================================

-- Create admin_actions table if it doesn't exist
CREATE TABLE IF NOT EXISTS admin_actions (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    target_user_id INTEGER,
    action_details TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES leads(id) ON DELETE CASCADE,
    FOREIGN KEY (target_user_id) REFERENCES leads(id) ON DELETE SET NULL
);

-- Index for admin action lookups
CREATE INDEX IF NOT EXISTS idx_admin_actions_admin_id ON admin_actions(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_actions_timestamp ON admin_actions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_admin_actions_type ON admin_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_admin_actions_target ON admin_actions(target_user_id);

-- ========================================
-- PERFORMANCE NOTES
-- ========================================
-- These indexes will speed up:
-- 1. Admin authentication (idx_leads_is_admin)
-- 2. User filtering by subscription (idx_leads_subscription_status)
-- 3. Message unread counts (idx_messages_recipient_read)
-- 4. Recent user queries (idx_leads_created_at)
-- 5. User search (idx_leads_email_lower, idx_leads_company_name)
-- 6. Admin audit trail queries (admin_actions indexes)

-- Expected improvement: 50-80% faster admin panel queries
