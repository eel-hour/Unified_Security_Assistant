#!/usr/bin/env python3
"""
Database models for the unified security platform
"""
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class LogEntry(Base):
    """Log entry model for CSV data"""
    __tablename__ = 'log_entries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String)
    time = Column(String)
    policy_identity = Column(String)
    internal_ip = Column(String)
    external_ip = Column(String)
    action = Column(String)
    destination = Column(String)
    categories = Column(String)
    source_file = Column(String)

class ProcessedFile(Base):
    """Track processed CSV files to avoid duplicates"""
    __tablename__ = 'processed_files'
    
    filename = Column(String, primary_key=True)
    processed_at = Column(DateTime, default=func.now())
