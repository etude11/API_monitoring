import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                           QWidget, QVBoxLayout, QPushButton, QLabel,
                           QGridLayout, QTableWidget, QTableWidgetItem, QComboBox, QHBoxLayout)
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QBarSeries, QBarSet
from PyQt5.QtCore import Qt, QTimer
import clickhouse_connect
from datetime import datetime, timedelta
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np
from scipy import stats

class APIAnalyticsDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("API Analytics Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        self.client = clickhouse_connect.get_client(host='localhost', username='default', password='')
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Create tabs
        tabs.addTab(self.create_overview_tab(), "Overview")
        tabs.addTab(self.create_response_times_tab(), "Response Times")
        tabs.addTab(self.create_errors_tab(), "Errors")
        tabs.addTab(self.create_endpoints_tab(), "Endpoints")
        
        # Add refresh button
        refresh_btn = QPushButton("Refresh Data")
        refresh_btn.clicked.connect(self.refresh_all)
        layout.addWidget(refresh_btn)
        
        # Set up auto-refresh timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_all)
        self.timer.start(30000)  # Refresh every 30 seconds

    def create_overview_tab(self):
        tab = QWidget()
        layout = QGridLayout()
        
        # Add statistics cards
        self.total_requests_label = QLabel("Total Requests: Loading...")
        self.error_rate_label = QLabel("Error Rate: Loading...")
        self.avg_response_label = QLabel("Avg Response Time: Loading...")
        
        layout.addWidget(self.total_requests_label, 0, 0)
        layout.addWidget(self.error_rate_label, 0, 1)
        layout.addWidget(self.avg_response_label, 0, 2)
        
        # Add charts
        status_chart = QChartView()
        self.status_chart_view = status_chart
        layout.addWidget(status_chart, 1, 0, 1, 3)
        
        tab.setLayout(layout)
        return tab

    def create_response_times_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Create matplotlib figure
        fig = Figure(figsize=(12, 6))
        canvas = FigureCanvasQTAgg(fig)
        layout.addWidget(canvas)
        self.response_fig = fig
        self.response_canvas = canvas
        
        # Add statistics panel
        stats_layout = QGridLayout()
        self.p95_label = QLabel("95th Percentile: Loading...")
        self.p99_label = QLabel("99th Percentile: Loading...")
        self.std_dev_label = QLabel("Standard Deviation: Loading...")
        self.trend_label = QLabel("Trend: Loading...")
        
        stats_layout.addWidget(self.p95_label, 0, 0)
        stats_layout.addWidget(self.p99_label, 0, 1)
        stats_layout.addWidget(self.std_dev_label, 1, 0)
        stats_layout.addWidget(self.trend_label, 1, 1)
        
        stats_widget = QWidget()
        stats_widget.setLayout(stats_layout)
        layout.addWidget(stats_widget)
        
        # Time range selector
        range_layout = QHBoxLayout()
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(['Last Hour', 'Last Day', 'Last Week', 'All Time'])
        self.time_range_combo.currentTextChanged.connect(self.update_response_times_chart)
        range_layout.addWidget(QLabel("Time Range:"))
        range_layout.addWidget(self.time_range_combo)
        range_layout.addStretch()
        
        range_widget = QWidget()
        range_widget.setLayout(range_layout)
        layout.addWidget(range_widget)
        
        tab.setLayout(layout)
        return tab

    def create_errors_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Error rate chart
        chart_view = QChartView()
        self.error_chart_view = chart_view
        layout.addWidget(chart_view)
        
        # Error table
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(3)
        self.error_table.setHorizontalHeaderLabels(["Endpoint", "Error Count", "Error Rate"])
        layout.addWidget(self.error_table)
        
        tab.setLayout(layout)
        return tab

    def create_endpoints_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Endpoints stats table
        self.endpoints_table = QTableWidget()
        self.endpoints_table.setColumnCount(5)
        self.endpoints_table.setHorizontalHeaderLabels([
            "Endpoint", "Requests", "Avg Time", "Error Rate", "Last Status"
        ])
        layout.addWidget(self.endpoints_table)
        
        tab.setLayout(layout)
        return tab

    def update_overview_stats(self):
        # Fetch basic stats
        total_query = "SELECT count() FROM api_logs"
        error_query = "SELECT countIf(status_code >= 400)/count()*100 FROM api_logs"
        avg_time_query = "SELECT avg(response_time) FROM api_logs WHERE response_time IS NOT NULL"
        
        total = self.client.query(total_query).result_rows[0][0]
        error_rate = self.client.query(error_query).result_rows[0][0]
        avg_time = self.client.query(avg_time_query).result_rows[0][0]
        
        self.total_requests_label.setText(f"Total Requests: {total}")
        self.error_rate_label.setText(f"Error Rate: {error_rate:.2f}%")
        self.avg_response_label.setText(f"Avg Response Time: {avg_time:.2f}ms")

    def update_response_times_chart(self):
        # Clear the figure
        self.response_fig.clear()
        
        # Get time range
        time_range = self.time_range_combo.currentText()
        time_clause = self.get_time_clause(time_range)
        
        # Fetch data - using toDateTime64 to handle microseconds
        query = f"""
        SELECT 
            toDateTime(timestamp) as ts_time,
            response_time,
            endpoint
        FROM api_logs 
        WHERE response_time IS NOT NULL
        {time_clause}
        ORDER BY ts_time
        """
        
        try:
            result = self.client.query(query)
            
            if not result.result_rows or len(result.result_rows) == 0:
                # Display "No data" message on the plot
                ax = self.response_fig.add_subplot(111)
                ax.text(0.5, 0.5, "No data available", horizontalalignment='center', 
                        verticalalignment='center', transform=ax.transAxes, fontsize=14)
                self.response_fig.tight_layout()
                self.response_canvas.draw()
                return
            
            timestamps = [row[0] for row in result.result_rows]
            response_times = [row[1] for row in result.result_rows]
            endpoints = [row[2] for row in result.result_rows]
            
            # Create subplots
            ax1 = self.response_fig.add_subplot(211)  # Time series
            ax2 = self.response_fig.add_subplot(212)  # Distribution
            
            # Plot time series
            ax1.plot(timestamps, response_times, 'b-', alpha=0.5)
            ax1.scatter(timestamps, response_times, c='blue', s=20, alpha=0.5)
            
            # Add trend line
            if len(timestamps) > 1:  # Only add trend line if we have enough points
                z = np.polyfit(range(len(timestamps)), response_times, 1)
                p = np.poly1d(z)
                trend_line = p(range(len(timestamps)))
                ax1.plot(timestamps, trend_line, 'r--', label='Trend')
                trend = 'Increasing' if z[0] > 0 else 'Decreasing'
                self.trend_label.setText(f"Trend: {trend} ({abs(z[0]):.4f}ms/request)")
            else:
                self.trend_label.setText("Trend: Not enough data")
            
            ax1.set_title('Response Times Over Time')
            ax1.set_xlabel('Timestamp')
            ax1.set_ylabel('Response Time (ms)')
            ax1.grid(True)
            
            # Plot distribution
            ax2.hist(response_times, bins=min(50, len(response_times)), alpha=0.7, color='blue')
            ax2.set_title('Response Time Distribution')
            ax2.set_xlabel('Response Time (ms)')
            ax2.set_ylabel('Frequency')
            ax2.grid(True)
            
            # Calculate statistics
            if response_times:
                p95 = np.percentile(response_times, 95)
                p99 = np.percentile(response_times, 99)
                std_dev = np.std(response_times)
                
                # Update statistics labels
                self.p95_label.setText(f"95th Percentile: {p95:.2f}ms")
                self.p99_label.setText(f"99th Percentile: {p99:.2f}ms")
                self.std_dev_label.setText(f"Standard Deviation: {std_dev:.2f}ms")
            else:
                self.p95_label.setText("95th Percentile: N/A")
                self.p99_label.setText("99th Percentile: N/A")
                self.std_dev_label.setText("Standard Deviation: N/A")
            
            # Adjust layout and display
            self.response_fig.tight_layout()
            self.response_canvas.draw()
            
        except Exception as e:
            print(f"Error updating response times chart: {str(e)}")
            # Show error in the plot
            self.response_fig.clear()
            ax = self.response_fig.add_subplot(111)
            ax.text(0.5, 0.5, f"Error: {str(e)}", horizontalalignment='center', 
                    verticalalignment='center', transform=ax.transAxes, fontsize=12,
                    wrap=True)
            self.response_fig.tight_layout()
            self.response_canvas.draw()

    def get_time_clause(self, time_range):
        now = datetime.now()
        if time_range == 'Last Hour':
            start_time = now - timedelta(hours=1)
        elif time_range == 'Last Day':
            start_time = now - timedelta(days=1)
        elif time_range == 'Last Week':
            start_time = now - timedelta(weeks=1)
        else:  # All Time
            return ""
        
        # Format the date to avoid microsecond issues
        formatted_date = start_time.strftime('%Y-%m-%d %H:%M:%S')
        return f"AND toDateTime(timestamp) >= toDateTime('{formatted_date}')"

    def update_error_chart(self):
        query = """
        SELECT 
            status_code,
            count() as count
        FROM api_logs 
        WHERE status_code IS NOT NULL
        GROUP BY status_code
        ORDER BY status_code
        """
        
        result = self.client.query(query)
        
        bar_set = QBarSet("Status Codes")
        labels = []
        for row in result.result_rows:
            bar_set.append(row[1])
            labels.append(str(row[0]))
        
        series = QBarSeries()
        series.append(bar_set)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Status Code Distribution")
        self.error_chart_view.setChart(chart)

    def refresh_all(self):
        self.update_overview_stats()
        self.update_response_times_chart()
        self.update_error_chart()
        self.update_tables()

    def update_tables(self):
        # Update endpoints table
        endpoint_query = """
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
        
        result = self.client.query(endpoint_query)
        self.endpoints_table.setRowCount(len(result.result_rows))
        
        for i, row in enumerate(result.result_rows):
            self.endpoints_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.endpoints_table.setItem(i, 1, QTableWidgetItem(str(row[1])))
            self.endpoints_table.setItem(i, 2, QTableWidgetItem(f"{row[2]:.2f}ms"))
            self.endpoints_table.setItem(i, 3, QTableWidgetItem(f"{row[3]:.2f}%"))
            self.endpoints_table.setItem(i, 4, QTableWidgetItem(str(row[4])))

def main():
    app = QApplication(sys.argv)
    dashboard = APIAnalyticsDashboard()
    dashboard.show()
    dashboard.refresh_all()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
