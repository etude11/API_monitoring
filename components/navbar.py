from dash import html, dcc

def create_navbar():
    """
    Creates the navigation bar for the dashboard
    """
    navbar = html.Nav(
        children=[
            html.A(
                html.Img(src="/assets/logo.png", className="logo"),
                href="/",
                className="logo-link"
            ),
            html.H3("API Monitoring Dashboard", className="navbar-title"),
            html.Button(
                "Toggle Theme",
                id="theme-toggle-button",
                className="theme-toggle-button"
            ),
            html.Div(
                className="nav-links",
                children=[
                    dcc.Link("Log Ingestion", href="/log-ingestion", className="nav-link"),
                    dcc.Link("Log Classification", href="/log-classification", className="nav-link"),
                    dcc.Link("Error Detection", href="/error-detection", className="nav-link"),
                    dcc.Link("API Metrics", href="/api-metrics", className="nav-link"),
                    dcc.Link("Infrastructure", href="/infrastructure", className="nav-link"),
                    dcc.Link("User Activity", href="/user-activity", className="nav-link"),
                    dcc.Link("Alerts", href="/alerts", className="nav-link"),
                ]
            ),
        ],
        className="navbar"
    )
    return navbar
