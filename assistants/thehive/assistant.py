#!/usr/bin/env python3
"""
TheHive Assistant - MCP integration for TheHive case management
"""
import json
import streamlit as st
from typing import Dict, Any
from utils.mcp_client import MCPClient
from assistants.base_assistant import BaseAssistant
from assistants.thehive.tool_definitions import TOOL_DEFINITIONS

class TheHiveAssistant(BaseAssistant):
    """TheHive Assistant for case management via MCP"""
    
    def __init__(self, config):
        super().__init__(config, 'thehive')
        self.mcp_client = None
        self.tools = []
    
    def get_display_name(self) -> str:
        return "🕵️ TheHive Assistant"
    
    def get_description(self) -> str:
        return "Manage security cases and incidents through TheHive platform"
    
    def get_tool_definitions(self) -> Dict[str, Any]:
        return TOOL_DEFINITIONS
    
    def initialize_resources(self):
        """Initialize MCP connection to TheHive server"""
        try:
            self.mcp_client = MCPClient(
                server_path=self.config.mcp.thehive_server_path,
                client_name="thehive-assistant",
                client_version="0.1.0"
            )
            
            # Initialize and get available tools
            self.tools = self.mcp_client.initialize()
            st.session_state.thehive_mcp_proc = self.mcp_client.process
            
            st.success(f"✅ Connected to TheHive MCP server ({len(self.tools)} tools available)")
            
        except Exception as e:
            st.error(f"Failed to connect to TheHive MCP server: {str(e)}")
            raise
    
    def cleanup_resources(self):
        """Cleanup MCP connection"""
        if self.mcp_client:
            self.mcp_client.cleanup()
    
    def handle_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Handle tool execution via MCP"""
        if not self.mcp_client:
            raise Exception("MCP client not initialized")
        
        # Format IDs with tilde prefix if needed
        for key in ["id", "case_id", "alert_id", "observable_id", "task_id"]:
            if key in args:
                args[key] = self._format_id(args[key])
        
        # Execute tool via MCP
        result = self.mcp_client.call_tool(tool_name, args)
        return result
    
    def _format_id(self, id_value: str) -> str:
        """Ensure ID has tilde prefix for TheHive"""
        id_str = str(id_value)
        if not id_str.startswith("~"):
            return "~" + id_str
        return id_str
    
    def format_tool_response(self, tool_name: str, result: Any) -> str:
        """Format MCP tool response for display"""
        try:
            # Generate summary using Gemini
            summary_prompt = f"Summarize the following TheHive {tool_name} results for a SOC analyst:\n{json.dumps(result)}"
            summary_response = self.model.generate_content(summary_prompt)
            summary = summary_response.text
            
            # Format the response
            if isinstance(result, list):
                count_info = f" ({len(result)} items)"
            else:
                count_info = ""
            
            formatted = f"### {tool_name} Results{count_info}\n\n"
            formatted += f"**Raw Data:**\n```json\n{json.dumps(result, indent=2)}\n```\n\n"
            formatted += f"**Summary:**\n{summary}"
            
            return formatted
            
        except Exception as e:
            # Fallback to basic formatting
            return f"### {tool_name} Results\n\n```json\n{json.dumps(result, indent=2)}\n```\n\n*Summary generation failed: {str(e)}*"
    
    def get_system_prompt(self) -> str:
        """Enhanced system prompt for TheHive operations"""
        base_prompt = super().get_system_prompt()
        
        enhanced_prompt = base_prompt + """

You are specialized in TheHive case management. When users ask about:
- Cases: use list_cases, get_case, create_case
- Alerts: use list_alerts, get_alert, create_alert  
- Observables: use list_observables, get_observable
- Tasks: use list_tasks, get_task

IMPORTANT: TheHive IDs must be prefixed with tilde (~). The system handles this automatically.
Provide actionable insights for incident response teams."""
        
        return enhanced_prompt
