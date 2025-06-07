# api-logger

A lightweight HTTP API server for centralized logging and debugging. Send log entries from any application or service to a central server with a web interface for real-time monitoring.

## Features

- HTTP API for receiving log entries
- Real-time web interface with Server-Sent Events (SSE)
- In-memory storage for fast access
- Thread-safe logging operations
- Support for multiple log levels and metadata
- Cross-platform compatibility
- Zero-configuration setup

## Installation

### Prerequisites

- Python 3.7+
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd api-logger
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python main.py
```

The server will start on port 2000 and display the local network IP address (e.g., `http://192.168.1.100:2000`).

**Note:** If port 2000 is already in use by another application, you'll need to change the port. See the [Configuration](#configuration) section below.

## Usage

### Web Interface

Navigate to the URL displayed when starting the server (e.g., `http://192.168.1.100:2000`) in your browser to view the real-time logging dashboard.

### API Endpoints

#### POST /log
Add a new log entry.

**Request Body:**
```json
{
  "level": "INFO",
  "message": "Your log message",
  "source": "application-name",
  "metadata": {
    "key": "value"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Log entry added",
  "log_id": 1
}
```

#### GET /logs
Retrieve all log entries (most recent first).

**Response:**
```json
{
  "success": true,
  "count": 2,
  "logs": [
    {
      "id": 2,
      "timestamp": "2024-01-01T12:00:00.000000",
      "level": "ERROR",
      "message": "Database connection failed",
      "source": "webapp",
      "metadata": {"error_code": 500}
    }
  ]
}
```

#### DELETE /logs
Clear all log entries.

**Response:**
```json
{
  "success": true,
  "message": "All logs cleared"
}
```

#### GET /events
Server-Sent Events endpoint for real-time log updates.

## Client Examples

### Python

```python
import requests
import json

def send_log(level, message, source="python-app", metadata=None):
    # Replace with your server's IP address and port
    url = "http://192.168.1.100:2000/log"
    data = {
        "level": level,
        "message": message,
        "source": source,
        "metadata": metadata or {}
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 201:
            print(f"Log sent successfully: {message}")
        else:
            print(f"Failed to send log: {response.text}")
    except Exception as e:
        print(f"Error sending log: {e}")

# Usage examples
send_log("INFO", "Application started")
send_log("ERROR", "Database connection failed", metadata={"error_code": 500})
send_log("DEBUG", "Processing user request", metadata={"user_id": 123})
```

### C++

```cpp
#include <iostream>
#include <string>
#include <curl/curl.h>
#include <json/json.h>

class ApiLogger {
private:
    std::string server_url;
    
public:
    ApiLogger(const std::string& url) : server_url(url + "/log") {}
    
    void sendLog(const std::string& level, const std::string& message, 
                 const std::string& source = "cpp-app", 
                 const Json::Value& metadata = Json::Value()) {
        CURL* curl;
        CURLcode res;
        
        curl = curl_easy_init();
        if(curl) {
            // Prepare JSON payload
            Json::Value json_data;
            json_data["level"] = level;
            json_data["message"] = message;
            json_data["source"] = source;
            json_data["metadata"] = metadata;
            
            Json::StreamWriterBuilder builder;
            std::string json_string = Json::writeString(builder, json_data);
            
            // Set headers
            struct curl_slist* headers = NULL;
            headers = curl_slist_append(headers, "Content-Type: application/json");
            
            // Configure curl
            curl_easy_setopt(curl, CURLOPT_URL, server_url.c_str());
            curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_string.c_str());
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
            
            // Perform request
            res = curl_easy_perform(curl);
            
            if(res != CURLE_OK) {
                std::cerr << "Failed to send log: " << curl_easy_strerror(res) << std::endl;
            }
            
            curl_slist_free_all(headers);
            curl_easy_cleanup(curl);
        }
    }
};

// Usage example
int main() {
    // Replace with your server's IP address and port
    ApiLogger logger("http://192.168.1.100:2000");
    
    // Send different types of logs
    logger.sendLog("INFO", "Application started");
    
    Json::Value metadata;
    metadata["error_code"] = 404;
    metadata["file"] = "main.cpp";
    logger.sendLog("ERROR", "File not found", "cpp-app", metadata);
    
    logger.sendLog("DEBUG", "Processing completed");
    
    return 0;
}
```

**Note:** The C++ example requires libcurl and jsoncpp libraries. Install them using:
```bash
# Ubuntu/Debian
sudo apt-get install libcurl4-openssl-dev libjsoncpp-dev

# macOS
brew install curl jsoncpp
```

## Log Levels

Supported log levels (case-insensitive):
- `DEBUG` - Detailed information for debugging
- `INFO` - General information messages
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical error messages

## Configuration

The server runs on port 2000 by default. If this port is already in use by another application, you'll need to change it.

To change the port, modify the `app.run()` call in `main.py`:

```python
app.run(host='0.0.0.0', port=YOUR_PORT, debug=True)
```

For example, to use port 3000:
```python
app.run(host='0.0.0.0', port=3000, debug=True)
```

Then update your client code to use the new port in the server URL.

## Limitations

- Logs are stored in memory only (cleared on server restart)
- No authentication or authorization
- No persistence to disk
- Single-threaded processing (suitable for development/debugging)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
