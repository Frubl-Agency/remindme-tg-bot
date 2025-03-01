import os
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

def load_tasks():
    """Load tasks from JSON file."""
    if os.path.exists('data/tasks.json'):
        with open('data/tasks.json', 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.error("Error decoding tasks.json, returning empty dict")
                return {}
    return {}

def save_tasks(tasks):
    """Save tasks to JSON file."""
    with open('data/tasks.json', 'w') as f:
        json.dump(tasks, f, indent=2)

# Initialize tasks
tasks = load_tasks()