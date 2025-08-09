#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Client Utility
"""
import json
import subprocess
import streamlit as st
import time
import threading
import sys
from typing import Dict, Any, List, Optional

class MCPClient:
    """Client for communicating with MCP servers"""
    
    def __init__(self, server_path: str, client_name: str, client_version: str):
        self.server_path = server_path
        self.client_name = client_name
        self.client_version = client_version
        self.process = None
        self.rpc_id_counter = 100
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for MCP server output"""
        self.log_prefix = f"[MCP-{self.client_name}]"
    
    def _log_server_output(self):
        """Monitor and log MCP server stderr output"""
        while self.process and self.process.poll() is None:
            try:
                line = self.process.stderr.readline()
                if line:
                    # Print to Docker logs with prefix
                    print(f"{self.log_prefix} SERVER: {line.strip()}", flush=True)
            except:
                break
    
    def initialize(self) -> List[Dict[str, Any]]:
        """Initialize MCP connection and return available tools"""
        try:
            print(f"{self.log_prefix} Starting MCP server: {self.server_path}", flush=True)
            
            # Start the MCP server process
            self.process = subprocess.Popen(
                [self.server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0  # Unbuffered for real-time communication
            )
            
            print(f"{self.log_prefix} MCP server started, PID: {self.process.pid}", flush=True)
            
            # Start stderr monitoring thread
            stderr_thread = threading.Thread(target=self._log_server_output, daemon=True)
            stderr_thread.start()
            
            # Give the process a moment to start
            time.sleep(0.2)
            
            # Send initialization messages
            init_messages = [
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"sampling": {}, "roots": {"listChanged": True}},
                        "clientInfo": {"name": self.client_name, "version": self.client_version}
                    }
                },
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
            ]
            
            print(f"{self.log_prefix} Sending initialization messages...", flush=True)
            
            # Send initialization messages one by one
            for i, msg in enumerate(init_messages):
                print(f"{self.log_prefix} Sending message {i+1}: {msg['method']}", flush=True)
                self._send_message(msg)
                time.sleep(0.1)  # Small delay between messages
            
            # Wait for tools list response
            tools = []
            max_attempts = 20
            attempts = 0
            
            print(f"{self.log_prefix} Waiting for tools list response...", flush=True)
            
            while attempts < max_attempts:
                msg = self._read_json_line()
                if msg:
                    print(f"{self.log_prefix} Received message: {json.dumps(msg)[:200]}...", flush=True)
                    
                    if msg.get("id") == 1 and "result" in msg:
                        tools = msg["result"].get("tools", [])
                        print(f"{self.log_prefix} Found {len(tools)} tools", flush=True)
                        break
                    elif msg.get("id") == 1 and "error" in msg:
                        raise Exception(f"MCP initialization error: {msg['error']}")
                
                attempts += 1
                time.sleep(0.1)
            
            if not tools and attempts >= max_attempts:
                raise Exception("Timeout waiting for tools list")
            
            print(f"{self.log_prefix} MCP initialization successful!", flush=True)
            return tools
            
        except Exception as e:
            print(f"{self.log_prefix} MCP initialization failed: {str(e)}", flush=True)
            if self.process:
                self.process.kill()
                self.process = None
            raise Exception(f"Failed to initialize MCP client: {str(e)}")
    
    def _send_message(self, message: Dict[str, Any]):
        """Send a message to the MCP server"""
        if not self.process:
            raise Exception("MCP process not running")
        
        json_str = json.dumps(message) + "\n"
        print(f"{self.log_prefix} SENDING: {json_str.strip()}", flush=True)
        
        self.process.stdin.write(json_str)
        self.process.stdin.flush()
    
    def _read_json_line(self) -> Optional[Dict[str, Any]]:
        """Read and parse a JSON line from the MCP server"""
        if not self.process:
            return None
            
        try:
            # Set a reasonable timeout for reading
            line = self.process.stdout.readline()
            if not line:
                return None
                
            line = line.strip()
            if not line:
                return None
            
            print(f"{self.log_prefix} RECEIVED: {line}", flush=True)
            return json.loads(line)
        except json.JSONDecodeError as e:
            print(f"{self.log_prefix} JSON decode error: {e}, line: {line}", flush=True)
            return None
        except Exception as e:
            print(f"{self.log_prefix} Error reading from MCP server: {e}", flush=True)
            return None
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server"""
        if not self.process:
            raise Exception("MCP client not initialized")
        
        # Generate unique ID for this call
        self.rpc_id_counter += 1
        call_id = self.rpc_id_counter
        
        print(f"{self.log_prefix} Calling tool '{tool_name}' with arguments: {arguments}", flush=True)
        
        # Prepare RPC call
        rpc_call = {
            "jsonrpc": "2.0",
            "id": call_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Send the call
        try:
            self._send_message(rpc_call)
        except Exception as e:
            print(f"{self.log_prefix} Failed to send tool call: {str(e)}", flush=True)
            raise Exception(f"Failed to send MCP call: {str(e)}")
        
        # Wait for response with timeout
        response = None
        max_attempts = 50  # 5 second timeout
        attempts = 0
        
        print(f"{self.log_prefix} Waiting for tool response (ID: {call_id})...", flush=True)
        
        while attempts < max_attempts:
            msg = self._read_json_line()
            if not msg:
                attempts += 1
                time.sleep(0.1)
                continue
                
            # Check if this is our response
            if msg.get("id") == call_id:
                response = msg
                print(f"{self.log_prefix} Received tool response for ID {call_id}", flush=True)
                break
                
            attempts += 1
            time.sleep(0.1)
        
        if not response:
            print(f"{self.log_prefix} Timeout waiting for tool response after {max_attempts} attempts", flush=True)
            raise Exception("Timeout waiting for MCP response")
        
        # Handle response
        if "error" in response:
            error_msg = response["error"].get("message", "Unknown MCP error")
            print(f"{self.log_prefix} Tool call error: {error_msg}", flush=True)
            raise Exception(f"MCP tool error: {error_msg}")
        
        if "result" not in response:
            print(f"{self.log_prefix} Invalid response: missing result", flush=True)
            raise Exception("Invalid MCP response: missing result")
        
        # Extract the content from the MCP response
        result = response["result"]
        print(f"{self.log_prefix} Tool call successful, result type: {type(result)}", flush=True)
        
        # Handle different response formats
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            print(f"{self.log_prefix} Found content array with {len(content)} items", flush=True)
            
            if isinstance(content, list) and len(content) > 0:
                # Combine all content items instead of just taking the first one
                combined_text = []
                
                for i, item in enumerate(content):
                    print(f"{self.log_prefix} Processing content item {i+1}/{len(content)}", flush=True)
                    
                    if isinstance(item, dict) and "text" in item:
                        combined_text.append(item["text"])
                    elif isinstance(item, dict) and "raw" in item and isinstance(item["raw"], dict) and "text" in item["raw"]:
                        # Handle the format: {"raw": {"text": "..."}}
                        combined_text.append(item["raw"]["text"])
                    elif isinstance(item, str):
                        combined_text.append(item)
                    else:
                        combined_text.append(str(item))
                
                # Join all content with double newlines for separation
                final_result = "\n\n".join(combined_text)
                print(f"{self.log_prefix} Combined {len(content)} content items into {len(final_result)} characters", flush=True)
                
                return final_result
            
            return content
        
        return result
    
    def cleanup(self):
        """Cleanup MCP connection"""
        print(f"{self.log_prefix} Cleaning up MCP connection...", flush=True)
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print(f"{self.log_prefix} MCP server terminated gracefully", flush=True)
            except subprocess.TimeoutExpired:
                self.process.kill()
                print(f"{self.log_prefix} MCP server killed forcefully", flush=True)
            except Exception as e:
                print(f"{self.log_prefix} Error during cleanup: {e}", flush=True)
            finally:
                self.process = None
