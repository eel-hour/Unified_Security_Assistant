#!/usr/bin/env python3
"""
Wazuh Assistant - MCP integration for Wazuh SIEM
"""
import json
import streamlit as st
from typing import Dict, Any
from utils.mcp_client import MCPClient
from assistants.base_assistant import BaseAssistant
from assistants.wazuh.tool_definitions import TOOL_DEFINITIONS

class WazuhAssistant(BaseAssistant):
    """Wazuh Assistant for SIEM integration via MCP"""
    
    def __init__(self, config):
        super().__init__(config, 'wazuh')
        self.mcp_client = None
        self.tools = []
    
    def get_display_name(self) -> str:
        return "🔍 Wazuh Assistant"
    
    def get_description(self) -> str:
        return "Interact with Wazuh SIEM through MCP server integration"
    
    def get_tool_definitions(self) -> Dict[str, Any]:
        return TOOL_DEFINITIONS
    
    def initialize_resources(self):
        """Initialize MCP connection to Wazuh server"""
        try:
            print("🔍 DEBUG: Starting Wazuh assistant initialization...")
            
            self.mcp_client = MCPClient(
                server_path=self.config.mcp.wazuh_server_path,
                client_name="wazuh-assistant",
                client_version="0.1.0"
            )
            print("🔍 DEBUG: MCPClient created")
            
            # Initialize and get available tools
            self.tools = self.mcp_client.initialize()
            print(f"🔍 DEBUG: MCP initialized, found {len(self.tools)} tools")
            
            st.session_state.wazuh_mcp_proc = self.mcp_client.process
            print("🔍 DEBUG: Session state updated")
            
            st.success(f"✅ Connected to Wazuh MCP server ({len(self.tools)} tools available)")
            
        except Exception as e:
            print(f"🔍 DEBUG: Exception in initialize_resources: {e}")
            import traceback
            traceback.print_exc()
            
            st.error(f"Failed to connect to Wazuh MCP server: {str(e)}")
            raise
    
    def cleanup_resources(self):
        """Cleanup MCP connection"""
        if self.mcp_client:
            self.mcp_client.cleanup()
    
    def handle_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Handle tool execution via MCP"""
        print(f"🔍 DEBUG: Wazuh handle_tool_call called: {tool_name} with {args}")
        
        if not self.mcp_client:
            print("🔍 DEBUG: MCP client not initialized!")
            raise Exception("MCP client not initialized")
        
        # Handle argument normalization
        if tool_name == "get_wazuh_agent_processes":
            if 'process_name' in args and 'search' not in args:
                args['search'] = args.pop('process_name')
        
        print(f"🔍 DEBUG: About to call MCP tool...")
        
        # Execute tool via MCP
        result = self.mcp_client.call_tool(tool_name, args)
        
        print(f"🔍 DEBUG: MCP tool returned: {type(result)}")
        print(f"🔍 DEBUG: Result length: {len(str(result))} characters")
        print(f"🔍 DEBUG: Result preview: {str(result)[:500]}...")
        
        return result
    
    def format_tool_response(self, tool_name: str, result: Any) -> str:
        """Format MCP tool response for display"""
        try:
            print(f"🔍 DEBUG: Formatting tool response for {tool_name}")
            print(f"🔍 DEBUG: Result type: {type(result)}, length: {len(str(result))}")
            
            # Handle the result - check if it's already formatted text or needs processing
            if isinstance(result, str):
                # If it's already formatted text from MCP, use it directly
                formatted_data = result
                
                # Try to parse it to understand structure for summary
                try:
                    # Count agents if this is agent-related
                    if "Agent ID:" in result:
                        agent_count = result.count("Agent ID:")
                        summary_context = f"Found {agent_count} agent(s). " + result[:1000]
                    else:
                        summary_context = result[:1000]  # First 1000 chars for summary
                except:
                    summary_context = str(result)[:1000]
                    
            else:
                # Convert non-string results to formatted text
                if isinstance(result, (dict, list)):
                    formatted_data = json.dumps(result, indent=2)
                    summary_context = json.dumps(result)
                else:
                    formatted_data = str(result)
                    summary_context = str(result)
            
            print(f"🔍 DEBUG: Formatted data length: {len(formatted_data)}")
            
            # Generate summary using Gemini with limited context
            try:
                summary_prompt = f"Provide a brief summary of this Wazuh {tool_name} data for a SOC analyst (max 3 sentences):\n{summary_context[:2000]}"
                summary_response = self.model.generate_content(summary_prompt)
                summary = summary_response.text.strip()
                print(f"🔍 DEBUG: Generated summary: {len(summary)} characters")
            except Exception as e:
                print(f"🔍 DEBUG: Summary generation failed: {e}")
                summary = f"Summary generation failed: {str(e)}"
            
            # Format the complete response
            formatted_response = f"### 🔍 {tool_name} Results\n\n"
            
            # Add summary first
            formatted_response += f"**📊 Summary:**\n{summary}\n\n"
            
            # Add raw data in expandable section for long content
            if len(formatted_data) > 2000:
                # Use Streamlit expander for long content
                formatted_response += f"**📋 Raw Data:** (Click to expand)\n"
                formatted_response += f"<details><summary>Show {len(formatted_data)} characters of data</summary>\n\n"
                formatted_response += f"```\n{formatted_data}\n```\n\n"
                formatted_response += f"</details>\n"
            else:
                # Show full data for shorter content
                formatted_response += f"**📋 Raw Data:**\n```\n{formatted_data}\n```\n"
            
            print(f"🔍 DEBUG: Final formatted response: {len(formatted_response)} characters")
            
            return formatted_response
            
        except Exception as e:
            print(f"🔍 DEBUG: Error formatting response: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback formatting
            fallback = f"### 🔍 {tool_name} Results\n\n"
            fallback += f"**⚠️ Formatting Error:** {str(e)}\n\n"
            fallback += f"**📋 Raw Data:**\n```\n{str(result)[:5000]}\n```\n"
            return fallback
    
    def get_system_prompt(self) -> str:
        """Enhanced system prompt for Wazuh operations"""
        base_prompt = super().get_system_prompt()
        
        enhanced_prompt = base_prompt + """

