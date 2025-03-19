import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import json

# Import components
from components.navbar import create_navbar
from components.log_ingestion import create_log_ingestion_layout
from components.log_classification import create_log_classification_layout
from components.error_detection import create_error_detection_layout
from components.api_metrics import create_api_metrics_layout
from components.infra_monitoring import create_infrastructure_monitoring_layout
from components.user_activity import create_user_activity_layout
from components.alerts import create_alerts_layout

# Import mock data
from data.mock_data import mock_data

# Import callbacks
from callbacks import register_callbacks

# Initialize the Dash app
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

app.title = "API Monitoring Dashboard"

# App layout with navigation
app.layout = html.Div(
    id="app-container",
    className="app-container light-mode",
    children=[
        dcc.Store(id="theme-store", data="light"),
        dcc.Location(id="url", refresh=False),
        create_navbar(),
        html.Div(id="page-content", className="content"),
    ],
)

# Callback to render different pages based on URL
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/log-ingestion" or pathname == "/":
        return create_log_ingestion_layout(mock_data)
    elif pathname == "/log-classification":
        return create_log_classification_layout(mock_data)
    elif pathname == "/error-detection":
        return create_error_detection_layout(mock_data)
    elif pathname == "/api-metrics":
        return create_api_metrics_layout(mock_data)
    elif pathname == "/infrastructure":
        return create_infrastructure_monitoring_layout(mock_data)
    elif pathname == "/user-activity":
        return create_user_activity_layout(mock_data)
    elif pathname == "/alerts":
        return create_alerts_layout(mock_data)
    else:
        return html.Div([html.H1("404 - Page not found")])

# Register all interactive callbacks
register_callbacks(app, mock_data)

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0')
