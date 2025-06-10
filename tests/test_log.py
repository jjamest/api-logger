import requests
import json
from datetime import datetime

def test_log_to_server():
    """Test function to send a log to the specified server"""
    url = "http://192.168.68.102:2000/log"
    
    # Create test log data
    test_data = {
        "timestamp": datetime.now().isoformat(),
        "level": "ERROR",
        "message": "Test log entry",
        "source": "test_log.py",
        "metadata": {
            "test_id": "test_001",
            "environment": "development"
        }
    }
    
    try:
        # Send POST request to the server
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending request: {e}")

if __name__ == "__main__":
    print("Sending test log to http://192.168.68.102:2000...")
    test_log_to_server()