You are specialized in Wazuh SIEM operations. When users ask about:
- Agent information: use get_wazuh_agents
- Process monitoring: use get_wazuh_agent_processes  
- System information: use get_wazuh_agent_info
- Security events: use appropriate Wazuh tools

IMPORTANT: Respond with ONLY the JSON tool call, no additional text or markdown formatting.
Example: {"name": "get_wazuh_agents", "arguments": {"status": "active"}}

Always provide actionable insights for SOC analysts."""
        
        return enhanced_prompt
    
    def run(self):
        """Main run method for the assistant"""
        try:
            print(f"🔍 DEBUG: Wazuh run() called")
            print(f"🔍 DEBUG: initialized_key = {self.initialized_key}")
            print(f"🔍 DEBUG: session state has key: {st.session_state.get(self.initialized_key, 'NOT FOUND')}")
            
            # Initialize resources if not done
            if not st.session_state.get(self.initialized_key, False):
                print(f"🔍 DEBUG: Initializing Wazuh resources...")
                self.initialize_resources()
                st.session_state[self.initialized_key] = True
                print(f"🔍 DEBUG: Wazuh initialization complete, session state set")
            else:
                print(f"🔍 DEBUG: Wazuh already initialized, skipping")
            
            # Show assistant header
            st.markdown(f"## {self.get_display_name()}")
            st.markdown(f"*{self.get_description()}*")
            st.markdown("---")
            
            # Render chat interface
            print(f"🔍 DEBUG: Rendering Wazuh chat interface...")
            self.render_chat_interface()
            
        except Exception as e:
            print(f"🔍 DEBUG: Exception in Wazuh run(): {e}")
            import traceback
            traceback.print_exc()
            st.error(f"Error running {self.assistant_name}: {str(e)}")
