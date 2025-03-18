from dash import html, dcc, dash_table
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime

def create_log_classification_layout(data):
    """
    Creates the layout for log classification visualization
    """
    # Convert logs to DataFrame for easier manipulation
    logs_df = pd.DataFrame(data["logs"])
    
    # Classification distribution
    classification_counts = logs_df['log_class'].value_counts().reset_index()
    classification_counts.columns = ['Class', 'Count']
    
    class_fig = px.pie(
        classification_counts,
        names='Class',
        values='Count',
        title='Log Classification Distribution',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Classification by severity
    class_by_severity = pd.crosstab(logs_df['log_class'], logs_df['severity'])
    class_by_severity_fig = px.bar(
        class_by_severity,
        title='Log Classification by Severity',
        barmode='stack',
        color_discrete_map={
            'INFO': '#4CAF50',
            'WARNING': '#FF9800',
            'ERROR': '#F44336',
            'CRITICAL': '#9C27B0'
        }
    )
    
    # Create filterable data table for logs with classification
    table = dash_table.DataTable(
        id='classification-table',
        columns=[
            {"name": "Timestamp", "id": "timestamp"},
            {"name": "Classification", "id": "log_class"},
            {"name": "Severity", "id": "severity"},
            {"name": "Endpoint", "id": "endpoint"},
            {"name": "Message", "id": "message"}
        ],
        data=logs_df.to_dict('records'),
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
            html.H1("Log Classification Dashboard", className="page-title"),
            
            html.Div([
                html.Div([
                    html.Div([
                        html.H3("Log Classification Distribution"),
                        dcc.Graph(
                            id='classification-pie-chart',
                            figure=class_fig
                        ),
                    ], className="card"),
                ], className="column-left"),
                
                html.Div([
                    html.Div([
                        html.H3("Classification by Severity"),
                        dcc.Graph(
                            id='class-severity-chart',
                            figure=class_by_severity_fig
                        ),
                    ], className="card"),
                ], className="column-right"),
            ], className="row"),
            
            html.Div([
                html.Div([
                    html.H3("Log Classification Filters"),
                    html.Div([
                        html.Div([
                            html.Label("Filter by Class:"),
                            dcc.Dropdown(
                                id='class-filter',
                                options=[{'label': cls, 'value': cls} for cls in data["log_classes"]],
                                multi=True,
                                value=[],
                                className="filter-dropdown"
                            ),
                        ], className="filter-item"),
                        
                        html.Div([
                            html.Label("Filter by Severity:"),
                            dcc.Dropdown(
                                id='severity-class-filter',
                                options=[{'label': sev, 'value': sev} for sev in data["severity_levels"]],
                                multi=True,
                                value=[],
                                className="filter-dropdown"
                            ),
                        ], className="filter-item"),
                        
                        html.Div([
                            html.Label("Date Range:"),
                            dcc.DatePickerRange(
                                id='date-range',
                                start_date=datetime.now().date(),
                                end_date=datetime.now().date(),
                                className="date-picker"
                            ),
                        ], className="filter-item"),
                        
                        html.Button(
                            "Apply Filters",
                            id="apply-class-filters",
                            className="filter-button"
                        ),
                    ], className="filters-container"),
                ], className="card full-width"),
            ], className="row"),
            
            html.Div([
                html.Div([
                    html.H3("Classified Logs"),
                    table,
                ], className="card full-width"),
            ], className="row"),
        ], className="dashboard-container"),
    ])
    
    return layout
