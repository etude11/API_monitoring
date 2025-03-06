import clickhouse_connect

def create_table():
    # Connect to ClickHouse
    client = clickhouse_connect.get_client(host='localhost', username='default', password='')

    # SQL to create the table
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS api_logs (
        timestamp DateTime,
        service String,
        message String,
        status_code Nullable(UInt16),
        response_time Nullable(UInt32),
        http_method Nullable(String),
        endpoint Nullable(String),
        client_ip Nullable(String),
        additional_info String
    ) ENGINE = MergeTree()
    ORDER BY timestamp;
    '''

    # Execute the query
    client.command(create_table_query)
    print("Table 'api_logs' created successfully.")

if __name__ == '__main__':
    create_table()