-- Admin Enhancement Features Migration
-- Created: November 1, 2025

-- Internal Messaging System
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    recipient_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    is_admin_message BOOLEAN DEFAULT FALSE,
    parent_message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_read ON messages(is_read);

-- User Surveys (Post-Registration)
CREATE TABLE IF NOT EXISTS user_surveys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    how_found_us VARCHAR(255),
    interested_features TEXT,
    suggestions TEXT,
    service_type VARCHAR(100),
    company_size VARCHAR(50),
    annual_revenue_range VARCHAR(50),
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_surveys_user ON user_surveys(user_id);

-- College and University Procurement Opportunities
CREATE TABLE IF NOT EXISTS educational_contracts (
    id SERIAL PRIMARY KEY,
    institution_name VARCHAR(255) NOT NULL,
    institution_type VARCHAR(50) NOT NULL,
    city VARCHAR(100) NOT NULL,
    county VARCHAR(100),
    contact_name VARCHAR(255),
    contact_title VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    department VARCHAR(255),
    opportunity_title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100) DEFAULT 'Cleaning & Janitorial',
    estimated_value DECIMAL(12,2),
    contract_term VARCHAR(100),
    bid_deadline DATE,
    start_date DATE,
    requirements TEXT,
    submission_method VARCHAR(255),
    website_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_edu_contracts_city ON educational_contracts(city);
CREATE INDEX IF NOT EXISTS idx_edu_contracts_institution ON educational_contracts(institution_name);
CREATE INDEX IF NOT EXISTS idx_edu_contracts_deadline ON educational_contracts(bid_deadline);
CREATE INDEX IF NOT EXISTS idx_edu_contracts_status ON educational_contracts(status);

-- Industry Days and Events
CREATE TABLE IF NOT EXISTS industry_days (
    id SERIAL PRIMARY KEY,
    event_title VARCHAR(255) NOT NULL,
    organizer VARCHAR(255) NOT NULL,
    organizer_type VARCHAR(100),
    event_date DATE NOT NULL,
    event_time VARCHAR(100),
    location VARCHAR(255),
    city VARCHAR(100),
    venue_name VARCHAR(255),
    event_type VARCHAR(100) DEFAULT 'Industry Day',
    description TEXT,
    target_audience VARCHAR(255),
    registration_required BOOLEAN DEFAULT TRUE,
    registration_deadline DATE,
    registration_link VARCHAR(500),
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    topics TEXT,
    is_virtual BOOLEAN DEFAULT FALSE,
    virtual_link VARCHAR(500),
    attachments TEXT,
    status VARCHAR(50) DEFAULT 'upcoming',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_industry_days_date ON industry_days(event_date);
CREATE INDEX IF NOT EXISTS idx_industry_days_city ON industry_days(city);
CREATE INDEX IF NOT EXISTS idx_industry_days_status ON industry_days(status);

-- Page Analytics (Track User Behavior)
CREATE TABLE IF NOT EXISTS page_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    page_url VARCHAR(500) NOT NULL,
    page_title VARCHAR(255),
    referrer VARCHAR(500),
    session_id VARCHAR(100),
    ip_address VARCHAR(50),
    user_agent TEXT,
    time_spent_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analytics_user ON page_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_page ON page_analytics(page_url);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON page_analytics(created_at);

-- Proposal Reviews (Admin Review System)
CREATE TABLE IF NOT EXISTS proposal_reviews (
    id SERIAL PRIMARY KEY,
    proposal_request_id INTEGER NOT NULL,
    admin_id INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'pending',
    admin_notes TEXT,
    feedback_to_user TEXT,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_proposal_reviews_request ON proposal_reviews(proposal_request_id);
CREATE INDEX IF NOT EXISTS idx_proposal_reviews_status ON proposal_reviews(status);

-- Admin Actions Log
CREATE TABLE IF NOT EXISTS admin_actions (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    action_type VARCHAR(100) NOT NULL,
    target_user_id INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    action_details TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_actions_admin ON admin_actions(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_actions_type ON admin_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_admin_actions_date ON admin_actions(created_at);

-- User Activity Sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);

-- Revenue Tracking
CREATE TABLE IF NOT EXISTS revenue_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    subscription_type VARCHAR(50),
    payment_method VARCHAR(50),
    transaction_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'completed',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_revenue_user ON revenue_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_revenue_type ON revenue_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_revenue_date ON revenue_transactions(created_at);

-- Password Reset Tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_by_admin_id INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reset_tokens_user ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_reset_tokens_token ON password_reset_tokens(token);

-- Add unread message count helper view
CREATE OR REPLACE VIEW user_message_stats AS
SELECT 
    recipient_id as user_id,
    COUNT(*) FILTER (WHERE is_read = FALSE) as unread_count,
    COUNT(*) as total_messages,
    MAX(created_at) as last_message_at
FROM messages
GROUP BY recipient_id;

-- Add admin analytics summary view
CREATE OR REPLACE VIEW admin_dashboard_stats AS
SELECT 
    (SELECT COUNT(*) FROM leads WHERE subscription_status = 'paid') as paid_subscribers,
    (SELECT COUNT(*) FROM leads WHERE subscription_status = 'free') as free_users,
    (SELECT COUNT(*) FROM leads WHERE created_at > NOW() - INTERVAL '30 days') as new_users_30d,
    (SELECT SUM(amount) FROM revenue_transactions WHERE created_at > NOW() - INTERVAL '30 days') as revenue_30d,
    (SELECT COUNT(*) FROM page_analytics WHERE created_at > NOW() - INTERVAL '24 hours') as page_views_24h,
    (SELECT COUNT(DISTINCT user_id) FROM page_analytics WHERE created_at > NOW() - INTERVAL '24 hours') as active_users_24h;
