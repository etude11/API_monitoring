from dash import Input, Output, State, callback_context
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime, timedelta

def register_callbacks(app, mock_data):
    # Convert to DataFrame for easier manipulation
    logs_df = pd.DataFrame(mock_data["logs"])
    logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp'])
    logs_df['date'] = logs_df['timestamp'].dt.date
    
    api_df = pd.DataFrame(mock_data["api_metrics"])
    api_df['timestamp'] = pd.to_datetime(api_df['timestamp'])
    
    infra_df = pd.DataFrame(mock_data["infra_metrics"])
    infra_df['timestamp'] = pd.to_datetime(infra_df['timestamp'])
    
    alerts_df = pd.DataFrame(mock_data["alerts"])
    alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'])
    
    # Log Ingestion callbacks
    @app.callback(
        Output("log-volume-graph", "figure"),
        [Input("severity-filter", "value")]
    )
    def update_log_volume_chart(selected_severities):
        if not selected_severities:
            selected_severities = mock_data["severity_levels"]
            
        filtered_logs = logs_df[logs_df['severity'].isin(selected_severities)]
        logs_by_date = filtered_logs.groupby(['date', 'severity']).size().reset_index(name='count')
        
        fig = px.bar(
            logs_by_date,
            x='date',
            y='count',
            color='severity',
            title='Log Volume by Severity',
            labels={'count': 'Number of Logs', 'date': 'Date'},
            color_discrete_map={
                'INFO': '#4CAF50',
                'WARNING': '#FF9800',
                'ERROR': '#F44336',
                'CRITICAL': '#9C27B0'
            }
        )
        
        return fig
    
    # Log table search filter
    @app.callback(
        Output("log-table", "data"),
        [Input("log-search", "value")]
    )
    def filter_log_table(search_term):
        if not search_term:
            return logs_df.tail(100).to_dict('records')
            
        filtered_df = logs_df[
            logs_df['message'].str.contains(search_term, case=False) | 
            logs_df['endpoint'].str.contains(search_term, case=False) |
            logs_df['user_id'].str.contains(search_term, case=False)
        ]
        
        return filtered_df.tail(100).to_dict('records')
    
    # Log Classification callbacks
    @app.callback(
        Output("classification-table", "data"),
        [Input("apply-class-filters", "n_clicks")],
        [
            State("class-filter", "value"),
            State("severity-class-filter", "value"),
            State("date-range", "start_date"),
            State("date-range", "end_date")
        ]
    )
    def filter_classification_table(n_clicks, classes, severities, start_date, end_date):
        filtered_df = logs_df.copy()
        
        if classes and len(classes) > 0:
            filtered_df = filtered_df[filtered_df['log_class'].isin(classes)]
            
        if severities and len(severities) > 0:
            filtered_df = filtered_df[filtered_df['severity'].isin(severities)]
            
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            filtered_df = filtered_df[
                (filtered_df['timestamp'].dt.date >= start_date) & 
                (filtered_df['timestamp'].dt.date <= end_date)
            ]
            
        return filtered_df.to_dict('records')
    
    # Error detection callbacks
    @app.callback(
        Output("error-table", "data"),
        [
            Input("error-severity-filter", "value"),
            Input("error-endpoint-filter", "value")
        ]
    )
    def filter_error_table(severity, endpoints):
        # Start with all error and critical logs
        filtered_df = logs_df[logs_df['severity'].isin(['ERROR', 'CRITICAL'])]
        
        # Filter by severity if not 'all'
        if severity != 'all':
            filtered_df = filtered_df[filtered_df['severity'] == severity]
            
        # Filter by endpoints if any selected
        if endpoints and len(endpoints) > 0:
            filtered_df = filtered_df[filtered_df['endpoint'].isin(endpoints)]
            
        return filtered_df.to_dict('records')
    
    # API Metrics callbacks
    @app.callback(
        [
            Output("time-series-graph", "figure"),
            Output("response-time-graph", "figure"),
            Output("error-rate-graph", "figure"),
            Output("throughput-graph", "figure")
        ],
        [Input("apply-api-filters", "n_clicks")],
        [
            State("endpoint-filter", "value"),
            State("time-range", "value")
        ]
    )
    def update_api_metrics(n_clicks, selected_endpoint, time_range):
        # Filter by time range
        now = datetime.now()
        if time_range == '24h':
            start_time = now - timedelta(days=1)
        elif time_range == '3d':
            start_time = now - timedelta(days=3)
        else:  # 1w
            start_time = now - timedelta(weeks=1)
            
        filtered_df = api_df[api_df['timestamp'] >= start_time]
        
        # Create endpoint data for time series
        endpoint_data = filtered_df[filtered_df['endpoint'] == selected_endpoint]
        
        # Time series chart
        time_series_fig = go.Figure()
        time_series_fig.add_trace(
            go.Scatter(
                x=endpoint_data['timestamp'], 
                y=endpoint_data['response_time'],
                name='Response Time (ms)'
            )
        )
        time_series_fig.update_layout(
            title=f'Response Time Over Time for {selected_endpoint}',
            xaxis_title='Timestamp',
            yaxis_title='Response Time (ms)'
        )
        
        # Calculate average metrics for bar charts
        avg_metrics = filtered_df.groupby('endpoint').agg({
            'response_time': 'mean',
            'error_rate': 'mean',
            'throughput': 'mean'
        }).reset_index()
        
        # Bar charts
        response_time_fig = px.bar(
            avg_metrics,
            x='endpoint',
            y='response_time',
            title='Average Response Time by Endpoint',
            labels={'response_time': 'Response Time (ms)', 'endpoint': 'API Endpoint'},
            color='response_time',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        error_rate_fig = px.bar(
            avg_metrics,
            x='endpoint',
            y='error_rate',
            title='Error Rate by Endpoint',
            labels={'error_rate': 'Error Rate (%)', 'endpoint': 'API Endpoint'},
            color='error_rate',
            color_continuous_scale=px.colors.sequential.Reds
        )
        
        throughput_fig = px.bar(
            avg_metrics,
            x='endpoint',
            y='throughput',
            title='Throughput by Endpoint',
            labels={'throughput': 'Requests per Minute', 'endpoint': 'API Endpoint'},
            color='throughput',
            color_continuous_scale=px.colors.sequential.Blues
        )
        
        return time_series_fig, response_time_fig, error_rate_fig, throughput_fig
    
    # Infrastructure monitoring callbacks
    @app.callback(
        [
            Output("cpu-trend-graph", "figure"),
            Output("memory-trend-graph", "figure"),
            Output("disk-trend-graph", "figure"),
            Output("network-trend-graph", "figure")
        ],
        [
            Input("server-selector", "value"),
            Input("time-range", "value")
        ]
    )
    def update_infra_metrics(selected_server, time_range):
        # Filter by time range
        now = datetime.now()
        if time_range == '24h':
            start_time = now - timedelta(days=1)
        elif time_range == '3d':
            start_time = now - timedelta(days=3)
        else:  # 1w
            start_time = now - timedelta(weeks=1)
            
        filtered_df = infra_df[infra_df['timestamp'] >= start_time]
        
        # Filter by server
        server_data = filtered_df[filtered_df['server'] == selected_server].sort_values('timestamp')
        
        # CPU Usage over time
        cpu_fig = px.line(
            server_data,
            x='timestamp',
            y='cpu_usage',
            title=f'CPU Usage Over Time - {selected_server}',
            labels={'cpu_usage': 'CPU Usage (%)', 'timestamp': 'Time'}
        )
        
        # Memory Usage over time
        memory_fig = px.line(
            server_data,
            x='timestamp',
            y='memory_usage',
            title=f'Memory Usage Over Time - {selected_server}',
            labels={'memory_usage': 'Memory Usage (%)', 'timestamp': 'Time'}
        )
        
        # Disk Usage over time
        disk_fig = px.line(
            server_data,
            x='timestamp',
            y='disk_usage',
            title=f'Disk Usage Over Time - {selected_server}',
            labels={'disk_usage': 'Disk Usage (%)', 'timestamp': 'Time'}
        )
        
        # Network IO over time
        network_fig = go.Figure()
        
        network_fig.add_trace(
            go.Scatter(
                x=server_data['timestamp'],
                y=server_data['network_in'],
                name='Network In (Mbps)'
            )
        )
        
        network_fig.add_trace(
            go.Scatter(
                x=server_data['timestamp'],
                y=server_data['network_out'],
                name='Network Out (Mbps)'
            )
        )
        
        network_fig.update_layout(
            title=f'Network I/O Over Time - {selected_server}',
            xaxis_title='Time',
            yaxis_title='Network Traffic (Mbps)'
        )
        
        return cpu_fig, memory_fig, disk_fig, network_fig
    
    # User activity callbacks
    @app.callback(
        Output("suspicious-table", "data"),
        [Input("apply-reason-filters", "n_clicks")],
        [State("reason-filter", "value")]
    )
    def filter_suspicious_activities(n_clicks, reasons):
        activity_df = pd.DataFrame(mock_data["user_activities"])
        suspicious_df = activity_df[activity_df['is_suspicious'] == True]
        
        if not reasons or len(reasons) == 0:
            return suspicious_df.to_dict('records')
            
        filtered_df = suspicious_df[suspicious_df['reason'].isin(reasons)]
        return filtered_df.to_dict('records')
    
    # Alert management callbacks
    @app.callback(
        Output("alerts-table", "data"),
        [Input("apply-alert-filters", "n_clicks")],
        [
            State("status-filter", "value"),
            State("priority-filter", "value")
        ]
    )
    def filter_alerts(n_clicks, status, priority):
        filtered_df = alerts_df.copy()
        
        if status != 'all':
            filtered_df = filtered_df[filtered_df['status'] == status]
            
        if priority != 'all':
            filtered_df = filtered_df[filtered_df['priority'] == priority]
            
        return filtered_df.to_dict('records')
    
    # Placeholder callbacks for alert management buttons
    @app.callback(
        Output("alerts-status-chart", "figure"),  # We'll update the status chart as output
        [
            Input("acknowledge-button", "n_clicks"),
            Input("resolve-button", "n_clicks")
        ],
        [State("alerts-table", "derived_virtual_selected_rows")]
    )
    def handle_alert_actions(ack_clicks, resolve_clicks, selected_rows):
        # This is just a placeholder function that would be replaced
        # with real backend logic in the actual implementation
        
        # Just return the current chart - in a real application this would update the data
        alerts_by_status = alerts_df['status'].value_counts().reset_index()
        alerts_by_status.columns = ['Status', 'Count']
        
        alerts_status_fig = px.bar(
            alerts_by_status,
            x='Status',
            y='Count',
            title='Alert Distribution by Status',
            color='Status',
            color_discrete_map={
                'active': '#F44336',
                'acknowledged': '#FF9800',
                'resolved': '#4CAF50'
            }
        )
        
        return alerts_status_fig
