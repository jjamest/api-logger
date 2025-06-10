#!/usr/bin/env python3
"""
Test script for the improved API Logger with LogManager and LogEntry classes.

This script demonstrates:
1. Basic log creation and management
2. Filtering capabilities
3. Statistics gathering
4. Error tracking
5. HTTP API testing

Run this after starting the server with: python main.py
"""

import requests
import json
import time
from datetime import datetime
import sys
import random
import os

# Add parent directory to path to import classes
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Server configuration
SERVER_URL = "http://localhost:2000"

def test_local_classes():
    """Test the LogManager and LogEntry classes directly"""
    print("🧪 Testing LogManager and LogEntry classes locally...")
    
    from classes import LogManager, LogEntry, LogLevel
    
    # Create a LogManager instance
    log_manager = LogManager(max_logs=100)
    
    # Test adding various log levels
    test_logs = [
        ("INFO", "Application started", "main.py"),
        ("DEBUG", "Database connection established", "db_manager.py"),
        ("WARNING", "High memory usage detected", "memory_monitor.py"),
        ("ERROR", "Failed to process user request", "api_handler.py"),
        ("CRITICAL", "Database connection lost", "db_manager.py"),
        ("INFO", "User login successful", "auth_service.py"),
        ("ERROR", "Invalid API key provided", "api_handler.py"),
    ]
    
    for level, message, source in test_logs:
        metadata = {
            "user_id": random.randint(1000, 9999),
            "request_id": f"req_{random.randint(100000, 999999)}",
            "ip_address": f"192.168.1.{random.randint(1, 255)}"
        }
        log_manager.add_log(level, message, source, metadata)
        time.sleep(0.1)  # Small delay to show timestamp differences
    
    # Test filtering
    print(f"\n📊 Total logs: {len(log_manager)}")
    
    # Get error logs only
    error_logs = log_manager.get_logs(level_filter="ERROR")
    print(f"🚨 Error logs: {len(error_logs)}")
    for log in error_logs:
        print(f"   {log}")
    
    # Get logs from specific source
    db_logs = log_manager.get_logs(source_filter="db_manager")
    print(f"\n🗄️ Database-related logs: {len(db_logs)}")
    for log in db_logs:
        print(f"   {log}")
    
    # Get recent errors
    recent_errors = log_manager.get_recent_errors()
    print(f"\n⚠️ Recent errors: {len(recent_errors)}")
    
    # Get statistics
    stats = log_manager.get_statistics()
    print(f"\n📈 Statistics:")
    print(f"   Current logs: {stats['current_log_count']}")
    print(f"   Total processed: {stats['total_logs_processed']}")
    print(f"   By level: {stats['logs_by_level']}")
    print(f"   By source: {stats['logs_by_source']}")
    
    print("✅ Local class testing completed!\n")

def test_api_endpoints():
    """Test the HTTP API endpoints"""
    print("🌐 Testing HTTP API endpoints...")
    
    try:
        # Test health check
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        print(f"   Make sure the server is running on {SERVER_URL}")
        return
    
    # Test adding logs via API
    test_api_logs = [
        {
            "level": "INFO",
            "message": "API test log - User registration",
            "source": "test_improved.py",
            "metadata": {
                "test_type": "api_test",
                "user_email": "test@example.com",
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "level": "ERROR", 
            "message": "API test log - Database timeout",
            "source": "test_improved.py",
            "metadata": {
                "test_type": "api_test",
                "error_code": 1001,
                "retry_count": 3
            }
        },
        {
            "level": "WARNING",
            "message": "API test log - Rate limit approaching", 
            "source": "test_improved.py",
            "metadata": {
                "test_type": "api_test",
                "current_requests": 450,
                "limit": 500
            }
        }
    ]
    
    print("\n📝 Adding test logs via API...")
    for i, log_data in enumerate(test_api_logs):
        try:
            response = requests.post(
                f"{SERVER_URL}/log",
                json=log_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            if response.status_code == 201:
                result = response.json()
                print(f"   ✅ Log {i+1} added (ID: {result.get('log_id')})")
            else:
                print(f"   ❌ Failed to add log {i+1}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error adding log {i+1}: {e}")
    
    # Test getting logs with filtering
    print("\n📋 Testing log retrieval with filters...")
    
    # Get all logs
    try:
        response = requests.get(f"{SERVER_URL}/logs", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Retrieved {data['count']} total logs")
        else:
            print(f"   ❌ Failed to get logs: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error getting logs: {e}")
    
    # Get error logs only
    try:
        response = requests.get(f"{SERVER_URL}/logs?level=ERROR", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Retrieved {data['count']} error logs")
        else:
            print(f"   ❌ Failed to get error logs: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error getting error logs: {e}")
    
    # Get logs from test source
    try:
        response = requests.get(f"{SERVER_URL}/logs?source=test_improved", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Retrieved {data['count']} logs from test source")
        else:
            print(f"   ❌ Failed to get test logs: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error getting test logs: {e}")
    
    # Test statistics endpoint
    print("\n📈 Testing statistics endpoint...")
    try:
        response = requests.get(f"{SERVER_URL}/logs/statistics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            stats = data['statistics']
            print(f"   ✅ Current logs: {stats['current_log_count']}")
            print(f"   ✅ Total processed: {stats['total_logs_processed']}")
            print(f"   ✅ By level: {stats['logs_by_level']}")
        else:
            print(f"   ❌ Failed to get statistics: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error getting statistics: {e}")
    
    # Test recent errors endpoint
    print("\n🚨 Testing recent errors endpoint...")
    try:
        response = requests.get(f"{SERVER_URL}/logs/errors", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Retrieved {data['count']} recent errors")
        else:
            print(f"   ❌ Failed to get recent errors: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error getting recent errors: {e}")
    
    print("\n✅ API testing completed!")

def main():
    """Main test function"""
    print("🚀 Starting comprehensive tests for improved API Logger\n")
    
    # Test local classes first
    test_local_classes()
    
    # Test API endpoints
    test_api_endpoints()
    
    print(f"\n🎉 All tests completed!")
    print(f"🌐 Visit {SERVER_URL} to see the web interface")
    print(f"📊 Visit {SERVER_URL}/logs/statistics for detailed statistics")

if __name__ == "__main__":
    main() 