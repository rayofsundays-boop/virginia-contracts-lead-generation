-- PostgreSQL Migration: Create commercial_lead_requests and bids tables
-- Run this on production database to fix the missing table error

-- Create commercial_lead_requests table (businesses requesting cleaners)
CREATE TABLE IF NOT EXISTS commercial_lead_requests (
    id SERIAL PRIMARY KEY,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create bids table (subscribers bidding on commercial requests)
CREATE TABLE IF NOT EXISTS bids (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL,
    user_email TEXT NOT NULL,
    company_name TEXT NOT NULL,
    bid_amount DECIMAL(10,2) NOT NULL,
    proposal_text TEXT,
    estimated_start_date DATE,
    contact_phone TEXT,
    status TEXT DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES commercial_lead_requests(id)
);

-- Create residential_lead_requests table (homeowners requesting cleaners)
CREATE TABLE IF NOT EXISTS residential_lead_requests (
    id SERIAL PRIMARY KEY,
    homeowner_name TEXT NOT NULL,
    contact_name TEXT NOT NULL,
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
    frequency TEXT NOT NULL,
    services_needed TEXT NOT NULL,
    special_requirements TEXT,
    budget_range TEXT,
    preferred_start_date DATE,
    urgency TEXT DEFAULT 'normal',
    status TEXT DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_commercial_requests_status ON commercial_lead_requests(status);
CREATE INDEX IF NOT EXISTS idx_commercial_requests_urgency ON commercial_lead_requests(urgency);
CREATE INDEX IF NOT EXISTS idx_commercial_requests_created ON commercial_lead_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_commercial_requests_city ON commercial_lead_requests(city);

CREATE INDEX IF NOT EXISTS idx_bids_request_id ON bids(request_id);
CREATE INDEX IF NOT EXISTS idx_bids_user_email ON bids(user_email);
CREATE INDEX IF NOT EXISTS idx_bids_status ON bids(status);

CREATE INDEX IF NOT EXISTS idx_residential_requests_status ON residential_lead_requests(status);
CREATE INDEX IF NOT EXISTS idx_residential_requests_created ON residential_lead_requests(created_at);

-- Insert sample commercial lead requests for testing (Virginia businesses)
INSERT INTO commercial_lead_requests 
(business_name, contact_name, email, phone, address, city, business_type, 
 square_footage, frequency, services_needed, budget_range, urgency, status)
VALUES 
('Tech Innovations LLC', 'Sarah Johnson', 'sarah.j@techinnovations.com', '757-555-0123',
 '1200 Tech Park Drive', 'Virginia Beach', 'Technology Office', 
 15000, 'Bi-weekly', 'Office cleaning, carpet shampooing, window washing', 
 '$2,000-$3,000/month', 'urgent', 'open'),

('Coastal Medical Center', 'Dr. Michael Chen', 'facilities@coastalmedical.com', '757-555-0456',
 '500 Medical Blvd', 'Norfolk', 'Healthcare Facility',
 35000, 'Daily', 'Medical facility cleaning, biohazard disposal, sanitation',
 '$4,000-$6,000/month', 'emergency', 'open'),

('Hampton Roads Law Group', 'Jennifer Martinez', 'office@hrlawgroup.com', '757-555-0789',
 '800 Professional Plaza', 'Hampton', 'Law Office',
 8000, 'Weekly', 'Office cleaning, conference room setup, restroom maintenance',
 '$1,500-$2,500/month', 'normal', 'open'),

('Suffolk Manufacturing Plant', 'Robert Williams', 'facilities@suffolkmfg.com', '757-555-0234',
 '2500 Industrial Drive', 'Suffolk', 'Manufacturing Facility',
 80000, 'Daily', 'Industrial cleaning, floor maintenance, warehouse sweeping',
 '$8,000-$12,000/month', 'urgent', 'open'),

('Newport News Shopping Center', 'Amanda Davis', 'management@nnshoppingcenter.com', '757-555-0567',
 '14000 Jefferson Ave', 'Newport News', 'Retail/Shopping Center',
 125000, 'Daily', 'Common area cleaning, restroom maintenance, parking lot cleanup',
 '$5,000-$7,000/month', 'normal', 'open')
ON CONFLICT DO NOTHING;

-- Success message
SELECT 'Migration completed successfully! Tables created and sample data inserted.' AS status;
