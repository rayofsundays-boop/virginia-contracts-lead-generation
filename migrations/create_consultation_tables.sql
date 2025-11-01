-- Consultation Requests Table (SQLite)
CREATE TABLE IF NOT EXISTS consultation_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    full_name TEXT NOT NULL,
    company_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    service_level TEXT NOT NULL,
    base_price INTEGER NOT NULL,
    solicitation_number TEXT,
    contract_type TEXT NOT NULL,
    proposal_length TEXT NOT NULL,
    deadline TEXT NOT NULL,
    add_branding BOOLEAN DEFAULT FALSE,
    add_marketing BOOLEAN DEFAULT FALSE,
    add_full_service BOOLEAN DEFAULT FALSE,
    description TEXT,
    contact_method TEXT NOT NULL,
    total_amount INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Consultation Payments Table (SQLite)
CREATE TABLE IF NOT EXISTS consultation_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    service_level TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    amount INTEGER NOT NULL,
    transaction_id TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_consultation_requests_email ON consultation_requests(user_email);
CREATE INDEX IF NOT EXISTS idx_consultation_requests_status ON consultation_requests(status);
CREATE INDEX IF NOT EXISTS idx_consultation_payments_email ON consultation_payments(user_email);
CREATE INDEX IF NOT EXISTS idx_consultation_payments_status ON consultation_payments(status);
