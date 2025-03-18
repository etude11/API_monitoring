
import pandas as pd
import numpy as np
from clickhouse_driver import Client
from datetime import datetime, timedelta
import scipy.stats as stats

# Connect to ClickHouse database
def get_db_connection():
    client = Client(
        host='10.1.101.196',
        port=9000,
        database='otel'  # Database name is correct
    )
    return client

# 1. Response Times Over Time
def get_response_times_over_time(client, time_range='day'):
    """
    Extract response time data with timestamps for plotting a line chart
    
    Args:
        client: ClickHouse client
        time_range: 'hour', 'day', 'week', or 'all'
    
    Returns:
        DataFrame with timestamps and response times
    """
    # Define time filter based on range
    if time_range == 'hour':
        time_filter = "Timestamp >= now() - INTERVAL 1 HOUR"
    elif time_range == 'day':
        time_filter = "Timestamp >= now() - INTERVAL 1 DAY"
    elif time_range == 'week':
        time_filter = "Timestamp >= now() - INTERVAL 1 WEEK"
    else:  # all time
        time_filter = "1=1"
    
    query = f"""
        SELECT 
            Timestamp, 
            Duration / 1000000 as response_time  -- Convert from nanoseconds to milliseconds
        FROM 
            otel_traces
        WHERE 
            {time_filter}
        ORDER BY 
            Timestamp ASC
    """
    
    result = client.execute(query)
    
    # Add endpoint information if available from SpanName
    if result:
        df = pd.DataFrame(result, columns=['timestamp', 'response_time'])
        
        # Try to get endpoint information
        try:
            endpoint_query = f"""
                SELECT 
                    Timestamp, 
                    SpanName as endpoint
                FROM 
                    otel_traces
                WHERE 
                    {time_filter}
                ORDER BY 
                    Timestamp ASC
            """
            endpoint_result = client.execute(endpoint_query)
            endpoint_df = pd.DataFrame(endpoint_result, columns=['timestamp', 'endpoint'])
            
            # Merge the endpoint information
            df = pd.merge(df, endpoint_df, on='timestamp', how='left')
        except Exception as e:
            # If we can't get endpoint info, continue without it
            pass
            
        # Calculate trend line
        if len(df) > 1:
            x = np.array(range(len(df)))
            y = df['response_time'].values
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            df['trend'] = intercept + slope * x
            
        return df
    else:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['timestamp', 'response_time', 'endpoint', 'trend'])

# 2. Response Time Distribution
def get_response_time_distribution(client, time_range='day', num_buckets=20):
    """
    Extract response time data for histogram
    
    Args:
        client: ClickHouse client
        time_range: 'hour', 'day', 'week', or 'all'
        num_buckets: Number of histogram buckets
    
    Returns:
        DataFrame with buckets and counts
    """
    # Define time filter based on range
    if time_range == 'hour':
        time_filter = "Timestamp >= now() - INTERVAL 1 HOUR"
    elif time_range == 'day':
        time_filter = "Timestamp >= now() - INTERVAL 1 DAY"
    elif time_range == 'week':
        time_filter = "Timestamp >= now() - INTERVAL 1 WEEK"
    else:  # all time
        time_filter = "1=1"
    
    query = f"""
        SELECT 
            Duration / 1000000 as response_time  -- Convert from nanoseconds to milliseconds
        FROM 
            otel_traces
        WHERE 
            {time_filter}
    """
    
    result = client.execute(query)
    response_times = [item[0] for item in result]
    
    if not response_times:
        # Handle empty result
        return pd.DataFrame(columns=['bin_start', 'bin_end', 'count', 'bin_label'])
    
    # Find reasonable min and max for bins based on actual data
    min_time = min(response_times)
    max_time = max(response_times)
    
    # Make sure we have a reasonable range
    if min_time == max_time:
        min_time = 0.9 * min_time if min_time > 0 else 0
        max_time = 1.1 * max_time if max_time > 0 else 1
    
    # Create histogram data
    hist, bin_edges = np.histogram(response_times, bins=num_buckets, range=(min_time, max_time))
    
    # Create a DataFrame with the histogram data
    df = pd.DataFrame({
        'bin_start': bin_edges[:-1],
        'bin_end': bin_edges[1:],
        'count': hist
    })
    
    # Create labels for each bin
    df['bin_label'] = df.apply(lambda row: f"{row['bin_start']:.2f}-{row['bin_end']:.2f}ms", axis=1)
    
    return df

