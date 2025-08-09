#!/usr/bin/env python3
"""
Sidebar navigation component for the unified security platform
"""
import streamlit as st

def render_sidebar() -> str:
    """Render the navigation sidebar and return selected assistant"""
    
    with st.sidebar:
        st.title("🛡️ Security Platform")
        st.markdown("---")
        
        # Assistant selection
        st.subheader("🤖 Assistants")
        
        assistant_options = {
            "tickets_manager": {
                "name": "📋 Tickets Manager",
                "description": "CSV log analysis and querying",
                "tool_count": "6 tools",
                "example_tools": ["count_entries", "get_entries", "count_lines"]
            },
            "wazuh": {
                "name": "🔍 Wazuh Assistant", 
                "description": "Wazuh SIEM integration",
                "tool_count": "14 tools",
                "example_tools": ["get_wazuh_agents", "get_wazuh_alerts", "search_wazuh_manager_logs"]
            },
            "thehive": {
                "name": "🕵️ TheHive Assistant",
                "description": "TheHive case management",
                "tool_count": "6 tools", 
                "example_tools": ["get_thehive_cases", "create_thehive_case", "get_thehive_alerts"]
            }
        }
        
        # Get current selection
        current = st.session_state.get('current_assistant', 'tickets_manager')
        
        # Create radio buttons for assistant selection
        selected = st.radio(
            "Choose an assistant:",
            options=list(assistant_options.keys()),
            format_func=lambda x: assistant_options[x]["name"],
            index=list(assistant_options.keys()).index(current)
        )
        
        # Show detailed info of selected assistant
        selected_info = assistant_options[selected]
        st.info(f"**{selected_info['description']}**\n\n**Available:** {selected_info['tool_count']}\n\n**Examples:** {', '.join(selected_info['example_tools'])}")
        
        # Add note about tools
        st.markdown("💡 **Tip:** Each assistant has different tools. Ask 'what tools do you have' to see the current assistant's capabilities.")
        
        st.markdown("---")
        
        # System status
        st.subheader("📊 System Status")
        
        # Database status
        if hasattr(st.session_state, 'database_connected'):
            db_status = "🟢 Connected" if st.session_state.database_connected else "🔴 Disconnected"
        else:
            db_status = "🟡 Unknown"
        st.write(f"Database: {db_status}")
        
        # CSV Watcher status (for tickets manager)
        if selected == 'tickets_manager':
            if hasattr(st.session_state, 'watcher'):
                watcher_status = "🟢 Running" if st.session_state.watcher else "🔴 Stopped"
            else:
                watcher_status = "🟡 Not Started"
            st.write(f"CSV Watcher: {watcher_status}")
        
        # MCP Server status (for Wazuh/TheHive)
        if selected in ['wazuh', 'thehive']:
            mcp_key = f'{selected}_mcp_proc'
            if hasattr(st.session_state, mcp_key):
                mcp_proc = getattr(st.session_state, mcp_key)
                if mcp_proc and hasattr(mcp_proc, 'poll') and mcp_proc.poll() is None:
                    mcp_status = "🟢 Connected"
                else:
                    mcp_status = "🔴 Disconnected"
            else:
                mcp_status = "🟡 Not Connected"
            st.write(f"MCP Server: {mcp_status}")
        
        st.markdown("---")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        if selected == 'tickets_manager':
            if st.button("🔄 Refresh CSV Data"):
                if hasattr(st.session_state, 'tickets_manager'):
                    st.session_state.tickets_manager.refresh_data()
                st.rerun()
        
        elif selected in ['wazuh', 'thehive']:
            if st.button("🔄 Reconnect MCP"):
                # Clear MCP connection to force reconnection
                mcp_key = f'{selected}_mcp_proc'
                if hasattr(st.session_state, mcp_key):
                    delattr(st.session_state, mcp_key)
                if selected in st.session_state.assistants_initialized:
                    del st.session_state.assistants_initialized[selected]
                st.rerun()
            
            # Debug button for Wazuh
            if selected == 'wazuh':
                if st.button("🔧 Force Wazuh Init"):
                    try:
                        from assistants.wazuh.assistant import WazuhAssistant
                        from config import load_config
                        
                        config = load_config()
                        assistant = WazuhAssistant(config)
                        assistant.initialize_resources()
                        
                        # Force session state update
                        st.session_state.wazuh = assistant
                        st.session_state.assistants_initialized['wazuh'] = True
                        st.session_state.wazuh_mcp_proc = assistant.mcp_client.process
                        st.session_state.wazuh_initialized = True
                        
                        st.success("✅ Wazuh assistant force-initialized!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Force init failed: {e}")
                        st.code(str(e))
                
                # Debug info button
                if st.button("🧪 Debug Wazuh Status"):
                    st.write("**Debug Info:**")
                    st.write(f"- assistants_initialized: {st.session_state.get('assistants_initialized', {})}")
                    st.write(f"- wazuh in session: {'wazuh' in st.session_state.__dict__}")
                    st.write(f"- wazuh_mcp_proc in session: {'wazuh_mcp_proc' in st.session_state.__dict__}")
                    st.write(f"- wazuh_initialized in session: {'wazuh_initialized' in st.session_state.__dict__}")
                    
                    if hasattr(st.session_state, 'wazuh'):
                        wazuh_assistant = st.session_state.wazuh
                        st.write(f"- MCP client exists: {wazuh_assistant.mcp_client is not None}")
                        if wazuh_assistant.mcp_client:
                            st.write(f"- MCP process: {wazuh_assistant.mcp_client.process}")
                            st.write(f"- Tools found: {len(wazuh_assistant.tools)}")
            
            # Debug button for TheHive
            if selected == 'thehive':
                if st.button("🔧 Force TheHive Init"):
                    try:
                        from assistants.thehive.assistant import TheHiveAssistant
                        from config import load_config
                        
                        config = load_config()
                        assistant = TheHiveAssistant(config)
                        assistant.initialize_resources()
                        
                        # Force session state update
                        st.session_state.thehive = assistant
                        st.session_state.assistants_initialized['thehive'] = True
                        st.session_state.thehive_mcp_proc = assistant.mcp_client.process
                        st.session_state.thehive_initialized = True
                        
                        st.success("✅ TheHive assistant force-initialized!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Force init failed: {e}")
                        st.code(str(e))
        
        # Clear chat history
        if st.button("🗑️ Clear Chat History"):
            # Clear messages for current assistant
            chat_key = f'{selected}_messages'
            if chat_key in st.session_state:
                del st.session_state[chat_key]
            st.rerun()
        
        # Emergency stop
        if st.button("🚨 Emergency Stop", type="secondary"):
            # Stop all processes and clear session
            for key in list(st.session_state.keys()):
                if 'proc' in key or 'watcher' in key:
                    try:
                        process = getattr(st.session_state, key)
                        if hasattr(process, 'stop'):
                            process.stop()
                        elif hasattr(process, 'kill'):
                            process.kill()
                    except:
                        pass
            st.session_state.clear()
            st.rerun()
        
        st.markdown("---")
        
        # Tool overview for all assistants
        st.subheader("🛠️ Available Tools")
        for key, info in assistant_options.items():
            icon = "👉" if key == selected else "  "
            st.markdown(f"{icon} **{info['name']}**: {info['tool_count']}")
        
        st.markdown("---")
        st.markdown("**💡 Tips:**")
        st.markdown("• Switch assistants to access different tools")
        st.markdown("• Each assistant maintains separate chat history")  
        st.markdown("• Ask 'list tools' to see current capabilities")
    
    return selected
