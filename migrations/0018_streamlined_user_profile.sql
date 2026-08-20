DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'gender') THEN
        ALTER TABLE users ADD COLUMN gender VARCHAR(20);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'dob') THEN
        ALTER TABLE users ADD COLUMN dob VARCHAR(30);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'pincode') THEN
        ALTER TABLE users ADD COLUMN pincode VARCHAR(10);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'shg_reg_no') THEN
        ALTER TABLE users ADD COLUMN shg_reg_no VARCHAR(100);
    END IF;
END $$;
