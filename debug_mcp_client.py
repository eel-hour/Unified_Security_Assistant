#!/usr/bin/env python3
import sys
sys.path.append('/app')

try:
    print("🔍 Testing MCP Client...")
    
    from utils.mcp_client import MCPClient
    print("✅ MCPClient imported successfully")
    
    # Test initialization
    client = MCPClient(
        server_path="/app/mcp-servers/mcp-server-wazuh-linux-amd64",
        client_name="debug-test",
        client_version="1.0"
    )
    print("✅ MCPClient created successfully")
    
    # Test initialization
    print("🔍 Initializing MCP client...")
    tools = client.initialize()
    print(f"✅ MCP client initialized successfully! Found {len(tools)} tools")
    
    for tool in tools:
        print(f"  - {tool.get('name', 'unknown')}")
    
    # Test a tool call
    print("🔍 Testing tool call...")
    result = client.call_tool("get_wazuh_agents", {"status": "active"})
    print(f"✅ Tool call successful! Result: {result[:200]}...")
    
    client.cleanup()
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
