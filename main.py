from flask import Flask, request, jsonify, render_template, Response
from datetime import datetime
import threading
import json

from network import get_local_ip

app = Flask(__name__)

# In-memory storage for logs
logs = []
log_lock = threading.Lock()

# SSE clients
sse_clients = []
sse_lock = threading.Lock()

def emit_log_update():
    """Emit log update to all SSE clients"""
    if not sse_clients:
        return
    
    data = json.dumps({
        "success": True,
        "count": len(logs),
        "logs": list(reversed(logs))
    })
    
    message = f"data: {data}\n\n"
    
    with sse_lock:
        # Remove disconnected clients
        active_clients = []
        for client in sse_clients:
            try:
                client.put(message)
                active_clients.append(client)
            except:
                pass  # Client disconnected
        sse_clients[:] = active_clients

@app.route('/')
def home():
    """Home endpoint with HTML page showing all logs"""
    return render_template('index.html', logs=list(reversed(logs)))

@app.route('/events')
def events():
    """Server-sent events endpoint for real-time log updates"""
    import queue
    
    client_queue = queue.Queue()
    
    with sse_lock:
        sse_clients.append(client_queue)
    
    def event_stream():
        try:
            # Send initial data
            initial_data = json.dumps({
                "success": True,
                "count": len(logs),
                "logs": list(reversed(logs))
            })
            yield f"data: {initial_data}\n\n"
            
            # Stream updates
            while True:
                message = client_queue.get()
                yield message
        except GeneratorExit:
            with sse_lock:
                if client_queue in sse_clients:
                    sse_clients.remove(client_queue)
    
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/log', methods=['POST'])
def add_log():
    """Add a new log entry"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Create log entry
        log_entry = {
            "id": len(logs) + 1,
            "timestamp": datetime.now().isoformat(),
            "level": data.get("level", "INFO").upper(),
            "message": data.get("message", ""),
            "source": data.get("source", "unknown"),
            "metadata": data.get("metadata", {})
        }

        print("\n-------------------- Log start --------------------")
        for key in log_entry:
            print(f"{key}: {log_entry[key]}")
        print("-------------------- Log end --------------------\n")
        
        # Add to logs with thread safety
        with log_lock:
            logs.append(log_entry)
        
        # Emit update to SSE clients
        emit_log_update()
        
        return jsonify({
            "success": True,
            "message": "Log entry added",
            "log_id": log_entry["id"]
        }), 201
        
    except Exception as e:
        print(f"💥 Error in add_log: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    """Get all logs with optional filtering"""
    try:
        return jsonify({
            "success": True,
            "count": len(logs),
            "logs": list(reversed(logs))
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logs', methods=['DELETE'])
def clear_logs():
    """Clear all logs"""
    try:
        with log_lock:
            logs.clear()
        
        # Emit update to SSE clients
        emit_log_update()
        
        return jsonify({
            "success": True,
            "message": "All logs cleared"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    local_ip = get_local_ip()

    print(f"\nServer running on http://{local_ip}:2000\n")
    
    # Run the server
    app.run(host='0.0.0.0', port=2000, debug=True)
