#!/usr/bin/env python3
"""
Unified Security Platform - Main Streamlit Interface
Combines Tickets Manager, Wazuh Assistant, and TheHive Assistant
"""
import streamlit as st
from config import load_config
from ui.sidebar import render_sidebar
from assistants.tickets_manager.assistant import TicketsManagerAssistant
from assistants.wazuh.assistant import WazuhAssistant
from assistants.thehive.assistant import TheHiveAssistant

# Page configuration
st.set_page_config(
    page_title="🛡️ Unified Security Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Load configuration
    config = load_config()
    
    # Initialize session state
    if 'current_assistant' not in st.session_state:
        st.session_state.current_assistant = 'tickets_manager'
    if 'assistants_initialized' not in st.session_state:
        st.session_state.assistants_initialized = {}
    
    # Render sidebar and get selected assistant
    selected_assistant = render_sidebar()
    st.session_state.current_assistant = selected_assistant
    
    # Main content area
    st.title("🛡️ Unified Security Platform")
    
    # Initialize and run the selected assistant
    try:
        if selected_assistant == 'tickets_manager':
            print(f"🔍 DEBUG: Selected Tickets Manager assistant")
            if 'tickets_manager' not in st.session_state.assistants_initialized:
                print(f"🔍 DEBUG: Tickets Manager not initialized, creating...")
                st.session_state.tickets_manager = TicketsManagerAssistant(config)
                st.session_state.assistants_initialized['tickets_manager'] = True
                print(f"🔍 DEBUG: Tickets Manager initialized")
            st.session_state.tickets_manager.run()
            
        elif selected_assistant == 'wazuh':
            print(f"🔍 DEBUG: Selected Wazuh assistant")
            
            if 'wazuh' not in st.session_state.assistants_initialized:
                print(f"🔍 DEBUG: Wazuh not initialized, creating...")
                st.session_state.wazuh = WazuhAssistant(config)
                print(f"🔍 DEBUG: WazuhAssistant created")
                st.session_state.assistants_initialized['wazuh'] = True
                print(f"🔍 DEBUG: Wazuh marked as initialized")
            else:
                print(f"🔍 DEBUG: Wazuh already initialized")
                
            print(f"🔍 DEBUG: About to run Wazuh assistant")
            st.session_state.wazuh.run()
            
        elif selected_assistant == 'thehive':
            print(f"🔍 DEBUG: Selected TheHive assistant")
            
            if 'thehive' not in st.session_state.assistants_initialized:
                print(f"🔍 DEBUG: TheHive not initialized, creating...")
                st.session_state.thehive = TheHiveAssistant(config)
                print(f"🔍 DEBUG: TheHiveAssistant created")
                st.session_state.assistants_initialized['thehive'] = True
                print(f"🔍 DEBUG: TheHive marked as initialized")
            else:
                print(f"🔍 DEBUG: TheHive already initialized")
                
            print(f"🔍 DEBUG: About to run TheHive assistant")
            st.session_state.thehive.run()
            
    except Exception as e:
        print(f"🔍 DEBUG: Exception in main(): {e}")
        import traceback
        traceback.print_exc()
        st.error(f"Error initializing {selected_assistant}: {str(e)}")
        st.info("Please check your configuration and try again.")

if __name__ == "__main__":
    main()
