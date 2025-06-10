import sys
import random
import os
import time
import requests


# Add parent directory to path to import classes
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.log_entry import LogEntry
# Server configuration
SERVER_URL = "http://localhost:2000"

def send_batch_logs(logs_batch):
    """Send a batch of logs to the server"""
    for log_entry in logs_batch:
        try:
            response = requests.post(f"{SERVER_URL}/log", json=log_entry.to_dict(), headers={"Content-Type": "application/json"})
            if response.status_code == 201:
                print(f"✅ Sent log: {log_entry.level} - {log_entry.message}")
            else:
                print(f"❌ Failed to send log: {response.status_code}")
        except Exception as e:
            print(f"❌ Error sending log: {e}")

def main():
    batch_size = 5  # Send logs in batches of 5
    batch_interval = 3.0  # Send batches every 3 seconds
    log_generation_interval = 0.5  # Generate a log every 0.5 seconds
    
    logs_batch = []
    last_batch_sent = time.time()
    
    print(f"🚀 Starting continuous log generation...")
    print(f"📦 Batch size: {batch_size} logs")
    print(f"⏱️  Batch interval: {batch_interval} seconds")
    print(f"🔄 Log generation interval: {log_generation_interval} seconds")
    print("-" * 50)
    
    while True:
        # Generate a new log entry
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        level = random.choice(levels)
        message = f"Test message {random.randint(1, 1000000)}"
        source = random.choice(["test_continuous.py", "test_improved.py", "test_log.py"])
        metadata = {
            "random_value": random.random(),
            "batch_id": len(logs_batch) + 1,
        }
        log_entry = LogEntry(level, message, source, metadata)
        logs_batch.append(log_entry)
        
        print(f"📝 Generated log {len(logs_batch)}/{batch_size}: {level} - {message}")
        
        # Check if we should send the batch
        current_time = time.time()
        should_send_batch = (len(logs_batch) >= batch_size) or (current_time - last_batch_sent >= batch_interval)
        
        if should_send_batch and logs_batch:
            print(f"\n📤 Sending batch of {len(logs_batch)} logs...")
            send_batch_logs(logs_batch)
            print(f"✨ Batch sent successfully!\n")
            logs_batch = []
            last_batch_sent = current_time
        
        time.sleep(log_generation_interval)
        
if __name__ == "__main__":
    main() 