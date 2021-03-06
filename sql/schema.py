CREATE_USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    password TEXT,
    salt TEXT,
    first_name TEXT,
    last_name TEXT,
    email_address TEXT UNIQUE,
    username TEXT UNIQUE,
    receive_emails_enabled BOOL DEFAULT True,
    phone_number TEXT UNIQUE,
    uid UUID DEFAULT uuid_generate_v4 () UNIQUE,
    external_id TEXT,
    sms_verification TEXT DEFAULT Null,
    sms_2fa_enabled BOOL DEFAULT False,
    active BOOL DEFAULT False,
    activation_key UUID DEFAULT uuid_generate_v4 () UNIQUE,
    register_date DATE
);
""".strip()

CREATE_PRE_REGISTER_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pre_register (
    id SERIAL PRIMARY KEY,
    email_address TEXT UNIQUE,
    username TEXT UNIQUE,
    uid UUID DEFAULT uuid_generate_v4 () UNIQUE,
    active BOOL DEFAULT False,
    activation_key UUID DEFAULT uuid_generate_v4 () UNIQUE,
    register_date DATE DEFAULT now()
);
""".strip()

CREATE_IV_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS identity_verifications (
    id SERIAL PRIMARY KEY,
    data JSON,
    scan_reference TEXT
);
""".strip()

CREATE_RESET_TOKENS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS reset_tokens (
    user_id INTEGER REFERENCES users(id) PRIMARY KEY,
    reset_token UUID DEFAULT NULL UNIQUE,
    reset_token_creation_time TIMESTAMP,
    email_address TEXT REFERENCES users(email_address)
);
""".strip()

CREATE_CONTACT_TRANSACTIONS_SQL = """
CREATE TABLE IF NOT EXISTS contact_transactions (
    id SERIAL PRIMARY KEY,
    uid UUID DEFAULT uuid_generate_v4 () UNIQUE,
    transaction_hash TEXT DEFAULT NULL,
    recipient TEXT,
    user_id INTEGER REFERENCES users(id),
    transaction_type TEXT,
    currency TEXT,
    amount FLOAT,
    created TIMESTAMP(0),
    status TEXT DEFAULT 'pending',
    last_notified TIMESTAMP(0) DEFAULT now()
);
""".strip()

CREATE_CURRENCY_ENUM_SQL = """
CREATE TYPE e_currency AS ENUM (
    'ETH',
    'BTC',
    'BOAR'
)
""".strip()

CREATE_ADDRESSES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS public_addresses (
    user_id INTEGER REFERENCES users(id),
    currency e_currency,
    address TEXT,
    CONSTRAINT pk_addresses PRIMARY KEY (user_id, currency)
)
""".strip()

CREATE_VOTING_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS votes (
    date TIMESTAMP(0) DEFAULT now(),
    name TEXT,
    symbol TEXT,
    ip TEXT,
    CONSTRAINT pk_voting PRIMARY KEY (symbol, ip)
)
""".strip()

CREATE_SUPPORTED_COINS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS supported_coins (
    symbol TEXT PRIMARY KEY,
    name TEXT,
    cmc_rank INTEGER DEFAULT NULL,
    round_won INTEGER DEFAULT NULL
)
""".strip()

CREATE_BLACKLIST_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS blacklist (
    username TEXT
)""".strip()

CREATE_DEVICES_ENUM_SQL = """
CREATE TYPE e_device_type AS ENUM (
    'ios',
    'android',
    'api'
)
""".strip()

CREATE_DEVICES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS devices (
    user_id INTEGER REFERENCES users(id),
    user_uid UUID REFERENCES users(uid),
    session_id TEXT default Null,
    device_type e_device_type,
    channel TEXT,
    ip TEXT,
    date TIMESTAMP(0),
    CONSTRAINT pk_channel_user_id PRIMARY KEY (user_id, channel)
)
""".strip()