# 3. Error Status Codes Distribution
def get_error_status_distribution(client, time_range='day'):
    """
    Extract error status codes and their counts
    
    Args:
        client: ClickHouse client
        time_range: 'hour', 'day', 'week', or 'all'
    
    Returns:
        DataFrame with status codes and counts
    """
    # Define time filter based on range
    if time_range == 'hour':
        time_filter = "Timestamp >= now() - INTERVAL 1 HOUR"
    elif time_range == 'day':
        time_filter = "Timestamp >= now() - INTERVAL 1 DAY"
    elif time_range == 'week':
        time_filter = "Timestamp >= now() - INTERVAL 1 WEEK"
    else:  # all time
        time_filter = "1=1"
    
    # Instead of using JSON fields, use the StatusCode field directly
    query = f"""
        SELECT 
            StatusCode as status_code,
            COUNT(*) as count
        FROM 
            otel_traces 
        WHERE 
            {time_filter} AND
            StatusCode = 'STATUS_CODE_ERROR'
        GROUP BY 
            status_code
        ORDER BY 
            count DESC
    """
    
    try:
        result = client.execute(query)
        df = pd.DataFrame(result, columns=['status_code', 'count'])
    except Exception as e:
        print(f"Error in status distribution query: {e}")
        # Fallback to simple status count
        fallback_query = f"""
            SELECT 
                'Error' as status_code,
                COUNT(*) as count
            FROM 
                otel_traces 
            WHERE 
                {time_filter} AND
                StatusCode != 'STATUS_CODE_UNSET'
        """
        result = client.execute(fallback_query)
        df = pd.DataFrame(result, columns=['status_code', 'count'])
        
    return df

# 4. Statistical Metrics
def get_statistical_metrics(client, time_range='day'):
    """
    Calculate statistical metrics for response times
    
    Args:
        client: ClickHouse client
        time_range: 'hour', 'day', 'week', or 'all'
    
    Returns:
        Dictionary with stats metrics
    """
    # Define time filter based on range
    if time_range == 'hour':
        time_filter = "Timestamp >= now() - INTERVAL 1 HOUR"
        prev_filter = "Timestamp >= now() - INTERVAL 2 HOUR AND Timestamp < now() - INTERVAL 1 HOUR"
    elif time_range == 'day':
        time_filter = "Timestamp >= now() - INTERVAL 1 DAY"
        prev_filter = "Timestamp >= now() - INTERVAL 2 DAY AND Timestamp < now() - INTERVAL 1 DAY"
    elif time_range == 'week':
        time_filter = "Timestamp >= now() - INTERVAL 1 WEEK"
        prev_filter = "Timestamp >= now() - INTERVAL 2 WEEK AND Timestamp < now() - INTERVAL 1 WEEK"
    else:  # all time
        time_filter = "1=1"
        prev_filter = "1=1"  # Not meaningful for all time
    
    # Current period metrics
    current_query = f"""
        SELECT 
            quantile(0.95)(Duration / 1000000) as p95,
            quantile(0.99)(Duration / 1000000) as p99,
            stddevPop(Duration / 1000000) as std_dev,
            avg(Duration / 1000000) as avg_time
        FROM 
            otel_traces 
        WHERE 
            {time_filter}
    """
    
    # Previous period metrics (for trend)
    prev_query = f"""
        SELECT 
            avg(Duration / 1000000) as prev_avg_time
        FROM 
            otel_traces 
        WHERE 
            {prev_filter}
    """
    
    current_result = client.execute(current_query)
    prev_result = client.execute(prev_query)
    
    p95, p99, std_dev, avg_time = current_result[0]
    
    # Calculate trend
    trend_direction = "stable"
    trend_percentage = 0
    
    if prev_result and prev_result[0][0] is not None:
        prev_avg_time = prev_result[0][0]
        if prev_avg_time > 0:
            change_percentage = ((avg_time - prev_avg_time) / prev_avg_time) * 100
            trend_percentage = change_percentage
            if change_percentage > 5:
                trend_direction = "increasing"
            elif change_percentage < -5:
                trend_direction = "decreasing"
    
    return {
        'p95': p95,
        'p99': p99,
        'std_dev': std_dev,
        'avg_time': avg_time,
        'trend': {
            'direction': trend_direction,
            'percentage': trend_percentage
        }
    }

