from dash import html, dcc, dash_table
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from collections import Counter

def create_log_ingestion_layout(data):
    """
    Creates the layout for log ingestion visualization
    """
    # Convert logs to DataFrame for easier manipulation
    logs_df = pd.DataFrame(data["logs"])
    
    # Add date column extracted from timestamp
    logs_df['date'] = pd.to_datetime(logs_df['timestamp']).dt.date
    
    # Count logs by date and severity
    logs_by_date = logs_df.groupby(['date', 'severity']).size().reset_index(name='count')
    
    # Create bar chart of logs by severity over time
    log_volume_fig = px.bar(
        logs_by_date,
        x='date',
        y='count',
        color='severity',
        title='Log Volume by Severity',
        labels={'count': 'Number of Logs', 'date': 'Date'},
        color_discrete_map={
            'INFO': '#4CAF50',  # Green
            'WARNING': '#FF9800',  # Orange
            'ERROR': '#F44336',  # Red
            'CRITICAL': '#9C27B0'  # Purple
        }
    )
    
    # Count logs by endpoint
    logs_by_endpoint = logs_df.groupby('endpoint').size().reset_index(name='count')
    logs_by_endpoint = logs_by_endpoint.sort_values('count', ascending=False)
    
    endpoint_fig = px.bar(
        logs_by_endpoint,
        x='count',
        y='endpoint',
        orientation='h',
        title='Log Volume by Endpoint',
        labels={'count': 'Number of Logs', 'endpoint': 'API Endpoint'}
    )
    
    # Create filterable data table for logs
    table = dash_table.DataTable(
        id='log-table',
        columns=[
            {"name": "Timestamp", "id": "timestamp"},
            {"name": "Severity", "id": "severity"},
            {"name": "Endpoint", "id": "endpoint"},
            {"name": "User ID", "id": "user_id"},
            {"name": "Message", "id": "message"}
        ],
        data=logs_df.tail(100).to_dict('records'),
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'minWidth': '100px',
            'maxWidth': '300px',
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_header={
            'backgroundColor': 'rgb(240, 240, 240)',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{severity} = "ERROR"'},
                'backgroundColor': 'rgba(255, 0, 0, 0.1)',
            },
            {
                'if': {'filter_query': '{severity} = "CRITICAL"'},
                'backgroundColor': 'rgba(139, 0, 139, 0.1)',
                'color': 'darkred',
                'fontWeight': 'bold'
            },
            {
                'if': {'filter_query': '{severity} = "WARNING"'},
                'backgroundColor': 'rgba(255, 165, 0, 0.1)',
            }
        ],
        filter_action="native",
        sort_action="native",
    )
    
    # Create layout
    layout = html.Div([
        html.Div([
            html.H1("Log Ingestion Dashboard", className="page-title"),
            
            html.Div([
                html.Div([
                    html.Div([
                        html.H3("Log Volume Over Time"),
                        html.Div([
                            html.Label("Filter by Severity:"),
                            dcc.Dropdown(
                                id='severity-filter',
                                options=[{'label': sev, 'value': sev} for sev in data["severity_levels"]],
                                multi=True,
                                value=data["severity_levels"],
                                className="filter-dropdown"
                            ),
                        ], className="filter-container"),
                        dcc.Graph(
                            id='log-volume-graph',
                            figure=log_volume_fig
                        ),
                    ], className="card"),
                ], className="column-left"),
                
                html.Div([
                    html.Div([
                        html.H3("Logs by Endpoint"),
                        dcc.Graph(
                            id='endpoint-distribution-graph',
                            figure=endpoint_fig
                        ),
                    ], className="card"),
                ], className="column-right"),
            ], className="row"),
            
            html.Div([
                html.Div([
                    html.H3("Recent Logs"),
                    html.Div([
                        html.Label("Search Logs:"),
                        dcc.Input(
                            id="log-search",
                            type="text",
                            placeholder="Search log messages...",
                            className="search-box"
                        ),
                    ], className="search-container"),
                    table,
                ], className="card full-width"),
            ], className="row"),
        ], className="dashboard-container"),
    ])
    
    return layout
