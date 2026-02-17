-- TG Business Suite Database Initialization

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('owner', 'admin', 'staff', 'viewer');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE account_status AS ENUM ('active', 'inactive', 'banned', 'auth_required', 'connection_error', 'pending');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE proxy_status AS ENUM ('active', 'inactive', 'testing', 'dead');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE proxy_protocol AS ENUM ('http', 'https', 'socks5');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE task_type AS ENUM ('profile_photo', 'bio_update', 'username_update', 'media_send', 'message_send');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE task_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE subscription_tier AS ENUM ('starter', 'pro', 'agency');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE subscription_status AS ENUM ('active', 'past_due', 'cancelled', 'trialing');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_organization ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_telegram_accounts_organization ON telegram_accounts(organization_id);
CREATE INDEX IF NOT EXISTS idx_telegram_accounts_status ON telegram_accounts(status);
CREATE INDEX IF NOT EXISTS idx_proxies_organization ON proxies(organization_id);
CREATE INDEX IF NOT EXISTS idx_automation_tasks_organization ON automation_tasks(organization_id);
CREATE INDEX IF NOT EXISTS idx_automation_tasks_status ON automation_tasks(status);
CREATE INDEX IF NOT EXISTS idx_activity_logs_organization ON activity_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tguser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tguser;
