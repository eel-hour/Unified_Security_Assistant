# tool_definitions.py

TOOL_DEFINITIONS = {
    "get_thehive_cases": {
        "description": "Retrieves a list of cases from TheHive. Returns formatted case information including ID, title, severity, and status.",
        "required_args": [],
        "optional_args": ["limit"],
        "example_args": {}
    },
    "promote_alert_to_case": {
        "description": "Promotes a TheHive alert to a case. Returns the newly created case information.",
        "required_args": ["alert_id"],
        "optional_args": [],
        "example_args": {}
    },
    "get_thehive_alerts": {
        "description": "Retrieves a list of alerts from TheHive. Returns formatted alert information including ID, title, severity, and status.",
        "required_args": [],
        "optional_args": ["limit"],
        "example_args": {}
    },
    "get_thehive_case_by_id": {
        "description": "Retrieves a specific case from TheHive by its ID. Returns detailed case information.",
        "required_args": ["case_id"],
        "optional_args": [],
        "example_args": {}
    },
    "create_thehive_case": {
        "description": "Creates a new case in TheHive. Returns the newly created case information.",
        "required_args": ["description", "title"],
        "optional_args": ["assignee", "case_template", "pap", "severity", "start_date", "status", "tags", "tlp"],
        "example_args": {}
    },
    "get_thehive_alert_by_id": {
        "description": "Retrieves a specific alert from TheHive by its ID. Returns detailed alert information.",
        "required_args": ["alert_id"],
        "optional_args": [],
        "example_args": {}
    }
}

