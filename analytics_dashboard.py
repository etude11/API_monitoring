import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import clickhouse_connect
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy import stats

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "API Analytics Dashboard"

# Connect to ClickHouse
client = clickhouse_connect.get_client(host='localhost', username='default', password='')

app.layout = dbc.Container([
    html.H1("API Analytics Dashboard", className="mb-4"),
    
    dcc.Interval(id='refresh-interval', interval=30*1000, n_intervals=0),
    
    dcc.Tabs([
        dcc.Tab(label="Overview", children=[
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H4("Total Requests", className="card-title"),
                        html.P(id="total-requests", className="card-text")
                    ])
                ]), width=4),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H4("Error Rate", className="card-title"),
                        html.P(id="error-rate", className="card-text")
                    ])
                ]), width=4),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H4("Avg Response Time", className="card-title"),
                        html.P(id="avg-response", className="card-text")
                    ])
                ]), width=4),
            ]),
        ]),
        
        dcc.Tab(label="Response Times", children=[
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Label("Time Range:"),
                        dcc.Dropdown(
                            id='time-range',
                            options=[
                                {'label': 'Last Hour', 'value': 'Last Hour'},
                                {'label': 'Last Day', 'value': 'Last Day'},
                                {'label': 'Last Week', 'value': 'Last Week'},
                                {'label': 'All Time', 'value': 'All Time'}
                            ],
                            value='Last Hour',
                            clearable=False
                        )
                    ], width=3)
                ]),
                
                dbc.Row([
                    dbc.Col(dcc.Graph(id='response-times-plot'), width=12)
                ]),
                
                dbc.Row([
                    dbc.Col(dcc.Graph(id='response-distribution'), width=6),
                    dbc.Col([
                        html.Div([
                            html.H5("Statistics"),
                            html.P(id="p95-stat"),
                            html.P(id="p99-stat"),
                            html.P(id="std-dev-stat"),
                            html.P(id="trend-stat")
                        ], className="mt-4 p-3 border rounded")
                    ], width=6)
                ])
            ])
        ]),
        
        dcc.Tab(label="Errors", children=[
            dbc.Row([
                dbc.Col(dcc.Graph(id='error-codes-chart'), width=6),
                dbc.Col(html.Div(id='error-table'), width=6)
            ])
        ]),
        
        dcc.Tab(label="Endpoints", children=[
            html.Div(id='endpoints-table')
        ])
    ])
], fluid=True)

def get_time_clause(time_range):
    now = datetime.now()
    if time_range == 'Last Hour':
        start_time = now - timedelta(hours=1)
    elif time_range == 'Last Day':
        start_time = now - timedelta(days=1)
    elif time_range == 'Last Week':
        start_time = now - timedelta(weeks=1)
    else:
        return ""
    return f"AND timestamp >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'"

@app.callback(
    [Output('total-requests', 'children'),
     Output('error-rate', 'children'),
     Output('avg-response', 'children')],
    Input('refresh-interval', 'n_intervals')
)
def update_overview(_):
    total = client.query("SELECT count() FROM api_logs").result_rows[0][0]
    error_rate = client.query("SELECT countIf(status_code >= 400)/count()*100 FROM api_logs").result_rows[0][0]
    avg_time = client.query("SELECT avg(response_time) FROM api_logs WHERE response_time IS NOT NULL").result_rows[0][0]
    return f"{total}", f"{error_rate:.2f}%", f"{avg_time:.2f}ms"

