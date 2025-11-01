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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_consultation_user_id ON consultation_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_consultation_status ON consultation_requests(status);
CREATE INDEX IF NOT EXISTS idx_launch_email ON launch_notifications(email);
CREATE INDEX IF NOT EXISTS idx_launch_notified ON launch_notifications(notified);

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
