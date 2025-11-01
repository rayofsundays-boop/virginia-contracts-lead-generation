-- Create customer_reviews table for storing customer feedback

-- For SQLite (local development)
CREATE TABLE IF NOT EXISTS customer_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    business_name VARCHAR(255),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_title VARCHAR(255),
    review_text TEXT NOT NULL,
    would_recommend BOOLEAN DEFAULT TRUE,
    allow_public BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT FALSE,
    admin_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_reviews_user ON customer_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON customer_reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_public ON customer_reviews(allow_public, is_approved);
CREATE INDEX IF NOT EXISTS idx_reviews_created ON customer_reviews(created_at DESC);
