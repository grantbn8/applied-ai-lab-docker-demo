-- Existing messages were all generated with the local model.
ALTER TABLE messages ADD COLUMN IF NOT EXISTS provider TEXT NOT NULL DEFAULT 'local'
    CHECK (provider IN ('local', 'chatgpt'));
