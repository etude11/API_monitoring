# Configuration for the log analyzer

CLICKHOUSE_CONFIG = {
    'host': '10.1.101.196',
    'port': 9000,
    'user': 'default',
    'password': '',
    'database': 'otel'
}

# How often to poll for new data (in seconds)
POLL_INTERVAL = 10

# Time window for historical data on startup (in hours)
INITIAL_HISTORY_HOURS = 1

# Maximum number of data points to keep in memory for each analysis
MAX_DATA_POINTS = 1000
