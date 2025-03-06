import clickhouse_connect
from datetime import datetime
import re
import json

def parse_log_line(line):
    try:
        # Split the line into timestamp and the rest
        parts = line.strip().split(' ', 3)
        if len(parts) < 4:
            return None
        
        # Extract timestamp
        timestamp_str = ' '.join(parts[:2])
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        # Extract service and message
        service_part = parts[3]
        service = service_part.split(' ')[1]
        message = ' '.join(service_part.split(' ')[2:])
        
        # Initialize fields
        status_code = None
        response_time = None
        http_method = None
        endpoint = None
        client_ip = None
        additional_info = {}

        # Extract response time and status code
        time_match = re.search(r'(response time|time): (\d+)ms', message)
        if time_match:
            response_time = int(time_match.group(2))
        
        status_match = re.search(r'status: (\d+)', message)
        if status_match:
            status_code = int(status_match.group(1))

        # Extract HTTP method, endpoint, client IP
        if 'received request' in message:
            match = re.search(r'received request: (\w+) (\/\S+) from (\S+)', message)
            if match:
                http_method = match.group(1)
                endpoint = match.group(2)
                client_ip = match.group(3)
        elif 'response sent' in message:
            match = re.search(r'response sent for \w+ (\/\S+),', message)
            if match:
                endpoint = match.group(1)

        # Extract additional info (userID, productID, etc.)
        for field in ['userID', 'productID', 'orderID', 'transactionID']:
            match = re.search(fr'{field}=(\d+)', message)
            if match:
                additional_info[field] = match.group(1)

        return {
            'timestamp': timestamp,
            'service': service,
            'message': message,
            'status_code': status_code,
            'response_time': response_time,
            'http_method': http_method,
            'endpoint': endpoint,
            'client_ip': client_ip,
            'additional_info': json.dumps(additional_info)
        }
    except Exception as e:
        print(f"Error parsing line: {line}\nError: {e}")
        return None

def main():
    client = clickhouse_connect.get_client(host='localhost', username='default', password='')
    
    with open('logs.txt', 'r') as f:
        logs = [parse_log_line(line) for line in f if line.strip()]
    
    valid_logs = [log for log in logs if log]
    
    # Define column names in the order they appear in the table
    column_names = ['timestamp', 'service', 'message', 'status_code', 
                    'response_time', 'http_method', 'endpoint', 'client_ip', 
                    'additional_info']
    
    # Convert list of dictionaries to list of lists
    rows = [[log[col] for col in column_names] for log in valid_logs]
    
    # Insert the data
    client.insert('api_logs', rows, column_names=column_names)
    print(f"Inserted {len(valid_logs)} logs into ClickHouse")

if __name__ == '__main__':
    main()
