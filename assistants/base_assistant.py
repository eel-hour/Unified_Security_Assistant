#!/usr/bin/env python3
"""
Base assistant class for the unified security platform
"""
import json
import streamlit as st
import google.generativeai as genai
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from config import AppConfig

class BaseAssistant(ABC):
    """Base class for all assistants"""
    
    def __init__(self, config: AppConfig, assistant_name: str):
        self.config = config
        self.assistant_name = assistant_name
        self.model = self._setup_gemini()
        
        # Initialize session state keys
        self.messages_key = f'{assistant_name}_messages'
        self.initialized_key = f'{assistant_name}_initialized'
        
        # Initialize messages if not exists
        if self.messages_key not in st.session_state:
            st.session_state[self.messages_key] = []
    
    def _setup_gemini(self):
        """Setup Gemini AI model"""
        genai.configure(api_key=self.config.gemini.api_key)
        return genai.GenerativeModel(self.config.gemini.model)
    
    @abstractmethod
    def get_tool_definitions(self) -> Dict[str, Any]:
        """Return tool definitions for this assistant"""
        pass
    
    @abstractmethod
    def initialize_resources(self):
        """Initialize assistant-specific resources (DB, MCP, etc.)"""
        pass
    
    @abstractmethod
    def cleanup_resources(self):
        """Cleanup assistant-specific resources"""
        pass
    
    @abstractmethod
    def handle_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Handle tool execution"""
        pass
    
    @abstractmethod
    def format_tool_response(self, tool_name: str, result: Any) -> str:
        """Format tool response for display"""
        pass
    
    def get_system_prompt(self) -> str:
        """Generate system prompt for this assistant"""
        tool_definitions = self.get_tool_definitions()
        
        tool_list = []
        for name, spec in tool_definitions.items():
            if name == "none":
                continue
            args_info = ', '.join(spec.get('required_args', [])) or 'None'
            tool_list.append(f"- {name}: {spec['description']} (Required args: {args_info})")
        
        return f"""You are a specialized AI assistant with access to these tools:
{chr(10).join(tool_list)}

When you need to use a tool, respond with ONLY valid JSON:
{{"name": "tool_name", "arguments": {{...}}}}

