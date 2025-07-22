import time
from flask import Flask, request, jsonify, render_template, Response
from datetime import datetime
import threading
import json

from network import get_local_ip
from classes import LogManager, LogEntry, LogLevel

app = Flask(__name__)

# Initialize the log manager
log_manager = LogManager(max_logs=10000)

@app.route('/')
def home():
    """Home endpoint with HTML page showing all logs"""
    logs = log_manager.get_logs_as_dicts()
    return render_template('index.html', logs=logs)

@app.route('/events')
def events():
    """Server-sent events endpoint for real-time log updates"""
    client_queue = log_manager.add_sse_client()
    
    def event_stream():
        try:
            # Send initial data
            initial_data = json.dumps({
                "success": True,
                "count": len(log_manager),
                "logs": log_manager.get_logs_as_dicts()
            })
            yield f"data: {initial_data}\n\n"
            
            # Stream updates
            while True:
                message = client_queue.get()
                yield message
        except GeneratorExit:
            log_manager.remove_sse_client(client_queue)
    
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/log', methods=['POST'])
def add_log():
    """Add a new log entry"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400

        time.sleep(0.5) # this is to prevent race conditions

        # Create log entry using LogManager
        log_entry = log_manager.add_log_from_dict(data)

        print(f"\n-------------------- Log start --------------------")
        print(f"ID: {log_entry.entry_id}")
        print(f"Timestamp: {log_entry.timestamp.isoformat()}")
        print(f"Level: {log_entry.level}")
        print(f"Message: {log_entry.message}")
        print(f"Source: {log_entry.source}")
        print(f"Metadata: {log_entry.metadata}")
        print(f"-------------------- Log end --------------------\n")
        
        return jsonify({
            "success": True,
            "message": "Log entry added",
            "log_id": log_entry.entry_id
        }), 201
        
    except Exception as e:
        print(f"💥 Error in add_log: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    """Get all logs with optional filtering"""
    try:
        # Get query parameters for filtering
        level_filter = request.args.get('level')
        source_filter = request.args.get('source')
        limit = request.args.get('limit', type=int)
        
        # Get filtered logs
        logs = log_manager.get_logs_as_dicts(
            level_filter=level_filter,
            source_filter=source_filter,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "count": len(logs),
            "logs": logs
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logs', methods=['DELETE'])
def clear_logs():
    """Clear all logs"""
    try:
        cleared_count = log_manager.clear_logs()
        
        return jsonify({
            "success": True,
            "message": f"Cleared {cleared_count} logs"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logs/statistics', methods=['GET'])
def get_log_statistics():
    """Get log statistics"""
    try:
        stats = log_manager.get_statistics()
        return jsonify({
            "success": True,
            "statistics": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/session/start', methods=['POST'])
def session_start():
    print('asdfasd')
    """Start new log session without clearing existing logs"""
    try:
        print(log_manager.add_session_start_marker())
        return jsonify({
            "success": True,
            "message": "Session start marker added"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/logs/errors', methods=['GET'])
def get_recent_errors():
    """Get recent error and critical logs"""
    try:
        hours = request.args.get('hours', default=24, type=int)
        limit = request.args.get('limit', default=100, type=int)
        
        error_logs = log_manager.get_recent_errors(hours=hours, limit=limit)
        error_dicts = [log.to_dict() for log in error_logs]
        
        return jsonify({
            "success": True,
            "count": len(error_dicts),
            "errors": error_dicts
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logs/search', methods=['GET'])
def search_logs():
    """Search logs for text content"""
    try:
        search_term = request.args.get('q', '').strip()
        
        if not search_term:
            return jsonify({"error": "Search term 'q' is required"}), 400
        
        # Get search parameters
        case_sensitive = request.args.get('case_sensitive', 'false').lower() == 'true'
        search_message = request.args.get('search_message', 'true').lower() == 'true'
        search_source = request.args.get('search_source', 'true').lower() == 'true'
        search_metadata = request.args.get('search_metadata', 'true').lower() == 'true'
        level_filter = request.args.get('level')
        limit = request.args.get('limit', type=int)
        
        # Perform search
        search_results = log_manager.search_logs_as_dicts(
            search_term=search_term,
            case_sensitive=case_sensitive,
            search_message=search_message,
            search_source=search_source,
            search_metadata=search_metadata,
            level_filter=level_filter,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "search_term": search_term,
            "count": len(search_results),
            "logs": search_results
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        stats = log_manager.get_statistics()
        return jsonify({
            "success": True,
            "status": "healthy",
            "log_count": stats['current_log_count'],
            "uptime": "running"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    local_ip = get_local_ip()

    print(f"\n🚀 API Logger Server starting...")
    print(f"Server running on http://{local_ip}:2000")
    
    # Run the server
    app.run(host='0.0.0.0', port=2000, debug=True)
