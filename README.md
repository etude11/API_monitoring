# API Monitoring Dashboard

An interactive dashboard for monitoring APIs, logs, infrastructure, user activity, and alerts. Built with Dash and Plotly.

## Features

- **Log Ingestion**: View and analyze logs with filtering capabilities
- **Log Classification**: Categorize and filter logs by classification type
- **Error Detection**: Track API errors and identify problematic endpoints
- **API Metrics**: Monitor response times, error rates, and throughput
- **Infrastructure Monitoring**: Track server performance metrics
- **User Activity Tracking**: Monitor user actions and detect suspicious activities
- **Alert Mechanism**: View and manage alerts based on priority and status

## Project Structure

- **app.py**: Main application file
- **callbacks.py**: Interactive callback functions
- **components/**: Separate modules for each dashboard section
- **data/**: Mock data for development and testing
- **assets/**: CSS styles and images

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install dash plotly pandas numpy
   ```
3. Run the application:
   ```
   python app.py
   ```
4. Open your browser and go to `http://localhost:8050`

## Usage

- Navigate between different sections using the navigation bar
- Use filters to customize the data view in each section
- View visualizations and metrics for different aspects of API performance
- Filter and search logs, errors, and alerts
- Export data or take action on alerts (in future implementations)

## Development

This dashboard is currently using mock data. To connect to real data sources:

1. Implement API connectors in the data layer
2. Update callback functions to fetch real-time data
3. Add authentication and user permissions as needed

## Future Enhancements

- PDF report generation
- Custom alert thresholds
- More advanced analytics features