For queries that combine multiple filters, include all relevant arguments in the JSON.
If you can answer without tools, respond naturally."""
    
    def render_chat_interface(self):
        """Render the chat interface"""
        messages = st.session_state[self.messages_key]
        
        # Display chat history
        for msg in messages:
            with st.chat_message(msg['role']):
                if isinstance(msg['content'], str):
                    st.markdown(msg['content'])
                elif isinstance(msg['content'], dict):
                    self._render_complex_content(msg['content'])
        
        # Handle user input
        if prompt := st.chat_input(f"Ask your {self.assistant_name} question..."):
            # Add user message
            messages.append({'role': 'user', 'content': prompt})
            with st.chat_message('user'):
                st.markdown(prompt)
            
            # Process the prompt
            self._process_user_prompt(prompt)
    
    def _render_complex_content(self, content: Dict[str, Any]):
        """Render complex content types"""
        if content.get('type') == 'tool_result':
            st.markdown(f"**{content['name']} Results**")
            st.json(content['result'])
            if 'summary' in content:
                st.markdown(f"**Summary:** {content['summary']}")
        elif content.get('type') == 'tool_listing':
            st.markdown("### Available Tools:")
            for tool in content['tools']:
                st.markdown(f"**{tool['name']}**: {tool.get('description', '')}")
        else:
            st.json(content)
    
    def _process_user_prompt(self, prompt: str):
        """Process user prompt and generate response"""
        messages = st.session_state[self.messages_key]
        
        try:
            print(f"🔍 DEBUG: Processing prompt for {self.assistant_name}: {prompt}")
            
            # Check for special commands first
            if self._handle_special_commands(prompt):
                return
            
            # Generate response using Gemini
            system_prompt = self.get_system_prompt()
            response = self.model.generate_content(system_prompt + f"\nUser: {prompt}")
            raw_response = response.text.strip()
            
            print(f"🔍 DEBUG: Gemini response: {raw_response}")
            
            # Try to parse as tool call - handle both pure JSON and markdown-wrapped JSON
            json_content = self._extract_json_from_response(raw_response)
            
            if json_content:
                try:
                    tool_call = json.loads(json_content)
                    if 'name' in tool_call and 'arguments' in tool_call:
                        print(f"🔍 DEBUG: Detected tool call: {tool_call}")
                        self._execute_tool_call(tool_call)
                        return
                except json.JSONDecodeError as e:
                    print(f"🔍 DEBUG: JSON parsing failed: {e}")
            
            print(f"🔍 DEBUG: Not a tool call, treating as natural language")
            
            # Regular text response
            messages.append({'role': 'assistant', 'content': raw_response})
            with st.chat_message('assistant'):
                st.markdown(raw_response)
                
        except Exception as e:
            print(f"🔍 DEBUG: Exception in _process_user_prompt: {e}")
            import traceback
            traceback.print_exc()
            
            error_msg = f"Error processing request: {str(e)}"
            messages.append({'role': 'assistant', 'content': error_msg})
            with st.chat_message('assistant'):
                st.error(error_msg)
    
    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """Extract JSON from response, handling both pure JSON and markdown-wrapped JSON"""
        response = response.strip()
        
        # Try direct JSON parsing first
        if response.startswith('{') and response.endswith('}'):
            print(f"🔍 DEBUG: Found pure JSON")
            return response
        
        # Try to extract JSON from markdown code blocks
        import re
        
        # Pattern for ```json ... ``` blocks
        json_pattern = r'```(?:json)?\s*\n?(\{.*?\})\s*\n?```'
        match = re.search(json_pattern, response, re.DOTALL)
        
        if match:
            json_content = match.group(1).strip()
            print(f"🔍 DEBUG: Found JSON in markdown: {json_content}")
            return json_content
        
        # Pattern for ``` ... ``` blocks (without json tag)
        generic_pattern = r'```\s*\n?(\{.*?\})\s*\n?```'
        match = re.search(generic_pattern, response, re.DOTALL)
        
        if match:
            json_content = match.group(1).strip()
            print(f"🔍 DEBUG: Found JSON in generic markdown: {json_content}")
            return json_content
        
        # Look for JSON-like content without markdown
        json_like_pattern = r'(\{"name":\s*"[^"]+",\s*"arguments":\s*\{.*?\}\})'
        match = re.search(json_like_pattern, response, re.DOTALL)
        
        if match:
            json_content = match.group(1).strip()
            print(f"🔍 DEBUG: Found JSON-like content: {json_content}")
            return json_content
        
        print(f"🔍 DEBUG: No JSON found in response")
        return None
    
    def _handle_special_commands(self, prompt: str) -> bool:
        """Handle special commands like 'list tools'"""
        lower_prompt = prompt.lower().strip()
        messages = st.session_state[self.messages_key]
        
        if any(phrase in lower_prompt for phrase in ["list tools", "available tools", "show tools"]):
            tool_definitions = self.get_tool_definitions()
            tool_list = []
            
            for name, spec in tool_definitions.items():
                if name == "none":
                    continue
                tool_list.append({
                    'name': name,
                    'description': spec['description'],
                    'required_args': spec.get('required_args', []),
                    'optional_args': spec.get('optional_args', [])
                })
            
            messages.append({
                'role': 'assistant',
                'content': {'type': 'tool_listing', 'tools': tool_list}
            })
            
            with st.chat_message('assistant'):
                st.markdown("### Available Tools:")
                for tool in tool_list:
                    st.markdown(f"**{tool['name']}**: {tool['description']}")
                    if tool['required_args']:
                        st.markdown(f"- **Required**: {', '.join(tool['required_args'])}")
                    if tool['optional_args']:
                        st.markdown(f"- **Optional**: {', '.join(tool['optional_args'])}")
                    st.markdown("---")
            
            return True
        
        return False
    
    def _execute_tool_call(self, tool_call: Dict[str, Any]):
        """Execute a tool call"""
        messages = st.session_state[self.messages_key]
        tool_name = tool_call['name']
        args = tool_call['arguments']
        
        print(f"🔍 DEBUG: Executing tool {tool_name} with args {args}")
        
        try:
            # Validate tool exists
            tool_definitions = self.get_tool_definitions()
            if tool_name not in tool_definitions:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            print(f"🔍 DEBUG: Tool found in definitions")
            
            # Validate required arguments
            spec = tool_definitions[tool_name]
            missing_args = [arg for arg in spec.get('required_args', []) if arg not in args]
            if missing_args:
                raise ValueError(f"Missing required arguments: {', '.join(missing_args)}")
            
            print(f"🔍 DEBUG: Arguments validated")
            
            # Show tool execution
            with st.chat_message('assistant'):
                st.markdown(f"**Executing:** `{tool_name}` with arguments `{args}`")
            
            print(f"🔍 DEBUG: About to call handle_tool_call")
            
            # Execute the tool
            result = self.handle_tool_call(tool_name, args)
            
            print(f"🔍 DEBUG: Tool returned: {type(result)} - {str(result)[:100]}...")
            
            # Format and display result
            formatted_result = self.format_tool_response(tool_name, result)
            messages.append({'role': 'assistant', 'content': formatted_result})
            
            with st.chat_message('assistant'):
                st.markdown(formatted_result)
                
        except Exception as e:
            print(f"🔍 DEBUG: Exception in _execute_tool_call: {e}")
            import traceback
            traceback.print_exc()
            
            error_msg = f"Tool execution error: {str(e)}"
            messages.append({'role': 'assistant', 'content': error_msg})
            with st.chat_message('assistant'):
                st.error(error_msg)
    
    def run(self):
        """Main run method for the assistant"""
        try:
            # Initialize resources if not done
            if not st.session_state.get(self.initialized_key, False):
                self.initialize_resources()
                st.session_state[self.initialized_key] = True
            
            # Show assistant header
            st.markdown(f"## {self.get_display_name()}")
            st.markdown(f"*{self.get_description()}*")
            st.markdown("---")
            
            # Render chat interface
            self.render_chat_interface()
            
        except Exception as e:
            st.error(f"Error running {self.assistant_name}: {str(e)}")
    
    @abstractmethod
    def get_display_name(self) -> str:
        """Get display name for the assistant"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get description for the assistant"""
        pass
