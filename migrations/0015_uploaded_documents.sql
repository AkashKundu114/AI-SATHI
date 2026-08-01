CREATE TABLE IF NOT EXISTS uploaded_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_phone VARCHAR(20) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    size_bytes INTEGER,
    text_content TEXT,
    blob_url VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT _user_filename_uc UNIQUE (user_phone, filename)
);
