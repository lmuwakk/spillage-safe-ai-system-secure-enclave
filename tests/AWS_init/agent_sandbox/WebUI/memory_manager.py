#!/usr/bin/env python3
"""
Memory Manager Tool
Acts as the backend for the 'remember' feature.
Updates memory.json by merging new data with existing keys/values.
"""

#-=-=-=-=-=-=-=-=-= Imports =-=-=-=-=-=-=-=-=-#
# Standard Python Libs
import json
import sys
import os

#-=-=-=-=-=-=-=-=-= Variables =-=-=-=-=-=-=-=-=-#
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")
SCHEMA_FILE = os.path.join(BASE_DIR, "memory_schema.json")

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def deep_merge(base, override):
    """Recursively merges override dict into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def update_memory(key=None, data=None):
    """Update memory with a key-value pair or a full JSON object."""
    current_mem = load_json(MEMORY_FILE)
    
    if key and not data:
        # Return specific key
        return json.dumps(current_mem.get(key, "Not found"), indent=2)
    
    if key:
        # Update specific key in memory
        new_mem = deep_merge(current_mem, {key: data})
    else:
        # Update whole object
        new_mem = deep_merge(current_mem, data)

    save_json(MEMORY_FILE, new_mem)
    return "Memory updated successfully."

if __name__ == "__main__":
    args = sys.argv
    
    if len(args) < 2:
        print("Usage: python memory_manager.py [--add KEY VALUE] [--get KEY]")
        sys.exit(1)
        
    command = args[1]
    
    if command == "--get":
        key = args[2] if len(args) > 2 else None
        print(update_memory(key=key))
    elif command == "--add":
        try:
            # Expecting JSON string for data or simple key value
            key = args[2]
            val_str = args[3] if len(args) > 3 else ""
            
            # Try parsing as JSON if it looks like one, otherwise treat as string
            try:
                val_data = json.loads(val_str)
            except:
                val_data = val_str
                
            result = update_memory(key=key, data=val_data)
            print(result)
        except Exception as e:
            print(f"Error adding memory: {e}")
    else:
        print(f"Unknown command: {command}")
