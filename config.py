#!/usr/bin/env python3
"""
Configuration management for the unified security platform
"""
import os
from dotenv import load_dotenv
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    url: str
    echo: bool = False

@dataclass
class GeminiConfig:
    api_key: str
    model: str = "gemini-2.0-flash"

@dataclass
class WazuhConfig:
    api_host: str
    api_port: str
    api_username: str
    api_password: str
    indexer_host: str
    indexer_port: str
    indexer_username: str
    indexer_password: str
    verify_ssl: str
    test_protocol: str = "https"

@dataclass
class TheHiveConfig:
    url: str
    api_token: str
    verify_ssl: str

@dataclass
class MCPConfig:
    wazuh_server_path: str
    thehive_server_path: str
    rust_log: str = "info"

@dataclass
class IngestionConfig:
    watch_directory: str
    csv_separator: str = ";"

@dataclass
class AppConfig:
    database: DatabaseConfig
    gemini: GeminiConfig
    wazuh: WazuhConfig
    thehive: TheHiveConfig
    mcp: MCPConfig
    ingestion: IngestionConfig

def load_config() -> AppConfig:
    """Load configuration from environment variables"""
    load_dotenv()
    
    # Validate required environment variables
    required_vars = {
        'DATABASE_URL': 'Database connection string',
        'GEMINI_API_KEY': 'Gemini API key',
        'WATCH_DIRECTORY': 'CSV files watch directory'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables:\n" + 
                        "\n".join(f"- {var}" for var in missing_vars))
    
    return AppConfig(
        database=DatabaseConfig(
            url=os.getenv("DATABASE_URL"),
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        ),
        gemini=GeminiConfig(
            api_key=os.getenv("GEMINI_API_KEY"),
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        ),
        wazuh=WazuhConfig(
            api_host=os.getenv("WAZUH_API_HOST", ""),
            api_port=os.getenv("WAZUH_API_PORT", ""),
            api_username=os.getenv("WAZUH_API_USERNAME", ""),
            api_password=os.getenv("WAZUH_API_PASSWORD", ""),
            indexer_host=os.getenv("WAZUH_INDEXER_HOST", ""),
            indexer_port=os.getenv("WAZUH_INDEXER_PORT", ""),
            indexer_username=os.getenv("WAZUH_INDEXER_USERNAME", ""),
            indexer_password=os.getenv("WAZUH_INDEXER_PASSWORD", ""),
            verify_ssl=os.getenv("WAZUH_VERIFY_SSL", "true"),
            test_protocol=os.getenv("WAZUH_TEST_PROTOCOL", "https")
        ),
        thehive=TheHiveConfig(
            url=os.getenv("THEHIVE_URL", ""),
            api_token=os.getenv("THEHIVE_API_TOKEN", ""),
            verify_ssl=os.getenv("VERIFY_SSL", "true")
        ),
        mcp=MCPConfig(
            wazuh_server_path=os.getenv("WAZUH_MCP_SERVER", "./mcp-servers/mcp-server-wazuh-linux-amd64"),
            thehive_server_path=os.getenv("THEHIVE_MCP_SERVER", "./mcp-servers/mcp-server-thehive-linux-amd64"),
            rust_log=os.getenv("RUST_LOG", "info")
        ),
        ingestion=IngestionConfig(
            watch_directory=os.getenv("WATCH_DIRECTORY"),
            csv_separator=os.getenv("CSV_SEPARATOR", ";")
        )
    )
