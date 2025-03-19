from dash import html, dcc, dash_table
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd

def create_alerts_layout(data):
    """
    Creates the layout for alerts visualization
    """
    # Convert alerts to DataFrame
    alerts_df = pd.DataFrame(data["alerts"])
    alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'])
    
    # Count alerts by type
    alerts_by_type = alerts_df['type'].value_counts().reset_index()
    alerts_by_type.columns = ['Type', 'Count']
    
    alerts_type_fig = px.pie(
        alerts_by_type,
        names='Type',
        values='Count',
        title='Alert Distribution by Type',
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    
    # Count alerts by priority
    alerts_by_priority = alerts_df['priority'].value_counts().reset_index()
    alerts_by_priority.columns = ['Priority', 'Count']
    
    # Define custom sort order for priority
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    alerts_by_priority['SortOrder'] = alerts_by_priority['Priority'].map(priority_order)
    alerts_by_priority = alerts_by_priority.sort_values('SortOrder')
    
    alerts_priority_fig = px.bar(
        alerts_by_priority,
        x='Priority',
        y='Count',
        title='Alert Distribution by Priority',
        color='Priority',
        color_discrete_map={
            'critical': '#9C27B0',
            'high': '#F44336',
            'medium': '#FF9800',
            'low': '#4CAF50'
        },
        category_orders={"Priority": ["critical", "high", "medium", "low"]}
    )
    
    # Count alerts by status
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
    
    # Create a table for active alerts
    active_alerts = alerts_df[alerts_df['status'] == 'active'].sort_values('timestamp', ascending=False)
    
    alerts_table = dash_table.DataTable(
        id='alerts-table',
        columns=[
            {"name": "Timestamp", "id": "timestamp"},
            {"name": "Type", "id": "type"},
            {"name": "Priority", "id": "priority"},
            {"name": "Description", "id": "description"},
            {"name": "Status", "id": "status"}
        ],
        data=alerts_df.to_dict('records'),
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'minWidth': '100px',
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_header={
            'backgroundColor': 'rgb(240, 240, 240)',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{priority} = "critical"'},
                'backgroundColor': 'rgba(156, 39, 176, 0.15)',
                'color': '#9C27B0',
                'fontWeight': 'bold'
            },
            {
                'if': {'filter_query': '{priority} = "high"'},
                'backgroundColor': 'rgba(244, 67, 54, 0.15)',
                'color': '#F44336'
            },
            {
                'if': {'filter_query': '{priority} = "medium"'},
                'backgroundColor': 'rgba(255, 152, 0, 0.15)',
                'color': '#FF9800'
            },
            {
                'if': {'filter_query': '{status} = "active"'},
                'backgroundColor': 'rgba(244, 67, 54, 0.05)'
            },
        ],
        filter_action="native",
        sort_action="native",
    )
    
    # Create layout
    layout = html.Div([
        html.Div([
            html.H1("Alerts Dashboard", className="page-title"),
            
            # Alert summary cards
            html.Div([
                html.Div([
                    html.H3("Alert Summary"),
                    html.Div([
                        html.Div([
                            html.H4(f"{len(alerts_df[alerts_df['status'] == 'active'])}"),
                            html.P("Active Alerts"),
                        ], className="summary-box active"),
                        html.Div([
                            html.H4(f"{len(alerts_df[alerts_df['status'] == 'acknowledged'])}"),
                            html.P("Acknowledged"),
                        ], className="summary-box acknowledged"),
                        html.Div([
                            html.H4(f"{len(alerts_df[alerts_df['status'] == 'resolved'])}"),
                            html.P("Resolved"),
                        ], className="summary-box resolved"),
                        html.Div([
                            html.H4(f"{len(alerts_df[alerts_df['priority'] == 'critical'])}"),
                            html.P("Critical"),
                        ], className="summary-box critical"),
                    ], className="summary-container"),
                ], className="card full-width"),
            ], className="row"),
            
            html.Div([
                html.Div([
                    html.Div([
                        html.H3("Alerts by Type"),
                        dcc.Graph(
                            id='alerts-type-chart',
                            figure=alerts_type_fig
                        ),
                    ], className="card"),
                ], className="column-left"),
                
                html.Div([
                    html.Div([
                        html.H3("Alerts by Priority"),
                        dcc.Graph(
                            id='alerts-priority-chart',
                            figure=alerts_priority_fig
                        ),
                    ], className="card"),
                ], className="column-right"),
            ], className="row"),
            
            html.Div([
                html.Div([
                    html.Div([
                        html.H3("Alerts by Status"),
                        dcc.Graph(
                            id='alerts-status-chart',
                            figure=alerts_status_fig
                        ),
                    ], className="card"),
                ], className="column-full"),
            ], className="row"),
            
            # Filters and Alert Table
            html.Div([
                html.Div([
                    html.H3("Alert Management"),
                    html.Div([
                        html.Div([
                            html.Label("Filter by Status:"),
                            dcc.Dropdown(
                                id='status-filter',
                                options=[
                                    {'label': 'All', 'value': 'all'},
                                    {'label': 'Active', 'value': 'active'},
                                    {'label': 'Acknowledged', 'value': 'acknowledged'},
                                    {'label': 'Resolved', 'value': 'resolved'}
                                ],
                                value='all',
                                className="filter-dropdown-inline"
                            ),
                        ], className="filter-item-inline"),
                        
                        html.Div([
                            html.Label("Filter by Priority:"),
                            dcc.Dropdown(
                                id='priority-filter',
                                options=[
                                    {'label': 'All', 'value': 'all'},
                                    {'label': 'Critical', 'value': 'critical'},
                                    {'label': 'High', 'value': 'high'},
                                    {'label': 'Medium', 'value': 'medium'},
                                    {'label': 'Low', 'value': 'low'}
                                ],
                                value='all',
                                className="filter-dropdown-inline"
                            ),
                        ], className="filter-item-inline"),
                        
                        html.Button(
                            "Apply Filters", 
                            id="apply-alert-filters",
                            className="filter-button-inline"
                        ),
                    ], className="filters-inline"),
                    alerts_table,
                    
                    html.Div([
                        html.Button(
                            "Acknowledge Selected", 
                            id="acknowledge-button",
                            className="action-button"
                        ),
                        html.Button(
                            "Resolve Selected", 
                            id="resolve-button",
                            className="action-button"
                        ),
                    ], className="button-container"),
                ], className="card full-width"),
            ], className="row"),
        ], className="dashboard-container"),
    ])
    
    return layout
