import time
import random
import threading
from yadtq import YADTQ

# Kafka and Redis Configuration
KAFKA_BROKER = 'localhost:9092'
REDIS_BACKEND = 'redis://localhost:6379/0'

yadtq = YADTQ(broker=KAFKA_BROKER, backend=REDIS_BACKEND)

EMERGENCY_TYPES = ["medical", "fire", "police"]

def generate_random_location():
    """Generate a random location, occasionally outside Bangalore."""
    # 80% chance to generate a valid Bangalore location
    if random.random() < 0.8:
        latitude = random.uniform(12.8, 13.1)  # Valid latitude for Bangalore
        longitude = random.uniform(77.5, 77.7)  # Valid longitude for Bangalore
    else:
        # Generate a location outside Bangalore
        latitude = random.uniform(10.0, 12.0)  # Example latitude range outside Bangalore
        longitude = random.uniform(75.0, 77.0)  # Example longitude range outside Bangalore
    return {"lat": latitude, "lon": longitude}
    

def create_task(emergency_type):
    """Create a task payload based on the emergency type."""
    task = {"location": generate_random_location()}
    if emergency_type == "fire":
        task["priority"] = random.choice(["high", "medium", "low"])
    elif emergency_type == "medical":
        task["severity"] = random.choice(["critical", "severe", "moderate"])
    elif emergency_type == "police":
        task["threat_level"] = random.choice(["high", "medium", "low"])
    return task

def simulate_fault():
    """Randomly simulate faults for testing purposes."""
    if random.random() < 0.2:  # 20% chance of a simulated fault
        raise ConnectionError("Simulated connection error")


def send_task():
    """Send a single task to the YADTQ queue with fault tolerance."""
    emergency_type = random.choice(EMERGENCY_TYPES)
    task_data = create_task(emergency_type)

    retries = 3
    for attempt in range(1, retries + 1):
        try:
            simulate_fault()  # Test fault tolerance with simulated errors
            task_id = yadtq.send_task(emergency_type, task_data)
            print(f"Task submitted: {task_id}")

            # Monitor the task status in a separate thread
            threading.Thread(target=yadtq.monitor_task_status, args=(task_id,), daemon=True).start()
            break  # Exit retry loop on success
        except Exception as e:
            print(f"Error submitting task: {e}")
            if attempt < retries:
                print(f"Retrying... (Attempt {attempt}/{retries})")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Failed to submit task after {retries} attempts.")

def print_task_updates(task_id, status):
    """Callback to print task updates."""
    print(f"Task {task_id} status: {status.get('status', 'unknown')}")
    if status.get("status") in ["success", "failed"]:
        if "result" in status:
            print(f"Result: {status['result']}")
        if "error" in status:
            print(f"Error: {status['error']}")

def send_tasks_continuously():
    """Continuously send tasks with fault tolerance."""
    while True:
        send_task()
        time.sleep(random.uniform(3,8 ))  # Add a slight delay to avoid overwhelming the system

def print_heartbeat_updates(worker_id, status, task_count, timestamp):
    """Callback to print heartbeat updates."""
    print(f"Heartbeat received from worker {worker_id}:")
    print(f"  Status: {status}")
    print(f"  Task count: {task_count}")
    print(f"  Timestamp: {time.ctime(timestamp)}\n")

if __name__ == "__main__":
    # Start sending tasks continuously in a separate thread
    threading.Thread(target=send_tasks_continuously, daemon=True).start()
    
    # Start monitoring heartbeats
    threading.Thread(
        target=yadtq.monitor_heartbeats, 
        args=(print_heartbeat_updates,), 
        daemon=True
    ).start()

    # Keep the main thread alive
    while True:
        time.sleep(1)


