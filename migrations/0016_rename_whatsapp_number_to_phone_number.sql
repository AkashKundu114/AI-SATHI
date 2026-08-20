DO $$ 
BEGIN 
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'whatsapp_number'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'phone_number'
    ) THEN
        ALTER TABLE users RENAME COLUMN whatsapp_number TO phone_number;
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'users' AND indexname = 'idx_users_whatsapp_number'
    ) THEN
        ALTER INDEX idx_users_whatsapp_number RENAME TO idx_users_phone_number;
    END IF;
END $$;
