-- Consultation Requests Table (PostgreSQL)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'consultation_requests') THEN
        CREATE TABLE consultation_requests (
            id SERIAL PRIMARY KEY,
            user_email VARCHAR(255) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            company_name VARCHAR(255) NOT NULL,
            phone VARCHAR(50) NOT NULL,
            service_level VARCHAR(50) NOT NULL,
            base_price INTEGER NOT NULL,
            solicitation_number VARCHAR(100),
            contract_type VARCHAR(50) NOT NULL,
            proposal_length VARCHAR(50) NOT NULL,
            deadline DATE NOT NULL,
            add_branding BOOLEAN DEFAULT FALSE,
            add_marketing BOOLEAN DEFAULT FALSE,
            add_full_service BOOLEAN DEFAULT FALSE,
            description TEXT,
            contact_method VARCHAR(50) NOT NULL,
            total_amount INTEGER NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX idx_consultation_requests_email ON consultation_requests(user_email);
        CREATE INDEX idx_consultation_requests_status ON consultation_requests(status);
    END IF;
END $$;

-- Consultation Payments Table (PostgreSQL)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'consultation_payments') THEN
        CREATE TABLE consultation_payments (
            id SERIAL PRIMARY KEY,
            user_email VARCHAR(255) NOT NULL,
            service_level VARCHAR(50) NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            amount INTEGER NOT NULL,
            transaction_id VARCHAR(100),
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX idx_consultation_payments_email ON consultation_payments(user_email);
        CREATE INDEX idx_consultation_payments_status ON consultation_payments(status);
    END IF;
END $$;
