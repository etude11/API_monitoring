import time
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from clickhouse_driver import Client
from typing import List, Dict, Any, Callable, Optional


class LogAnalyzer:
    """
    Analyzes log data from ClickHouse database and streams analysis results.
    """
    def __init__(self, 
                 host: str = '10.1.101.196',
                 port: int = 9000, 
                 user: str = 'default', 
                 password: str = '',
                 database: str = 'default',
                 poll_interval: int = 10):
        """
        Initialize the log analyzer with database connection details.
        
        Args:
            host: ClickHouse server host
            port: ClickHouse server port
            user: Username for ClickHouse
            password: Password for ClickHouse
            database: ClickHouse database name
            poll_interval: How often to poll for new data (in seconds)
        """
        self.client = Client(host=host, port=port, user=user, password=password, database=database)
        self.poll_interval = poll_interval
        self.last_fetch_time = datetime.now() - timedelta(hours=1)  # Start with data from last hour
        self.callbacks = []
        
    def register_callback(self, callback: Callable[[str, Any], None]) -> None:
        """
        Register a callback function to receive analysis results.
        
        Args:
            callback: Function that takes (analysis_name, analysis_result) parameters
        """
        self.callbacks.append(callback)
        
    def _notify_callbacks(self, analysis_name: str, result: Any) -> None:
        """Notify all registered callbacks with new results"""
        for callback in self.callbacks:
            callback(analysis_name, result)
    
    def get_traces(self, time_from: Optional[datetime] = None) -> pd.DataFrame:
        """
        Fetch trace data from ClickHouse.
        
        Args:
            time_from: Fetch traces from this time onwards (optional)
            
        Returns:
            DataFrame with trace data
        """
        query = f"""
        SELECT Timestamp, TraceId, SpanId, SpanName, ServiceName, Duration, StatusCode, StatusMessage
        FROM otel_traces 
        WHERE Timestamp >= '{time_from.isoformat() if time_from else self.last_fetch_time.isoformat()}'
        ORDER BY Timestamp
        """
        result = self.client.execute(query)
        
        if not result:
            return pd.DataFrame()
        
        df = pd.DataFrame(result, columns=[
            'Timestamp', 'TraceId', 'SpanId', 'SpanName', 'ServiceName', 
            'Duration', 'StatusCode', 'StatusMessage'
        ])
        
        # Convert timestamp to datetime
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        # Convert duration from nanoseconds to milliseconds
        df['Duration'] = df['Duration'] / 1_000_000
        
        return df
    
    def get_logs(self, time_from: Optional[datetime] = None) -> pd.DataFrame:
        """
        Fetch log data from ClickHouse.
        
        Args:
            time_from: Fetch logs from this time onwards (optional)
            
        Returns:
            DataFrame with log data
        """
        query = f"""
        SELECT Timestamp, TraceId, SpanId, ServiceName, Body, SeverityText
        FROM otel_logs
        WHERE Timestamp >= '{time_from.isoformat() if time_from else self.last_fetch_time.isoformat()}'
        ORDER BY Timestamp
        """
        result = self.client.execute(query)
        
        if not result:
            return pd.DataFrame()
        
        df = pd.DataFrame(result, columns=[
            'Timestamp', 'TraceId', 'SpanId', 'ServiceName', 'Body', 'SeverityText'
        ])
        
        # Convert timestamp to datetime
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        return df
    
    def get_metrics(self, time_from: Optional[datetime] = None) -> Dict[str, pd.DataFrame]:
        """
        Fetch metric data from ClickHouse.
        
        Args:
            time_from: Fetch metrics from this time onwards (optional)
            
        Returns:
            Dictionary with DataFrames for different metric types
        """
        metrics = {}
        
        # Get histogram metrics
        query = f"""
        SELECT TimeUnix, ServiceName, MetricName, Sum, Count, Min, Max, Attributes
        FROM otel_metrics_histogram
        WHERE TimeUnix >= '{time_from.isoformat() if time_from else self.last_fetch_time.isoformat()}'
        ORDER BY TimeUnix
        """
        result = self.client.execute(query)
        
        if result:
            metrics['histogram'] = pd.DataFrame(result, columns=[
                'TimeUnix', 'ServiceName', 'MetricName', 'Sum', 'Count', 'Min', 'Max', 'Attributes'
            ])
            metrics['histogram']['TimeUnix'] = pd.to_datetime(metrics['histogram']['TimeUnix'])
        
        # Get gauge metrics
        query = f"""
        SELECT TimeUnix, ServiceName, MetricName, Value, Attributes
        FROM otel_metrics_gauge
        WHERE TimeUnix >= '{time_from.isoformat() if time_from else self.last_fetch_time.isoformat()}'
        ORDER BY TimeUnix
        """
        result = self.client.execute(query)
        
        if result:
            metrics['gauge'] = pd.DataFrame(result, columns=[
                'TimeUnix', 'ServiceName', 'MetricName', 'Value', 'Attributes'
            ])
            metrics['gauge']['TimeUnix'] = pd.to_datetime(metrics['gauge']['TimeUnix'])
        
        # Get sum metrics
        query = f"""
        SELECT TimeUnix, ServiceName, MetricName, Value, Attributes
        FROM otel_metrics_sum
        WHERE TimeUnix >= '{time_from.isoformat() if time_from else self.last_fetch_time.isoformat()}'
        ORDER BY TimeUnix
        """
        result = self.client.execute(query)
        
        if result:
            metrics['sum'] = pd.DataFrame(result, columns=[
                'TimeUnix', 'ServiceName', 'MetricName', 'Value', 'Attributes'
            ])
            metrics['sum']['TimeUnix'] = pd.to_datetime(metrics['sum']['TimeUnix'])
        
        return metrics

    # Analysis Functions
    
    def analyze_response_time(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze response times from trace data.
        
        Args:
            df: DataFrame containing trace data
            
        Returns:
            Dictionary with response time analysis
        """
        if df.empty:
            return {'data': [], 'avg': 0, 'max': 0, 'min': 0}
        
        # Group by timestamp (rounded to minute) and calculate average response time
        df['TimestampMinute'] = df['Timestamp'].dt.floor('min')
        response_times = df.groupby('TimestampMinute').agg(
            avg_duration=('Duration', 'mean'),
            max_duration=('Duration', 'max'),
            min_duration=('Duration', 'min'),
            count=('Duration', 'count')
        ).reset_index()
        
        result = {
            'data': response_times.to_dict('records'),
            'avg': df['Duration'].mean(),
            'max': df['Duration'].max(),
            'min': df['Duration'].min(),
            'p95': df['Duration'].quantile(0.95),
            'p99': df['Duration'].quantile(0.99),
        }
        
        return result
    
    def analyze_error_rate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze error rates from trace data.
        
        Args:
            df: DataFrame containing trace data
            
        Returns:
            Dictionary with error rate analysis
        """
        if df.empty:
            return {'data': [], 'error_rate': 0, 'total_requests': 0, 'total_errors': 0}
        
        # Consider status code other than Unset or OK as errors
        # (Depending on your data, you might need to adjust this logic)
        df['IsError'] = df['StatusCode'].apply(lambda x: 0 if x in ['Unset', 'OK'] else 1)
        
        # Group by timestamp (rounded to minute) and calculate error rate
        df['TimestampMinute'] = df['Timestamp'].dt.floor('min')
        error_rates = df.groupby('TimestampMinute').agg(
            error_count=('IsError', 'sum'),
            total_count=('IsError', 'count'),
        ).reset_index()
        
        error_rates['error_rate'] = error_rates['error_count'] / error_rates['total_count'] * 100
        
        total_requests = len(df)
        total_errors = df['IsError'].sum()
        
        result = {
            'data': error_rates.to_dict('records'),
            'error_rate': (total_errors / total_requests * 100) if total_requests > 0 else 0,
            'total_requests': total_requests,
            'total_errors': total_errors,
        }
        
        return result
    
    def analyze_request_volume(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze request volume from trace data.
        
        Args:
            df: DataFrame containing trace data
            
        Returns:
            Dictionary with request volume analysis
        """
        if df.empty:
            return {'data': [], 'total_requests': 0, 'req_per_minute': 0}
        
        # Group by timestamp (rounded to minute) and count requests
        df['TimestampMinute'] = df['Timestamp'].dt.floor('min')
        volume = df.groupby('TimestampMinute').size().reset_index(name='count')
        
        # Calculate requests per minute
        time_range = (df['Timestamp'].max() - df['Timestamp'].min()).total_seconds() / 60
        req_per_minute = len(df) / time_range if time_range > 0 else 0
        
        result = {
            'data': volume.to_dict('records'),
            'total_requests': len(df),
            'req_per_minute': req_per_minute,
        }
        
        return result
    
    def analyze_service_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze performance by service from trace data.
        
        Args:
            df: DataFrame containing trace data
            
        Returns:
            Dictionary with service performance analysis
        """
        if df.empty:
            return {'data': []}
        
        # Group by service and calculate stats
        service_perf = df.groupby('ServiceName').agg(
            avg_duration=('Duration', 'mean'),
            max_duration=('Duration', 'max'),
            min_duration=('Duration', 'min'),
            count=('Duration', 'count'),
            p95=('Duration', lambda x: x.quantile(0.95)),
        ).reset_index()
        
        result = {
            'data': service_perf.to_dict('records'),
        }
        
        return result
    
    async def stream_analysis(self) -> None:
        """
        Continuously poll for new data and stream analysis results.
        """
        while True:
            try:
                # Get data since last fetch
                traces_df = self.get_traces()
                logs_df = self.get_logs()
                metrics = self.get_metrics()
                
                # Update last fetch time
                self.last_fetch_time = datetime.now()
                
                if not traces_df.empty:
                    # Perform analyses
                    response_time_analysis = self.analyze_response_time(traces_df)
                    error_rate_analysis = self.analyze_error_rate(traces_df)
                    request_volume_analysis = self.analyze_request_volume(traces_df)
                    service_performance_analysis = self.analyze_service_performance(traces_df)
                    
                    # Notify callbacks with results
                    self._notify_callbacks('response_time', response_time_analysis)
                    self._notify_callbacks('error_rate', error_rate_analysis)
                    self._notify_callbacks('request_volume', request_volume_analysis)
                    self._notify_callbacks('service_performance', service_performance_analysis)
                    
                # Sleep until next polling interval
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                print(f"Error during analysis: {e}")
                await asyncio.sleep(self.poll_interval)
    
    def start_streaming(self) -> None:
        """
        Start streaming analysis results in a separate thread.
        """
        loop = asyncio.get_event_loop()
        loop.create_task(self.stream_analysis())
        loop.run_forever()


# Helper functions for direct usage
def print_callback(analysis_name: str, result: Any) -> None:
    """Simple callback that prints analysis results"""
    print(f"[{datetime.now()}] New {analysis_name} analysis:")
    print(result)
    print("-" * 50)


if __name__ == "__main__":
    # Example usage
    analyzer = LogAnalyzer(poll_interval=15)  # Poll every 15 seconds
    analyzer.register_callback(print_callback)
    print("Starting analysis stream...")
    analyzer.start_streaming()
