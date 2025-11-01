-- Database migrations for new features
-- Run these SQL commands in your database

-- Table for consultation requests
CREATE TABLE IF NOT EXISTS consultation_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES leads(id),
    full_name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    solicitation_number VARCHAR(100),
    contract_type VARCHAR(50) NOT NULL,
    proposal_length VARCHAR(50) NOT NULL,
    deadline DATE NOT NULL,
    add_branding BOOLEAN DEFAULT FALSE,
    add_marketing BOOLEAN DEFAULT FALSE,
    add_full_service BOOLEAN DEFAULT FALSE,
    description TEXT NOT NULL,
    contact_method VARCHAR(20) NOT NULL,
    service_level VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for federal contracts launch notifications
CREATE TABLE IF NOT EXISTS launch_notifications (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    notified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for bulk product requests
CREATE TABLE IF NOT EXISTS bulk_product_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES leads(id),
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    unit VARCHAR(50) NOT NULL,
    target_price_per_unit DECIMAL(10,2),
    total_budget DECIMAL(12,2),
    specifications TEXT,
    city VARCHAR(100) NOT NULL,
    zip_code VARCHAR(10) NOT NULL,
    urgency VARCHAR(50) DEFAULT 'flexible',
    status VARCHAR(20) DEFAULT 'open',
    quote_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for bulk product quotes
CREATE TABLE IF NOT EXISTS bulk_product_quotes (
    id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES bulk_product_requests(id),
    user_id INTEGER REFERENCES leads(id),
    price_per_unit DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    delivery_timeline VARCHAR(100) NOT NULL,
    brands TEXT,
    details TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add urgency column to commercial_lead_requests if not exists
ALTER TABLE commercial_lead_requests ADD COLUMN IF NOT EXISTS urgency VARCHAR(20) DEFAULT 'normal';

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_consultation_user_id ON consultation_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_consultation_status ON consultation_requests(status);
CREATE INDEX IF NOT EXISTS idx_launch_email ON launch_notifications(email);
CREATE INDEX IF NOT EXISTS idx_launch_notified ON launch_notifications(notified);
CREATE INDEX IF NOT EXISTS idx_bulk_requests_category ON bulk_product_requests(category);
CREATE INDEX IF NOT EXISTS idx_bulk_requests_status ON bulk_product_requests(status);
CREATE INDEX IF NOT EXISTS idx_bulk_requests_urgency ON bulk_product_requests(urgency);
CREATE INDEX IF NOT EXISTS idx_bulk_quotes_request ON bulk_product_quotes(request_id);
CREATE INDEX IF NOT EXISTS idx_bulk_quotes_user ON bulk_product_quotes(user_id);
CREATE INDEX IF NOT EXISTS idx_commercial_urgency ON commercial_lead_requests(urgency);

-- For SQLite (if using locally), use this instead:
-- CREATE TABLE IF NOT EXISTS consultation_requests (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     user_id INTEGER REFERENCES leads(id),
--     full_name VARCHAR(255) NOT NULL,
--     company_name VARCHAR(255) NOT NULL,
--     email VARCHAR(255) NOT NULL,
--     phone VARCHAR(50) NOT NULL,
--     solicitation_number VARCHAR(100),
--     contract_type VARCHAR(50) NOT NULL,
--     proposal_length VARCHAR(50) NOT NULL,
--     deadline DATE NOT NULL,
--     add_branding BOOLEAN DEFAULT 0,
--     add_marketing BOOLEAN DEFAULT 0,
--     add_full_service BOOLEAN DEFAULT 0,
--     description TEXT NOT NULL,
--     contact_method VARCHAR(20) NOT NULL,
--     service_level VARCHAR(20),
--     status VARCHAR(20) DEFAULT 'pending',
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE TABLE IF NOT EXISTS launch_notifications (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     email VARCHAR(255) UNIQUE NOT NULL,
--     notified BOOLEAN DEFAULT 0,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE TABLE IF NOT EXISTS bulk_product_requests (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     user_id INTEGER REFERENCES leads(id),
--     company_name VARCHAR(255) NOT NULL,
--     contact_name VARCHAR(255) NOT NULL,
--     email VARCHAR(255) NOT NULL,
--     phone VARCHAR(50) NOT NULL,
--     product_name VARCHAR(255) NOT NULL,
--     description TEXT NOT NULL,
--     category VARCHAR(50) NOT NULL,
--     quantity INTEGER NOT NULL,
--     unit VARCHAR(50) NOT NULL,
--     target_price_per_unit DECIMAL(10,2),
--     total_budget DECIMAL(12,2),
--     specifications TEXT,
--     city VARCHAR(100) NOT NULL,
--     zip_code VARCHAR(10) NOT NULL,
--     urgency VARCHAR(50) DEFAULT 'flexible',
--     status VARCHAR(20) DEFAULT 'open',
--     quote_count INTEGER DEFAULT 0,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE TABLE IF NOT EXISTS bulk_product_quotes (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     request_id INTEGER REFERENCES bulk_product_requests(id),
--     user_id INTEGER REFERENCES leads(id),
--     price_per_unit DECIMAL(10,2) NOT NULL,
--     total_amount DECIMAL(12,2) NOT NULL,
--     delivery_timeline VARCHAR(100) NOT NULL,
--     brands TEXT,
--     details TEXT,
--     status VARCHAR(20) DEFAULT 'pending',
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- Table for buyer bulk purchase requests (companies wanting to purchase products)
CREATE TABLE IF NOT EXISTS bulk_purchase_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES leads(id),
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    product_category VARCHAR(100) NOT NULL,
    product_description TEXT NOT NULL,
    quantity VARCHAR(255) NOT NULL,
    budget VARCHAR(100),
    delivery_location VARCHAR(100) NOT NULL,
    needed_by DATE NOT NULL,
    urgency VARCHAR(50) DEFAULT 'standard',
    additional_notes TEXT,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
