import clickhouse_connect
import matplotlib.pyplot as plt
from datetime import datetime

def fetch_data(client):
    # Query for responses (where message contains 'response sent')
    response_query = """
    SELECT timestamp, response_time
    FROM api_logs
    WHERE service = 'response'
      AND response_time IS NOT NULL
    ORDER BY timestamp
    """
    
    # Execute queries
    response_result = client.query(response_query)
    
    # Extract data
    response_timestamps = [row[0] for row in response_result.result_rows]
    response_times = [row[1] for row in response_result.result_rows]
    
    return (response_timestamps, response_times)

def plot_response_times(response_data):
    # Unpack data
    response_timestamps, response_times = response_data
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Plot responses
    if response_timestamps:
        ax.plot(response_timestamps, response_times, 'r-', label='Response Sent Time')
        ax.scatter(response_timestamps, response_times, color='red', s=20)
        ax.set_title('Response Times for Responses')
        ax.set_xlabel('Timestamp')
        ax.set_ylabel('Response Time (ms)')
        ax.legend()
        ax.grid(True)
    
    # Adjust layout and display
    plt.tight_layout()
    plt.show()

def main():
    # Connect to ClickHouse
    client = clickhouse_connect.get_client(host='localhost', username='default', password='')
    
    # Fetch data
    response_data = fetch_data(client)
    
    # Check if there's data to plot
    if not response_data[0]:
        print("No data available to plot.")
        return
    
    # Plot the data
    plot_response_times(response_data)
    
    # Print some basic stats
    if response_data[1]:
        print(f"Responses - Avg Response Time: {sum(response_data[1]) / len(response_data[1]):.2f} ms, "
              f"Min: {min(response_data[1])} ms, Max: {max(response_data[1])} ms")

if __name__ == '__main__':
    main()
