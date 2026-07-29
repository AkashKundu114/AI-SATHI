ALTER TABLE users 
ADD COLUMN verification_status VARCHAR(20) DEFAULT 'unverified',
ADD COLUMN user_type VARCHAR(30);

CREATE TABLE user_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    doc_type VARCHAR(100) NOT NULL,
    doc_id_number VARCHAR(100),
    doc_image_s3_key VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending',
    submitted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMPTZ,
    reviewer_notes TEXT
);

CREATE INDEX idx_user_verifications_status ON user_verifications(status);
CREATE INDEX idx_user_verifications_user_id ON user_verifications(user_id);
