#!/usr/bin/env python3
"""
Tool definitions for the Tickets Manager Assistant
"""
from typing import Dict, Any

def list_tools(args: Dict[str, Any], tool_definitions: Dict[str, Any]) -> str:
    """Return plain text description of tools"""
    tool_list = []
    for name, spec in tool_definitions.items():
        if name == "none":
            continue
        args_info = ', '.join(spec['required_args']) if spec['required_args'] else 'None'
        tool_list.append(f"- {name}: {spec['description']} (Required args: {args_info})")
    return "Available Tools:\n" + "\n".join(tool_list)

def count_lines(args: Dict[str, Any], db_manager) -> int:
    """Count all log entries"""
    return db_manager.count_lines()

def get_line_by_id(args: Dict[str, Any], db_manager):
    """Get log entry by ID"""
    entry_id = int(args['id'])
    result = db_manager.get_line_by_id(entry_id)
    return result if result else "No entry found with that ID"

def count_entries(args: Dict[str, Any], db_manager) -> int:
    """Count entries with filters"""
    return db_manager.count_entries(args)

def get_entries(args: Dict[str, Any], db_manager) -> list:
    """Get entries with filters"""
    return db_manager.get_entries(args)

# Tool registry
TOOL_DEFINITIONS = {
    'list_tools': {
        'description': 'List all available tools',
        'required_args': [],
        'func': list_tools
    },
    'count_lines': {
        'description': 'Count all log entries',
        'required_args': [],
        'func': count_lines
    },
    'count_entries': {
        'description': 'Count entries by date/time or other filters',
        'required_args': [],
        'func': count_entries
    },
    'get_line_by_id': {
        'description': 'Get log entry by ID',
        'required_args': ['id'],
        'func': get_line_by_id
    },
    'get_entries': {
        'description': 'Get entries by date/time or other filters',
        'required_args': [],
        'func': get_entries
    },
    'none': {
        'description': 'No tool needed - normal conversation',
        'required_args': [],
        'func': lambda args, db: "No tool executed"
    }
}
