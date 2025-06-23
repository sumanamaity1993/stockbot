CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    symbol TEXT,
    published_at TIMESTAMP,
    title TEXT,
    summary TEXT,
    source TEXT,
    url TEXT,
    fetched_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sentiment_scores (
    id SERIAL PRIMARY KEY,
    symbol TEXT,
    source TEXT,
    reference_id INT,
    sentiment_model TEXT,
    score NUMERIC,
    label TEXT,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trading_signals (
    id SERIAL PRIMARY KEY,
    symbol TEXT,
    strategy TEXT,
    signal TEXT,
    signal_score NUMERIC,
    generated_at TIMESTAMP DEFAULT now(),
    note TEXT
); 