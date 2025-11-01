-- ========================================
-- COMMERCIAL LEAD REQUESTS TABLES
-- Created: 2025-11-01
-- Purpose: Create tables for commercial lead marketplace
-- ========================================

-- Commercial lead requests table (businesses requesting cleaners)
CREATE TABLE IF NOT EXISTS commercial_lead_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_name TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT DEFAULT 'VA',
    zip_code TEXT,
    business_type TEXT NOT NULL,
    square_footage INTEGER,
    frequency TEXT NOT NULL,
    services_needed TEXT NOT NULL,
    special_requirements TEXT,
    budget_range TEXT,
    start_date DATE,
    urgency TEXT DEFAULT 'normal',
    status TEXT DEFAULT 'open',
    bid_count INTEGER DEFAULT 0,
    winning_bid_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Bids table (subscribers bidding on commercial requests)
CREATE TABLE IF NOT EXISTS bids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    user_email TEXT NOT NULL,
    company_name TEXT NOT NULL,
    bid_amount DECIMAL(10,2) NOT NULL,
    proposal_text TEXT,
    estimated_start_date DATE,
    contact_phone TEXT,
    status TEXT DEFAULT 'pending',
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    accepted_at DATETIME,
    FOREIGN KEY (request_id) REFERENCES commercial_lead_requests(id) ON DELETE CASCADE
);

-- Residential lead requests table (homeowners requesting cleaners)
CREATE TABLE IF NOT EXISTS residential_lead_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    homeowner_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT DEFAULT 'VA',
    zip_code TEXT,
    property_type TEXT NOT NULL,
    square_footage INTEGER,
    bedrooms INTEGER,
    bathrooms INTEGER,
    service_type TEXT NOT NULL,
    frequency TEXT,
    special_requirements TEXT,
    budget_range TEXT,
    preferred_date DATE,
    urgency TEXT DEFAULT 'normal',
    status TEXT DEFAULT 'open',
    bid_count INTEGER DEFAULT 0,
    winning_bid_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_commercial_requests_status ON commercial_lead_requests(status);
CREATE INDEX IF NOT EXISTS idx_commercial_requests_urgency ON commercial_lead_requests(urgency);
CREATE INDEX IF NOT EXISTS idx_commercial_requests_city ON commercial_lead_requests(city);
CREATE INDEX IF NOT EXISTS idx_commercial_requests_created ON commercial_lead_requests(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_bids_request_id ON bids(request_id);
CREATE INDEX IF NOT EXISTS idx_bids_user_email ON bids(user_email);
CREATE INDEX IF NOT EXISTS idx_bids_status ON bids(status);

CREATE INDEX IF NOT EXISTS idx_residential_requests_status ON residential_lead_requests(status);
CREATE INDEX IF NOT EXISTS idx_residential_requests_city ON residential_lead_requests(city);
CREATE INDEX IF NOT EXISTS idx_residential_requests_created ON residential_lead_requests(created_at DESC);
