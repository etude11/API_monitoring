from dash import html, dcc
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta

def create_api_metrics_layout(data):
    """
    Creates the layout for API metrics visualization
    """
    # Convert API metrics to DataFrame
    api_df = pd.DataFrame(data["api_metrics"])
    api_df['timestamp'] = pd.to_datetime(api_df['timestamp'])
    
    # Get the most recent day's data
    last_day = api_df['timestamp'].max().date()
    recent_data = api_df[api_df['timestamp'].dt.date == last_day]
    
    # Calculate average metrics by endpoint for the recent data
    avg_metrics = recent_data.groupby('endpoint').agg({
        'response_time': 'mean',
        'error_rate': 'mean',
        'throughput': 'mean'
    }).reset_index()
    
    # Create response time bar chart
    response_time_fig = px.bar(
        avg_metrics,
        x='endpoint',
        y='response_time',
        title='Average Response Time by Endpoint',
        labels={'response_time': 'Response Time (ms)', 'endpoint': 'API Endpoint'},
        color='response_time',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    # Create error rate bar chart
    error_rate_fig = px.bar(
        avg_metrics,
        x='endpoint',
        y='error_rate',
        title='Error Rate by Endpoint',
        labels={'error_rate': 'Error Rate (%)', 'endpoint': 'API Endpoint'},
        color='error_rate',
        color_continuous_scale=px.colors.sequential.Reds
    )
    
    # Create throughput bar chart
    throughput_fig = px.bar(
        avg_metrics,
        x='endpoint',
        y='throughput',
        title='Throughput by Endpoint',
        labels={'throughput': 'Requests per Minute', 'endpoint': 'API Endpoint'},
        color='throughput',
        color_continuous_scale=px.colors.sequential.Blues
    )
    
    # Time series data for one selected endpoint
    default_endpoint = data["endpoints"][0]
    endpoint_data = api_df[api_df['endpoint'] == default_endpoint]
    
    time_series_fig = go.Figure()
    
    time_series_fig.add_trace(
        go.Scatter(
            x=endpoint_data['timestamp'], 
            y=endpoint_data['response_time'],
            name='Response Time (ms)'
        )
    )
    
    time_series_fig.update_layout(
        title=f'Response Time Over Time for {default_endpoint}',
        xaxis_title='Timestamp',
        yaxis_title='Response Time (ms)'
    )
    
    # Create layout
    layout = html.Div([
        html.Div([
            html.H1("API Metrics Dashboard", className="page-title"),
            
            # Overview cards
            html.Div([
                html.Div([
                    html.H3("API Performance Overview"),
                    html.Div([
                        html.Div([
                            html.H4(f"{avg_metrics['response_time'].mean():.1f} ms"),
                            html.P("Avg Response Time"),
                        ], className="summary-box response-time"),
                        html.Div([
                            html.H4(f"{avg_metrics['error_rate'].mean():.2f}%"),
                            html.P("Avg Error Rate"),
                        ], className="summary-box error-rate"),
                        html.Div([
                            html.H4(f"{avg_metrics['throughput'].mean():.0f}/min"),
                            html.P("Avg Throughput"),
                        ], className="summary-box throughput"),
                        html.Div([
                            html.H4(f"{len(data['endpoints'])}"),
                            html.P("Active Endpoints"),
                        ], className="summary-box endpoints"),
                    ], className="summary-container"),
                ], className="card full-width"),
            ], className="row"),
            
            # Filters
            html.Div([
                html.Div([
                    html.H3("Filters"),
                    html.Div([
                        html.Div([
                            html.Label("Select Endpoint:"),
                            dcc.Dropdown(
                                id='endpoint-filter',
                                options=[{'label': ep, 'value': ep} for ep in data["endpoints"]],
                                value=default_endpoint,
                                className="filter-dropdown"
                            ),
                        ], className="filter-item"),
                        
                        html.Div([
                            html.Label("Time Range:"),
                            dcc.RadioItems(
                                id='time-range',
                                options=[
                                    {'label': 'Last 24 Hours', 'value': '24h'},
                                    {'label': 'Last 3 Days', 'value': '3d'},
                                    {'label': 'Last Week', 'value': '1w'}
                                ],
                                value='24h',
                                className="radio-items"
                            ),
                        ], className="filter-item"),
                        
                        html.Button(
                            "Apply Filters", 
                            id="apply-api-filters",
                            className="filter-button"
                        ),
                    ], className="filters-container"),
                ], className="card full-width"),
            ], className="row"),
            
            # Charts Row 1
            html.Div([
                html.Div([
                    html.Div([
                        html.H3("Response Time by Endpoint"),
                        dcc.Graph(
                            id='response-time-graph',
                            figure=response_time_fig
                        ),
                    ], className="card"),
                ], className="column-left"),
                
                html.Div([
                    html.Div([
                        html.H3("Error Rate by Endpoint"),
                        dcc.Graph(
                            id='error-rate-graph',
                            figure=error_rate_fig
                        ),
                    ], className="card"),
                ], className="column-right"),
            ], className="row"),
            
            # Charts Row 2
            html.Div([
                html.Div([
                    html.Div([
                        html.H3("Throughput by Endpoint"),
                        dcc.Graph(
                            id='throughput-graph',
                            figure=throughput_fig
                        ),
                    ], className="card"),
                ], className="column-left"),
                
                html.Div([
                    html.Div([
                        html.H3("Response Time Trend"),
                        dcc.Graph(
                            id='time-series-graph',
                            figure=time_series_fig
                        ),
                    ], className="card"),
                ], className="column-right"),
            ], className="row"),
        ], className="dashboard-container"),
    ])
    
    return layout
