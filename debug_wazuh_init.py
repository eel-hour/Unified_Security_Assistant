#!/usr/bin/env python3
import sys
sys.path.append('/app')

try:
    print("🔍 Testing Wazuh Assistant Initialization...")
    
    from config import load_config
    print("✅ Config loaded")
    
    from assistants.wazuh.assistant import WazuhAssistant
    print("✅ WazuhAssistant imported")
    
    config = load_config()
    print("✅ Config created")
    
    assistant = WazuhAssistant(config)
    print("✅ WazuhAssistant created")
    
    print("🔍 Initializing resources...")
    assistant.initialize_resources()
    print("✅ Resources initialized successfully!")
    
    print(f"MCP Client: {assistant.mcp_client}")
    print(f"Tools found: {len(assistant.tools)}")
    
except Exception as e:
    print(f"❌ Error during initialization: {e}")
    import traceback
    traceback.print_exc()
