from dash import html, dcc, dash_table
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd

def create_user_activity_layout(data):
    """
    Creates the layout for user activity tracking visualization
    """
    # Convert user activity data to DataFrame
    activity_df = pd.DataFrame(data["user_activities"])
    activity_df['timestamp'] = pd.to_datetime(activity_df['timestamp'])
    
    # Add date column for grouping
    activity_df['date'] = activity_df['timestamp'].dt.date
    
    # Count activities by action type
    actions_count = activity_df['action'].value_counts().reset_index()
    actions_count.columns = ['Action', 'Count']
    
    action_fig = px.pie(
        actions_count,
        names='Action',
        values='Count',
        title='Activity Distribution by Action Type',
        hole=0.4
    )
    
    # Count activities by date
    activities_by_date = activity_df.groupby('date').size().reset_index(name='count')
    
    activity_trend_fig = px.line(
        activities_by_date,
        x='date',
        y='count',
        title='User Activity Trends',
        labels={'count': 'Number of Activities', 'date': 'Date'}
    )
    
    # Filter suspicious activities
    suspicious_df = activity_df[activity_df['is_suspicious'] == True]
    
    suspicious_fig = px.bar(
        suspicious_df.groupby(['reason']).size().reset_index(name='count'),
        x='reason',
        y='count',
        title='Suspicious Activities by Reason',
        labels={'count': 'Number of Activities', 'reason': 'Reason'},
        color_discrete_sequence=['#ff7f0e']
    )
    
    # Most active users
    user_activity_counts = activity_df.groupby('user_id').size().reset_index(name='count')
    top_users = user_activity_counts.sort_values('count', ascending=False).head(10)
    
    users_fig = px.bar(
        top_users,
        x='user_id',
        y='count',
        title='Top 10 Most Active Users',
        labels={'count': 'Number of Activities', 'user_id': 'User ID'}
    )
    
    # Create table for suspicious activities
    suspicious_table = dash_table.DataTable(
        id='suspicious-table',
        columns=[
            {"name": "Timestamp", "id": "timestamp"},
            {"name": "User ID", "id": "user_id"},
            {"name": "Action", "id": "action"},
            {"name": "IP Address", "id": "ip_address"},
            {"name": "Reason", "id": "reason"}
        ],
        data=suspicious_df.to_dict('records'),
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
                'if': {'filter_query': '{reason} contains "Multiple failed"'},
                'backgroundColor': 'rgba(255, 0, 0, 0.1)',
            },
            {
                'if': {'filter_query': '{reason} contains "Unusual"'},
                'backgroundColor': 'rgba(255, 165, 0, 0.1)',
            }
        ],
        filter_action="native",
        sort_action="native",
    )
    
    # Create layout
    layout = html.Div([
        html.Div([
            html.H1("User Activity Tracking Dashboard", className="page-title"),
            
            # Summary cards
            html.Div([
                html.Div([
                    html.H3("User Activity Overview"),
                    html.Div([
                        html.Div([
                            html.H4(f"{len(activity_df)}"),
                            html.P("Total Activities"),
                        ], className="summary-box total"),
                        html.Div([
                            html.H4(f"{len(activity_df['user_id'].unique())}"),
                            html.P("Unique Users"),
                        ], className="summary-box users"),
                        html.Div([
                            html.H4(f"{len(suspicious_df)}"),
                            html.P("Suspicious Activities"),
                        ], className="summary-box suspicious"),
                        html.Div([
                            html.H4(f"{len(activity_df['ip_address'].unique())}"),
                            html.P("Unique IP Addresses"),
                        ], className="summary-box ips"),
                    ], className="summary-container"),
                ], className="card full-width"),
            ], className="row"),
            
            html.Div([
                html.Div([
                    html.Div([
                        html.H3("Activity Distribution"),
                        dcc.Graph(
                            id='action-distribution-chart',
                            figure=action_fig
                        ),
                    ], className="card"),
                ], className="column-left"),
                
                html.Div([
                    html.Div([
                        html.H3("Activity Trends"),
                        dcc.Graph(
                            id='activity-trend-graph',
                            figure=activity_trend_fig
                        ),
                    ], className="card"),
                ], className="column-right"),
            ], className="row"),
            
            html.Div([
                html.Div([
                    html.Div([
                        html.H3("Top Active Users"),
                        dcc.Graph(
                            id='top-users-chart',
                            figure=users_fig
                        ),
                    ], className="card"),
                ], className="column-left"),
                
                html.Div([
                    html.Div([
                        html.H3("Suspicious Activity Reasons"),
                        dcc.Graph(
                            id='suspicious-chart',
                            figure=suspicious_fig
                        ),
                    ], className="card"),
                ], className="column-right"),
            ], className="row"),
            
            html.Div([
                html.Div([
                    html.H3("Suspicious Activities"),
                    html.Div([
                        html.Label("Filter by Reason:"),
                        dcc.Dropdown(
                            id='reason-filter',
                            options=[{'label': reason, 'value': reason} 
                                     for reason in suspicious_df['reason'].unique() if reason],
                            multi=True,
                            value=[],
                            className="filter-dropdown-inline"
                        ),
                        html.Button(
                            "Apply Filters", 
                            id="apply-reason-filters",
                            className="filter-button-inline"
                        ),
                    ], className="filters-inline"),
                    suspicious_table,
                ], className="card full-width"),
            ], className="row"),
        ], className="dashboard-container"),
    ])
    
    return layout
