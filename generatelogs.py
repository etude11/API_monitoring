import random
import uuid
from datetime import datetime, timedelta

# Define services and corresponding actions
SERVICES = {
    "API-Gateway": ["GET /users/{id}", "POST /orders", "DELETE /cart/item/{id}", "PATCH /payments/refund/{id}"],
    "Auth-Service": ["Validating JWT token for userID={id}", "Token validation successful", "Token validation failed: Expired token"],
    "User-Service": ["Fetching profile for userID={id}", "Response time: {time}ms, status: {status}"],
    "Order-Service": ["Placing new order for userID={id}", "Order processing failed: Out of stock", "Order confirmed with OrderID={order_id}"],
}

# HTTP status codes
HTTP_STATUS_CODES = {
    200: "OK",
    201: "Created",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error"
}

# Generate a random timestamp within the last 7 days
def random_timestamp():
    start_time = datetime.now() - timedelta(days=7)
    random_time = start_time + timedelta(seconds=random.randint(0, 7 * 24 * 60 * 60))
    return random_time

# Generate a random IP address
def random_ip():
    return f"{random.randint(192, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

# Generate a random user ID
def random_user_id():
    return random.randint(1000, 9999)

# Generate a random order ID
def random_order_id():
    return str(uuid.uuid4())[:8]

# Generate a realistic log group for a single API request
def generate_log_group():
    logs = []
    timestamp = random_timestamp()
    user_id = random_user_id()
    ip_address = random_ip()
    service = "API-Gateway"
    endpoint = random.choice(SERVICES[service]).format(id=user_id)
    
    # 1. API Gateway receives the request
    logs.append(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} Service {service} received request: {endpoint} from {ip_address}")

    # Increment timestamp slightly for next logs
    timestamp += timedelta(seconds=1)

    # 2. Authentication check
    auth_status = random.choice(["successful", "failed"])
    logs.append(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} Service Auth-Service validating JWT token for userID={user_id}")

    timestamp += timedelta(seconds=1)

    if auth_status == "successful":
        logs.append(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} Service Auth-Service token validation successful")
    else:
        logs.append(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} Service Auth-Service token validation failed: Expired token")
        logs.append(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} Service {service} response sent for {endpoint}, status: 401, time: {random.randint(50, 200)}ms")
        return logs  # Return early if authentication fails

    timestamp += timedelta(seconds=1)

    # 3. Backend processing (fetch user data, place order, etc.)
    backend_service = random.choice(["User-Service", "Order-Service"])
    backend_action = random.choice(SERVICES[backend_service]).format(id=user_id, order_id=random_order_id(), time=random.randint(50, 500), status=random.choice(list(HTTP_STATUS_CODES.keys())))

    logs.append(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} Service {backend_service} {backend_action}")

    timestamp += timedelta(seconds=1)

    # 4. API Gateway sends the final response
    response_time = random.randint(100, 500)
    response_status = 200 if auth_status == "successful" else 401
    logs.append(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} Service {service} response sent for {endpoint}, status: {response_status}, time: {response_time}ms")

    return logs

# Generate and write logs to a file
def generate_logs_file(filename="grouped_logs.txt", num_groups=100):
    with open(filename, "w") as file:
        for _ in range(num_groups):
            log_group = generate_log_group()
            file.write("\n".join(log_group) + "\n\n")  # Add a newline between log groups
    print(f"{num_groups} grouped logs generated and written to {filename}")

# Run the log generator
generate_logs_file()
