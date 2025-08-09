#!/usr/bin/env python3
"""
Tickets Manager Assistant - CSV log analysis and querying
"""
import json
import streamlit as st
from typing import Dict, Any
from database.operations import DatabaseManager
from ingestion.csv_handler import CSVWatcher
from assistants.base_assistant import BaseAssistant
from assistants.tickets_manager.tool_definitions import TOOL_DEFINITIONS

class TicketsManagerAssistant(BaseAssistant):
    """Tickets Manager Assistant for CSV log analysis"""
    
    def __init__(self, config):
        super().__init__(config, 'tickets_manager')
        self.db_manager = None
        self.csv_watcher = None
    
    def get_display_name(self) -> str:
        return "📋 Tickets Manager"
    
    def get_description(self) -> str:
        return "Analyze and query CSV log files with natural language"
    
    def get_tool_definitions(self) -> Dict[str, Any]:
        return TOOL_DEFINITIONS
    
    def initialize_resources(self):
        """Initialize database and CSV watcher"""
        try:
            # Initialize database
            self.db_manager = DatabaseManager(self.config.database)
            self.db_manager.initialize()
            st.session_state.database_connected = True
            
            # Initialize CSV watcher
            self.csv_watcher = CSVWatcher(
                self.config.ingestion.watch_directory,
                self.db_manager,
                self.config.ingestion.csv_separator
            )
            self.csv_watcher.start()
            st.session_state.watcher = self.csv_watcher
            
            st.success("✅ Database and CSV watcher initialized successfully")
            
        except Exception as e:
            st.error(f"Failed to initialize resources: {str(e)}")
            st.session_state.database_connected = False
            raise
    
    def cleanup_resources(self):
        """Cleanup database and CSV watcher"""
        if self.csv_watcher:
            self.csv_watcher.stop()
        if self.db_manager:
            self.db_manager.close()
    
    def handle_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Handle tool execution for tickets manager"""
        if not self.db_manager:
            raise Exception("Database not initialized")
        
        # Get the tool function from definitions
        tool_spec = TOOL_DEFINITIONS[tool_name]
        tool_func = tool_spec['func']
        
        # Execute the tool with database manager
        if tool_name == 'list_tools':
            return tool_func(args, TOOL_DEFINITIONS)
        else:
            return tool_func(args, self.db_manager)
    
    def format_tool_response(self, tool_name: str, result: Any) -> str:
        """Format tool response for display"""
        if tool_name in ['get_entries', 'get_line_by_id']:
            # JSON format for data retrieval tools
            if isinstance(result, str) and "No entry found" in result:
                return "No entries found"
            elif isinstance(result, list) and len(result) == 0:
                return "No entries found"
            else:
                if tool_name == 'get_entries':
                    return f"📋 JSON Results ({len(result)} entries):\n```json\n{json.dumps(result, indent=2)}\n```"
                else:  # get_line_by_id
                    return f"📄 JSON Entry Details:\n```json\n{json.dumps(result, indent=2)}\n```"
        else:
            # Human language format for other tools
            if isinstance(result, int):
                return f"🔢 Result: {result}"
            elif isinstance(result, str):
                return result
            else:
                return str(result)
    
    def get_system_prompt(self) -> str:
        """Enhanced system prompt with multiple filter examples"""
        base_prompt = super().get_system_prompt()
        
        enhanced_prompt = base_prompt + """

Available filter arguments for count_entries and get_entries:
  - 'date': 'DD/MM/YYYY' (e.g., '29/07/2025')
  - 'time': 'HH:MM' or 'HH' (e.g., '13:30' or '13')
  - 'datetime': 'DD/MM/YYYY HH:MM' (combined format)
  - 'internal_ip': IP address (e.g., '107.78.99.191')
  - 'external_ip': IP address
  - 'action': action type (e.g., 'Blocked', 'Allowed')
  - 'destination': destination URL/domain
  - 'policy_identity': policy name
You can combine multiple filters in one query!

Examples:
  User: How many entries from 29/07/2025?
  Assistant: {"name":"count_entries","arguments":{"date":"29/07/2025"}}
  
  User: Get me lines with internal ip 107.78.99.191 and happened at 29/07/2025 13:13
  Assistant: {"name":"get_entries","arguments":{"internal_ip":"107.78.99.191","date":"29/07/2025","time":"13:13"}}
  
  User: Count blocked entries from internal IP 192.168.1.1 on 30/07/2025
  Assistant: {"name":"count_entries","arguments":{"action":"Blocked","internal_ip":"192.168.1.1","date":"30/07/2025"}}"""
        
        return enhanced_prompt
    
    def refresh_data(self):
        """Refresh CSV data"""
        if self.csv_watcher:
            self.csv_watcher.process_existing_files()
            st.success("✅ CSV data refreshed")
        else:
            st.error("❌ CSV watcher not initialized")
