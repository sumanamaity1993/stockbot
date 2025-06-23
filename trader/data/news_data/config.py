import os

# NEWS_DATA_CONFIG should only reference environment variables for sensitive data.
# Set your API keys and secrets in a .env file or as environment variables.
NEWS_DATA_CONFIG = {
    'GNEWS_API_KEY': os.getenv('GNEWS_API_KEY'),
    'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY'),
    'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID'),
    'REDDIT_CLIENT_SECRET': os.getenv('REDDIT_CLIENT_SECRET'),
    'REDDIT_USER_AGENT': os.getenv('REDDIT_USER_AGENT'),
    'ENABLED_SOURCES': ['gnews', 'newsapi', 'reddit'],
    'FETCH_INTERVAL_MINUTES': 30,
} 