@app.callback(
    [Output('response-times-plot', 'figure'),
     Output('response-distribution', 'figure'),
     Output('p95-stat', 'children'),
     Output('p99-stat', 'children'),
     Output('std-dev-stat', 'children'),
     Output('trend-stat', 'children')],
    [Input('time-range', 'value'),
     Input('refresh-interval', 'n_intervals')]
)
def update_response_times(time_range, _):
    time_clause = get_time_clause(time_range)
    query = f"""
    SELECT 
        timestamp,
        response_time,
        endpoint
    FROM api_logs 
    WHERE response_time IS NOT NULL
    {time_clause}
    ORDER BY timestamp
    """
    
    result = client.query(query)
    df = pd.DataFrame(result.result_rows, columns=['timestamp', 'response_time', 'endpoint'])
    
    # Create figures
    time_fig = go.Figure()
    dist_fig = go.Figure()
    stats_outputs = ["N/A"] * 4
    
    if not df.empty:
        # Time series plot
        time_fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['response_time'],
            mode='lines+markers',
            name='Response Time'
        ))
        
        # Trend line
        if len(df) > 1:
            z = np.polyfit(range(len(df)), df['response_time'], 1)
            p = np.poly1d(z)
            trend = 'Increasing' if z[0] > 0 else 'Decreasing'
            trend_text = f"{trend} ({abs(z[0]):.4f}ms/request)"
            time_fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=p(range(len(df))),
                mode='lines',
                name='Trend',
                line=dict(color='red', dash='dash')
            ))
        else:
            trend_text = "Not enough data"
        
        # Distribution plot
        dist_fig.add_trace(go.Histogram(
            x=df['response_time'],
            nbinsx=50,
            marker_color='blue'
        ))
        
        # Calculate statistics
        p95 = np.percentile(df['response_time'], 95)
        p99 = np.percentile(df['response_time'], 99)
        std_dev = np.std(df['response_time'])
        stats_outputs = [
            f"95th Percentile: {p95:.2f}ms",
            f"99th Percentile: {p99:.2f}ms",
            f"Standard Deviation: {std_dev:.2f}ms",
            f"Trend: {trend_text}"
        ]
    
    time_fig.update_layout(
        title='Response Times Over Time',
        xaxis_title='Timestamp',
        yaxis_title='Response Time (ms)'
    )
    
    dist_fig.update_layout(
        title='Response Time Distribution',
        xaxis_title='Response Time (ms)',
        yaxis_title='Frequency'
    )
    
    return time_fig, dist_fig, *stats_outputs

@app.callback(
    [Output('error-codes-chart', 'figure'),
     Output('error-table', 'children')],
    Input('refresh-interval', 'n_intervals')
)
def update_errors(_):
    query = """
    SELECT 
        status_code,
        count() as count,
        endpoint
    FROM api_logs 
    WHERE status_code IS NOT NULL AND status_code >= 400
    GROUP BY status_code, endpoint
    ORDER BY count DESC
    """
    
    result = client.query(query)
    df = pd.DataFrame(result.result_rows, columns=['status_code', 'count', 'endpoint'])
    
    error_fig = go.Figure()
    table = html.Div("No errors found")
    
    if not df.empty:
        error_fig.add_trace(go.Bar(
            x=df['status_code'].astype(str),
            y=df['count'],
            name='Error Count'
        ))
        
        table = dbc.Table([
            html.Thead(html.Tr([
                html.Th("Status Code"), 
                html.Th("Count"), 
                html.Th("Endpoint")
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(row['status_code']),
                    html.Td(row['count']),
                    html.Td(row['endpoint'])
                ]) for _, row in df.iterrows()
            ])
        ], bordered=True, striped=True)
    
    error_fig.update_layout(
        title='Error Status Codes Distribution',
        xaxis_title='Status Code',
        yaxis_title='Count'
    )
    
    return error_fig, table

@app.callback(
    Output('endpoints-table', 'children'),
    Input('refresh-interval', 'n_intervals')
)
def update_endpoints(_):
    query = """
    SELECT 
        endpoint,
        count() as requests,
        avg(response_time) as avg_time,
        countIf(status_code >= 400)/count()*100 as error_rate,
        argMax(status_code, timestamp) as last_status
    FROM api_logs 
    WHERE endpoint IS NOT NULL
    GROUP BY endpoint
    ORDER BY requests DESC
    """
    
    result = client.query(query)
    df = pd.DataFrame(result.result_rows, 
                    columns=['Endpoint', 'Requests', 'Avg Time', 'Error Rate', 'Last Status'])
    
    return dbc.Table([
        html.Thead(html.Tr([
            html.Th("Endpoint"),
            html.Th("Requests"),
            html.Th("Avg Time"),
            html.Th("Error Rate"),
            html.Th("Last Status")
        ])),
        html.Tbody([
            html.Tr([
                html.Td(row['Endpoint']),
                html.Td(f"{row['Requests']}"),
                html.Td(f"{row['Avg Time']:.2f}ms"),
                html.Td(f"{row['Error Rate']:.2f}%"),
                html.Td(row['Last Status'])
            ]) for _, row in df.iterrows()
        ])
    ], bordered=True, striped=True, hover=True)

if __name__ == '__main__':
    app.run_server(debug=True)