# tool_definitions.py

TOOL_DEFINITIONS = {
    "search_wazuh_manager_logs": {
        "description": "Searches Wazuh manager logs. Returns formatted log entries including timestamp, tag, level, and description. Supports filtering by limit, offset, level, tag, and a search term.",
        "required_args": ["level"],
        "optional_args": ["limit", "offset", "search_term", "tag"],
        "example_args": {}
    },
    "get_wazuh_remoted_stats": {
        "description": "Retrieves statistics from the Wazuh remoted daemon. Returns information about queue size, TCP sessions, event counts, and message traffic.",
        "required_args": [],
        "optional_args": [],
        "example_args": {}
    },
    "get_wazuh_weekly_stats": {
        "description": "Retrieves weekly statistics from the Wazuh manager. Returns a JSON object detailing various metrics aggregated over the past week.",
        "required_args": [],
        "optional_args": [],
        "example_args": {}
    },
    "get_wazuh_alert_summary": {
        "description": "Retrieves a summary of Wazuh security alerts. Returns formatted alert information including ID, timestamp, and description.",
        "required_args": [],
        "optional_args": ["limit"],
        "example_args": {}
    },
    "get_wazuh_cluster_nodes": {
        "description": "Retrieves a list of nodes in the Wazuh cluster. Returns formatted node information including name, type, version, IP, and status. Supports filtering by limit, offset, and node type.",
        "required_args": [],
        "optional_args": ["limit", "node_type", "offset"],
        "example_args": {}
    },
    "get_wazuh_critical_vulnerabilities": {
        "description": "Retrieves critical vulnerabilities for a specific Wazuh agent. Returns formatted vulnerability information including CVE ID, title, description, CVSS scores, and detection details. Only shows vulnerabilities with 'Critical' severity level.",
        "required_args": ["agent_id"],
        "optional_args": ["limit"],
        "example_args": {}
    },
    "get_wazuh_agents": {
        "description": "Retrieves a list of Wazuh agents with their current status and details. Returns formatted agent information including ID, name, IP, status, OS details, and last activity. Supports filtering by status, name, IP, group, OS platform, and version.",
        "required_args": ["status"],
        "optional_args": ["group", "ip", "limit", "name", "os_platform", "version"],
        "example_args": {}
    },
    "get_wazuh_manager_error_logs": {
        "description": "Retrieves Wazuh manager error logs. Returns formatted log entries including timestamp, tag, level (error), and description.",
        "required_args": [],
        "optional_args": ["limit"],
        "example_args": {}
    },
    "get_wazuh_vulnerability_summary": {
        "description": "Retrieves a summary of Wazuh vulnerability detections for a specific agent. Returns formatted vulnerability information including CVE ID, severity, detection time, and agent details. Supports filtering by severity level.",
        "required_args": ["agent_id"],
        "optional_args": ["cve", "limit", "severity"],
        "example_args": {}
    },
    "get_wazuh_log_collector_stats": {
        "description": "Retrieves log collector statistics for a specific Wazuh agent. Returns information about events processed, dropped, bytes, and target log files.",
        "required_args": ["agent_id"],
        "optional_args": [],
        "example_args": {}
    },
    "get_wazuh_cluster_health": {
        "description": "Checks the health of the Wazuh cluster. Returns whether the cluster is enabled, running, and if nodes are connected.",
        "required_args": [],
        "optional_args": [],
        "example_args": {}
    },
    "get_wazuh_agent_processes": {
        "description": "Retrieves a list of running processes for a specific Wazuh agent. Returns formatted process information including PID, name, state, user, and command. Supports filtering by process name/command.",
        "required_args": ["agent_id"],
        "optional_args": ["limit", "search"],
        "example_args": {}
    },
    "get_wazuh_agent_ports": {
        "description": "Retrieves a list of open network ports for a specific Wazuh agent. Returns formatted port information including local/remote IP and port, protocol, state, and associated process/PID. Supports filtering by protocol and state.",
        "required_args": ["agent_id", "protocol", "state"],
        "optional_args": ["limit"],
        "example_args": {
    		"agent_id": "000",
    		"protocol": "tcp", 
    		"state": "LISTENING",
    		"limit": 15
	}
    },
    "get_wazuh_rules_summary": {
        "description": "Retrieves a summary of Wazuh security rules. Returns formatted rule information including ID, level, description, and groups. Supports filtering by level, group, and filename.",
        "required_args": [],
        "optional_args": ["filename", "group", "level", "limit"],
        "example_args": {}
    }
}

