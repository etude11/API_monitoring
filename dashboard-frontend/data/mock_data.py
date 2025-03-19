from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import random

# Generate timestamps for the past week
now = datetime.now()
timestamps = [(now - timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(168, 0, -1)]

# Generate API endpoints
api_endpoints = [
    "/api/users", 
    "/api/products", 
    "/api/orders", 
    "/api/auth/login", 
    "/api/auth/logout",
    "/api/payments",
    "/api/analytics"
]

# Log severity levels
severity_levels = ["INFO", "WARNING", "ERROR", "CRITICAL"]
log_classes = ["Authentication", "Database", "Network", "Authorization", "Input Validation"]

# Generate mock log data
logs = []
for i in range(500):
    timestamp = random.choice(timestamps)
    severity = random.choice(severity_levels)
    endpoint = random.choice(api_endpoints)
    user_id = f"user_{random.randint(1, 100)}"
    message = f"API request to {endpoint}"
    if severity == "ERROR":
        message = f"Failed API request to {endpoint}: Invalid parameters"
    elif severity == "CRITICAL":
        message = f"Service unavailable at {endpoint}: Database connection timeout"
    elif severity == "WARNING":
        message = f"Slow response from {endpoint}: Took over 1000ms"
    
    log_class = random.choice(log_classes)
    
    logs.append({
        "timestamp": timestamp,
        "severity": severity,
        "endpoint": endpoint,
        "user_id": user_id,
        "message": message,
        "log_class": log_class,
    })

# Generate API metrics data
api_metrics = []
for timestamp in timestamps:
    for endpoint in api_endpoints:
        # Response time between 50ms and 500ms
        response_time = max(50, int(np.random.normal(200, 50)))
        
        # Error rate between 0% and 10%
        error_rate = max(0, min(10, np.random.normal(2, 2)))
        
        # Throughput between 10 and 100 requests per minute
        throughput = max(10, int(np.random.normal(50, 20)))
        
        api_metrics.append({
            "timestamp": timestamp,
            "endpoint": endpoint,
            "response_time": response_time,
            "error_rate": error_rate,
            "throughput": throughput
        })

# Generate infrastructure metrics
infra_metrics = []
server_names = ["server-1", "server-2", "server-3", "api-server", "db-server"]

for timestamp in timestamps:
    for server in server_names:
        # CPU usage between 0% and 100%
        cpu_usage = max(0, min(100, np.random.normal(60, 15)))
        
        # Memory usage between 0% and 100%
        memory_usage = max(0, min(100, np.random.normal(70, 10)))
        
        # Disk usage between 20% and 95%
        disk_usage = max(20, min(95, np.random.normal(65, 10)))
        
        # Network IO in Mbps between 1 and 1000
        network_in = max(1, min(1000, np.random.normal(200, 150)))
        network_out = max(1, min(1000, np.random.normal(150, 100)))
        
        infra_metrics.append({
            "timestamp": timestamp,
            "server": server,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "network_in": network_in,
            "network_out": network_out
        })

# Generate user activity data
user_activities = []
actions = ["login", "logout", "view_page", "edit_resource", "delete_resource", "create_resource", "export_data"]
ips = [f"192.168.1.{i}" for i in range(1, 20)] + [f"10.0.0.{i}" for i in range(1, 20)]

for i in range(300):
    timestamp = random.choice(timestamps)
    user_id = f"user_{random.randint(1, 100)}"
    action = random.choice(actions)
    ip_address = random.choice(ips)
    
    # Flag some activities as suspicious
    is_suspicious = random.random() < 0.1
    reason = None
    
    if is_suspicious:
        reasons = [
            "Multiple failed login attempts",
            "Unusual access time",
            "Access from new location",
            "Unusual data export volume",
            "Multiple resource deletions"
        ]
        reason = random.choice(reasons)
    
    user_activities.append({
        "timestamp": timestamp,
        "user_id": user_id,
        "action": action,
        "ip_address": ip_address,
        "is_suspicious": is_suspicious,
        "reason": reason
    })

# Generate alerts
alerts = []
alert_types = ["High Error Rate", "Service Unavailable", "Slow Response Time", "High CPU Usage", "Memory Leak", "Suspicious Activity"]
severity_map = {"INFO": "low", "WARNING": "medium", "ERROR": "high", "CRITICAL": "critical"}

for i in range(50):
    timestamp = random.choice(timestamps)
    alert_type = random.choice(alert_types)
    severity = random.choice(list(severity_map.keys()))
    priority = severity_map[severity]
    
    if alert_type == "High Error Rate":
        description = f"Error rate exceeded threshold for endpoint {random.choice(api_endpoints)}"
    elif alert_type == "Service Unavailable":
        description = f"Service {random.choice(api_endpoints)} is not responding"
    elif alert_type == "Slow Response Time":
        description = f"Response time exceeded 1000ms for endpoint {random.choice(api_endpoints)}"
    elif alert_type == "High CPU Usage":
        description = f"CPU usage above 90% on server {random.choice(server_names)}"
    elif alert_type == "Memory Leak":
        description = f"Memory usage consistently increasing on server {random.choice(server_names)}"
    else:
        description = f"Suspicious activity detected for user {random.choice([f'user_{i}' for i in range(1, 20)])}"
    
    alerts.append({
        "timestamp": timestamp,
        "type": alert_type,
        "severity": severity,
        "priority": priority,
        "description": description,
        "status": random.choice(["active", "acknowledged", "resolved"])
    })

# Combine all mock data
mock_data = {
    "logs": logs,
    "api_metrics": api_metrics,
    "infra_metrics": infra_metrics,
    "user_activities": user_activities,
    "alerts": alerts,
    "endpoints": api_endpoints,
    "severity_levels": severity_levels,
    "servers": server_names,
    "log_classes": log_classes
}
