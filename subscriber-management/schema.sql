CREATE TABLE IF NOT EXISTS filter_criteria (
    id SERIAL PRIMARY KEY,
    subscriber_id VARCHAR(100) UNIQUE NOT NULL,
    event_types TEXT[] NOT NULL,
    user_tiers TEXT[],
    min_amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);