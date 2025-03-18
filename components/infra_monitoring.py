from dash import html, dcc
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd

def create_infrastructure_monitoring_layout(data):
    """
    Creates the layout for infrastructure monitoring visualization
    """
    # Convert infrastructure metrics to DataFrame
    infra_df = pd.DataFrame(data["infra_metrics"])
    infra_df['timestamp'] = pd.to_datetime(infra_df['timestamp'])
    
    # Get the most recent data
    last_timestamp = infra_df['timestamp'].max()
    recent_data = infra_df[infra_df['timestamp'] == last_timestamp]
    
    # Create CPU usage gauge charts
    cpu_gauges = []
    
    for server in data["servers"]:
        server_data = recent_data[recent_data['server'] == server]
        if not server_data.empty:
            cpu_value = server_data['cpu_usage'].values[0]
            
            gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=cpu_value,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': server},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#1f77b4"},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgreen"},
                        {'range': [60, 80], 'color': "lightyellow"},
                        {'range': [80, 100], 'color': "lightcoral"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            gauge.update_layout(height=200, margin=dict(l=10, r=10, t=50, b=10))
            
            cpu_gauges.append(
                html.Div([
                    dcc.Graph(figure=gauge, config={'displayModeBar': False})
                ], className="gauge-chart")
            )
    
    # Create time series for a selected server
    default_server = data["servers"][0]
    server_data = infra_df[infra_df['server'] == default_server].sort_values('timestamp')
    
    # CPU Usage over time
    cpu_fig = px.line(
        server_data,
        x='timestamp',
        y='cpu_usage',
        title=f'CPU Usage Over Time - {default_server}',
        labels={'cpu_usage': 'CPU Usage (%)', 'timestamp': 'Time'}
    )
    
    # Memory Usage over time
    memory_fig = px.line(
        server_data,
        x='timestamp',
        y='memory_usage',
        title=f'Memory Usage Over Time - {default_server}',
        labels={'memory_usage': 'Memory Usage (%)', 'timestamp': 'Time'}
    )
    
    # Disk Usage over time
    disk_fig = px.line(
        server_data,
        x='timestamp',
        y='disk_usage',
        title=f'Disk Usage Over Time - {default_server}',
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
        title=f'Network I/O Over Time - {default_server}',
        xaxis_title='Time',
        yaxis_title='Network Traffic (Mbps)'
    )
    
    # Create layout
    layout = html.Div([
        html.Div([
            html.H1("Infrastructure Monitoring Dashboard", className="page-title"),
            
            # Server selector
            html.Div([
                html.Div([
                    html.H3("Server Selection"),
                    html.Div([
                        html.Label("Select Server:"),
                        dcc.Dropdown(
                            id='server-selector',
                            options=[{'label': server, 'value': server} for server in data["servers"]],
                            value=default_server,
                            className="filter-dropdown"
                        ),
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
                    ], className="filters-container"),
                ], className="card full-width"),
            ], className="row"),
            
            # CPU Usage Gauges
            html.Div([
                html.Div([
                    html.H3("CPU Usage by Server"),
                    html.Div(cpu_gauges, className="gauges-container"),
                ], className="card full-width"),
            ], className="row"),
            
            # Resource usage charts
            html.Div([
                html.Div([
                    html.Div([
                        html.H3("CPU Usage Trend"),
                        dcc.Graph(
                            id='cpu-trend-graph',
                            figure=cpu_fig
                        ),
                    ], className="card"),
                ], className="column-left"),
                
                html.Div([
                    html.Div([
                        html.H3("Memory Usage Trend"),
                        dcc.Graph(
                            id='memory-trend-graph',
                            figure=memory_fig
                        ),
                    ], className="card"),
                ], className="column-right"),
            ], className="row"),
            
            html.Div([
                html.Div([
                    html.Div([
                        html.H3("Disk Usage Trend"),
                        dcc.Graph(
                            id='disk-trend-graph',
                            figure=disk_fig
                        ),
                    ], className="card"),
                ], className="column-left"),
                
                html.Div([
                    html.Div([
                        html.H3("Network I/O Trend"),
                        dcc.Graph(
                            id='network-trend-graph',
                            figure=network_fig
                        ),
                    ], className="card"),
                ], className="column-right"),
            ], className="row"),
        ], className="dashboard-container"),
    ])
    
    return layout