# 5. Error Table
def get_error_table(client, time_range='day'):
    """
    Get detailed error table with status codes and affected endpoints
    
    Args:
        client: ClickHouse client
        time_range: 'hour', 'day', 'week', or 'all'
    
    Returns:
        DataFrame with error details by endpoint
    """
    # Define time filter based on range
    if time_range == 'hour':
        time_filter = "Timestamp >= now() - INTERVAL 1 HOUR"
    elif time_range == 'day':
        time_filter = "Timestamp >= now() - INTERVAL 1 DAY"
    elif time_range == 'week':
        time_filter = "Timestamp >= now() - INTERVAL 1 WEEK"
    else:  # all time
        time_filter = "1=1"
    
    # Use SpanName as the endpoint and StatusCode directly
    query = f"""
        SELECT 
            StatusCode as status_code,
            SpanName as endpoint,
            COUNT(*) as error_count
        FROM 
            otel_traces 
        WHERE 
            {time_filter} AND
            StatusCode = 'STATUS_CODE_ERROR'
        GROUP BY 
            status_code, endpoint
        ORDER BY 
            error_count DESC
    """
    
    try:
        result = client.execute(query)
        df = pd.DataFrame(result, columns=['status_code', 'endpoint', 'error_count'])
    except Exception as e:
        print(f"Error in error table query: {e}")
        # Fallback to simple endpoint errors
        fallback_query = f"""
            SELECT 
                'Error' as status_code,
                SpanName as endpoint,
                COUNT(*) as error_count
            FROM 
                otel_traces 
            WHERE 
                {time_filter} AND
                StatusCode = 'STATUS_CODE_ERROR'
            GROUP BY 
                endpoint
            ORDER BY 
                error_count DESC
        """
        result = client.execute(fallback_query)
        df = pd.DataFrame(result, columns=['status_code', 'endpoint', 'error_count'])
    
    return df

# 6. Endpoints Table
def get_endpoints_table(client, time_range='day'):
    """
    Get detailed endpoint performance metrics
    
    Args:
        client: ClickHouse client
        time_range: 'hour', 'day', 'week', or 'all'
    
    Returns:
        DataFrame with endpoint performance stats
    """
    # Define time filter based on range
    if time_range == 'hour':
        time_filter = "Timestamp >= now() - INTERVAL 1 HOUR"
    elif time_range == 'day':
        time_filter = "Timestamp >= now() - INTERVAL 1 DAY"
    elif time_range == 'week':
        time_filter = "Timestamp >= now() - INTERVAL 1 WEEK"
    else:  # all time
        time_filter = "1=1"
    
    # Use SpanName as the endpoint
    query = f"""
        SELECT 
            SpanName as endpoint,
            COUNT(*) as total_requests,
            avg(Duration / 1000000) as avg_time,
            countIf(StatusCode = 'STATUS_CODE_ERROR') / COUNT(*) as error_rate,
            argMax(StatusCode, Timestamp) as last_status
        FROM 
            otel_traces 
        WHERE 
            {time_filter}
        GROUP BY 
            endpoint
        ORDER BY 
            total_requests DESC
    """
    
    result = client.execute(query)
    df = pd.DataFrame(result, columns=['endpoint', 'total_requests', 'avg_time', 'error_rate', 'last_status'])
    
    # Format error rate as percentage
    df['error_rate'] = df['error_rate'] * 100
    
    return df

def get_table_schema(client, table_name):
    """
    Helper function to get the schema of a table
    """
    query = f"DESCRIBE {table_name}"
    try:
        result = client.execute(query)
        return pd.DataFrame(result, columns=['name', 'type', 'default_type', 'default_expression'])
    except Exception as e:
        print(f"Error getting schema: {e}")
        return pd.DataFrame()

def main():
    try:
        client = get_db_connection()
        
        # Get and print schema to help debugging
        print("\n=== TABLE SCHEMA ===")
        schema = get_table_schema(client, 'otel_traces')
        print(schema)
        
        # Default time range
        time_range = 'all'
        
        # 1. Response Times Over Time
        print("\n=== RESPONSE TIMES OVER TIME ===")
        response_times_df = get_response_times_over_time(client, time_range)
        print(f"Retrieved {len(response_times_df)} data points")
        print(response_times_df.head(10))
        
        # 2. Response Time Distribution
        print("\n=== RESPONSE TIME DISTRIBUTION ===")
        distribution_df = get_response_time_distribution(client, time_range)
        print(distribution_df)
        
        # 3. Error Status Distribution
        print("\n=== ERROR STATUS DISTRIBUTION ===")
        error_dist_df = get_error_status_distribution(client, time_range)
        print(error_dist_df)
        
        # 4. Statistical Metrics
        print("\n=== STATISTICAL METRICS ===")
        stats_metrics = get_statistical_metrics(client, time_range)
        for key, value in stats_metrics.items():
            if key != 'trend':
                print(f"{key}: {value:.2f} ms")
            else:
                print(f"Trend: {value['direction']} ({value['percentage']:.2f}%)")
        
        # 5. Error Table
        print("\n=== ERROR TABLE ===")
        error_table_df = get_error_table(client, time_range)
        print(error_table_df)
        
        # 6. Endpoints Table
        print("\n=== ENDPOINTS PERFORMANCE TABLE ===")
        endpoints_df = get_endpoints_table(client, time_range)
        print(endpoints_df)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
