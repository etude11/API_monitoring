from dash import html, dcc, dash_table
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd

def create_error_detection_layout(data):
    """
    Creates the layout for error detection visualization
    """
    # Convert logs to DataFrame for easier manipulation
    logs_df = pd.DataFrame(data["logs"])
    
    # Filter for errors and critical logs
    error_logs = logs_df[logs_df['severity'].isin(['ERROR', 'CRITICAL'])]
    error_logs['date'] = pd.to_datetime(error_logs['timestamp']).dt.date
    
    # Count errors by date
    errors_by_date = error_logs.groupby(['date', 'severity']).size().reset_index(name='count')
    
    # Create line chart of errors over time
    error_trend_fig = px.line(
        errors_by_date,
        x='date',
        y='count',
        color='severity',
        title='Error Trends Over Time',
        labels={'count': 'Number of Errors', 'date': 'Date'},
        color_discrete_map={
            'ERROR': '#F44336',  # Red
            'CRITICAL': '#9C27B0'  # Purple
        }
    )
    
    # Count errors by endpoint
    errors_by_endpoint = error_logs.groupby(['endpoint', 'severity']).size().reset_index(name='count')
    errors_by_endpoint = errors_by_endpoint.sort_values('count', ascending=False)
    
    endpoint_error_fig = px.bar(
        errors_by_endpoint,
        x='endpoint',
        y='count',
        color='severity',
        title='Errors by Endpoint',
        labels={'count': 'Number of Errors', 'endpoint': 'API Endpoint'},
        color_discrete_map={
            'ERROR': '#F44336',  # Red
            'CRITICAL': '#9C27B0'  # Purple
        }
    )
    
    # Create table for error logs
    error_table = dash_table.DataTable(
        id='error-table',
        columns=[
            {"name": "Timestamp", "id": "timestamp"},
            {"name": "Severity", "id": "severity"},
            {"name": "Endpoint", "id": "endpoint"},
            {"name": "User ID", "id": "user_id"},
            {"name": "Message", "id": "message"}
        ],
        data=error_logs.to_dict('records'),
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
            }
        ],
        filter_action="native",
        sort_action="native",
    )
    
    # Create layout
    layout = html.Div([
        html.Div([
            html.H1("Error Detection Dashboard", className="page-title"),
            
            # Summary cards
            html.Div([
                html.Div([
                    html.H3("Error Summary"),
                    html.Div([
                        html.Div([
                            html.H4(f"{len(error_logs[error_logs['severity'] == 'ERROR'])}"),
                            html.P("Errors"),
                        ], className="summary-box error"),
                        html.Div([
                            html.H4(f"{len(error_logs[error_logs['severity'] == 'CRITICAL'])}"),
                            html.P("Critical"),
                        ], className="summary-box critical"),
                        html.Div([
                            html.H4(f"{len(error_logs['endpoint'].unique())}"),
                            html.P("Affected Endpoints"),
                        ], className="summary-box endpoints"),
                    ], className="summary-container"),
                ], className="card full-width"),
            ], className="row"),
            
            html.Div([
                html.Div([
                    html.Div([
                        html.H3("Error Trends"),
                        dcc.Graph(
                            id='error-trend-graph',
                            figure=error_trend_fig
                        ),
                    ], className="card"),
                ], className="column-left"),
                
                html.Div([
                    html.Div([
                        html.H3("Errors by Endpoint"),
                        dcc.Graph(
                            id='endpoint-error-graph',
                            figure=endpoint_error_fig
                        ),
                    ], className="card"),
                ], className="column-right"),
            ], className="row"),
            
            html.Div([
                html.Div([
                    html.H3("Error Logs"),
                    html.Div([
                        html.Label("Filter Errors:"),
                        dcc.Dropdown(
                            id='error-severity-filter',
                            options=[
                                {'label': 'All Errors', 'value': 'all'},
                                {'label': 'Errors Only', 'value': 'ERROR'},
                                {'label': 'Critical Only', 'value': 'CRITICAL'}
                            ],
                            value='all',
                            className="filter-dropdown-inline"
                        ),
                        html.Label("Filter by Endpoint:"),
                        dcc.Dropdown(
                            id='error-endpoint-filter',
                            options=[{'label': ep, 'value': ep} for ep in data["endpoints"]],
                            multi=True,
                            value=[],
                            className="filter-dropdown-inline"
                        ),
                    ], className="filters-inline"),
                    error_table,
                ], className="card full-width"),
            ], className="row"),
        ], className="dashboard-container"),
    ])
    
    return layout
