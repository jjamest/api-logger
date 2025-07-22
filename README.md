# api-logger

A lightweight HTTP API server for centralized logging and debugging. Send log entries from any application or service to a central server with a web interface for real-time monitoring.

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/jjamest/api-logger.git
cd api-logger
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## How to Run

Start the server by running:

```bash
python main.py
```

The server will start on port 2000 and display the local network IP address (e.g., `http://192.168.1.100:2000`).

Once running, you can:
- View the web interface at the displayed URL
- Send logs to `http://[IP]:2000/log`
- Access various endpoints like `/logs`, `/logs/statistics`, `/health`

## Troubleshooting

### Port Already in Use

If you see an error that port 2000 is already in use, modify the port in `main.py`:

```python
app.run(host='0.0.0.0', port=3000, debug=True)  # Change 2000 to any available port
```

### Cannot Connect from Other Devices

1. Check your firewall settings - ensure the port is open
2. Verify the IP address displayed when starting the server
3. Make sure both devices are on the same network

### Python Module Import Errors

If you get import errors, ensure you're running from the project root directory and all dependencies are installed:

```bash
cd api-logger
pip install -r requirements.txt
python main.py
```

### Permission Errors

On some systems, you may need to run with elevated permissions or use a different port:

```bash
# Use a port above 1024 (doesn't require admin privileges)
# Edit main.py to use port 8000 instead of 2000
```

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
            return response.json()
        else:
            print(f"Failed to send log: {response.text}")
            return None
    except Exception as e:
        print(f"Error sending log: {e}")
        return None

# Usage examples
send_log("INFO", "Application started")
send_log("ERROR", "Database connection failed", metadata={"error_code": 500})
send_log("DEBUG", "Processing user request", metadata={"user_id": 123})
```

### C

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>

typedef struct {
    char* data;
    size_t size;
} APIResponse;

size_t write_callback(void* contents, size_t size, size_t nmemb, APIResponse* response) {
    size_t total_size = size * nmemb;
    response->data = realloc(response->data, response->size + total_size + 1);
    if (response->data) {
        memcpy(&(response->data[response->size]), contents, total_size);
        response->size += total_size;
        response->data[response->size] = 0;
    }
    return total_size;
}

int send_log(const char* server_url, const char* level, const char* message, 
             const char* source, const char* metadata_json) {
    CURL* curl;
    CURLcode res;
    APIResponse response = {0};
    
    curl = curl_easy_init();
    if (!curl) {
        fprintf(stderr, "Failed to initialize CURL\n");
        return -1;
    }
    
    // Prepare JSON payload
    char* json_data = malloc(2048);
    snprintf(json_data, 2048,
        "{"
        "\"level\":\"%s\","
        "\"message\":\"%s\","
        "\"source\":\"%s\","
        "\"metadata\":%s"
        "}",
        level, message, source, metadata_json ? metadata_json : "{}"
    );
    
    // Set headers
    struct curl_slist* headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    
    // Configure CURL
    curl_easy_setopt(curl, CURLOPT_URL, server_url);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_data);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    
    // Perform request
    res = curl_easy_perform(curl);
    
    if (res != CURLE_OK) {
        fprintf(stderr, "Failed to send log: %s\n", curl_easy_strerror(res));
        free(json_data);
        free(response.data);
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
        return -1;
    }
    
    printf("Log sent successfully. Response: %s\n", response.data);
    
    // Cleanup
    free(json_data);
    free(response.data);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    
    return 0;
}

int main() {
    // Replace with your server's IP address and port
    const char* server_url = "http://192.168.1.100:2000/log";
    
    // Send different types of logs
    send_log(server_url, "INFO", "Application started", "c-app", NULL);
    send_log(server_url, "ERROR", "File not found", "c-app", "{\"error_code\":404,\"file\":\"main.c\"}");
    send_log(server_url, "DEBUG", "Processing completed", "c-app", NULL);
    
    return 0;
}
```

**Compilation:**
```bash
# Install libcurl development headers first
# Ubuntu/Debian: sudo apt-get install libcurl4-openssl-dev
# macOS: brew install curl

gcc -o logger_client main.c -lcurl
./logger_client
```

### C++

```cpp
#include <iostream>
#include <string>
#include <memory>
#include <curl/curl.h>

class APILogger {
private:
    std::string server_url;
    CURL* curl;
    
    struct APIResponse {
        std::string data;
    };
    
    static size_t WriteCallback(void* contents, size_t size, size_t nmemb, APIResponse* response) {
        size_t total_size = size * nmemb;
        response->data.append((char*)contents, total_size);
        return total_size;
    }
    
public:
    APILogger(const std::string& url) : server_url(url + "/log") {
        curl_global_init(CURL_GLOBAL_DEFAULT);
        curl = curl_easy_init();
        if (!curl) {
            throw std::runtime_error("Failed to initialize CURL");
        }
    }
    
    ~APILogger() {
        if (curl) {
            curl_easy_cleanup(curl);
        }
        curl_global_cleanup();
    }
    
    bool sendLog(const std::string& level, const std::string& message, 
                 const std::string& source = "cpp-app", 
                 const std::string& metadata = "{}") {
        if (!curl) return false;
        
        // Prepare JSON payload
        std::string json_data = "{"
            "\"level\":\"" + level + "\","
            "\"message\":\"" + message + "\","
            "\"source\":\"" + source + "\","
            "\"metadata\":" + metadata +
        "}";
        
        // Set headers
        struct curl_slist* headers = nullptr;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        
        APIResponse response;
        
        // Configure CURL
        curl_easy_setopt(curl, CURLOPT_URL, server_url.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_data.c_str());
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
        
        // Perform request
        CURLcode res = curl_easy_perform(curl);
        
        curl_slist_free_all(headers);
        
        if (res != CURLE_OK) {
            std::cerr << "Failed to send log: " << curl_easy_strerror(res) << std::endl;
            return false;
        }
        
        std::cout << "Log sent successfully. Response: " << response.data << std::endl;
        return true;
    }
};

int main() {
    try {
        // Replace with your server's IP address and port
        APILogger logger("http://192.168.1.100:2000");
        
        // Send different types of logs
        logger.sendLog("INFO", "Application started");
        logger.sendLog("ERROR", "File not found", "cpp-app", "{\"error_code\":404,\"file\":\"main.cpp\"}");
        logger.sendLog("DEBUG", "Processing completed");
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
```

**Compilation:**
```bash
# Install libcurl development headers first
# Ubuntu/Debian: sudo apt-get install libcurl4-openssl-dev
# macOS: brew install curl

g++ -o logger_client main.cpp -lcurl
./logger_client
```

## API Endpoints

- `POST /log` - Add a new log entry
- `GET /logs` - Retrieve all log entries
- `DELETE /logs` - Clear all log entries
- `GET /events` - Server-Sent Events for real-time updates
- `GET /health` - Health check endpoint
- `GET /logs/statistics` - Get log statistics
- `GET /logs/errors` - Get recent error logs
- `GET /logs/search` - Search logs by text

## Log Levels

Supported log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## License

This project is licensed under the MIT License.
