#!/usr/bin/env python3
"""
Database operations for the unified security platform
"""
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from database.models import Base, LogEntry, ProcessedFile
from datetime import datetime
import streamlit as st

class DatabaseManager:
    """Manages database operations for the security platform"""
    
    def __init__(self, db_config):
        self.db_url = db_config.url
        self.echo = db_config.echo
        self.engine = None
        self.Session = None
        self._setup_database()
    
    def _setup_database(self):
        """Setup database connection and session factory"""
        self.engine = create_engine(self.db_url, echo=self.echo)
        self.Session = sessionmaker(bind=self.engine)
    
    def initialize(self):
        """Initialize database schema and handle migrations"""
        try:
            # Check existing schema
            inspector = inspect(self.engine)
            has_log_table = inspector.has_table("log_entries")
            existing_columns = []
            
            if has_log_table:
                existing_columns = [c["name"] for c in inspector.get_columns("log_entries")]
            
            # Create tables
            Base.metadata.create_all(self.engine)
            
            # Handle schema migrations
            if has_log_table:
                self._migrate_schema(existing_columns)
            
            st.success("✅ Database initialized successfully")
            
        except Exception as e:
            st.error(f"Database initialization failed: {str(e)}")
            raise
    
    def _migrate_schema(self, existing_columns: List[str]):
        """Handle schema migrations for existing tables"""
        expected_columns = [
            'date', 'time', 'policy_identity', 'internal_ip', 
            'external_ip', 'action', 'destination', 'categories', 'source_file'
        ]
        
        missing_columns = [col for col in expected_columns if col not in existing_columns and col != 'id']
        
        if missing_columns:
            with self.engine.connect() as conn:
                for col in missing_columns:
                    try:
                        conn.execute(text(f"ALTER TABLE log_entries ADD COLUMN {col} VARCHAR;"))
                        conn.commit()
                    except Exception as e:
                        st.warning(f"Could not add column {col}: {str(e)}")
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
    
    # Tool implementation methods
    def count_lines(self) -> int:
        """Count total log entries"""
        session = self.get_session()
        try:
            return session.query(LogEntry).count()
        finally:
            session.close()
    
    def get_line_by_id(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """Get log entry by ID"""
        session = self.get_session()
        try:
            entry = session.get(LogEntry, entry_id)
            if not entry:
                return None
            return {c.name: getattr(entry, c.name) for c in LogEntry.__table__.c}
        finally:
            session.close()
    
    def _parse_datetime(self, dt_str: str):
        """Parse combined date/time strings into separate components"""
        formats = [
            "%d/%m/%Y %H:%M",   # 27/07/2025 13:30
            "%d/%m/%Y %H",       # 27/07/2025 13
            "%d/%m/%Y",          # 27/07/2025
            "%d/%m/%y %H:%M",    # 27/07/25 13:30
            "%d/%m/%y %H",       # 27/07/25 13
            "%d/%m/%y"           # 27/07/25
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(dt_str, fmt)
                return dt.strftime("%d/%m/%Y"), dt.strftime("%H:%M")
            except ValueError:
                continue
        return None, None
    
    def _build_query(self, session, args: Dict[str, Any]):
        """Build query with filters"""
        query = session.query(LogEntry)
        
        # Handle combined date/time queries
        if 'datetime' in args:
            date_part, time_part = self._parse_datetime(args['datetime'])
            if date_part:
                query = query.filter(LogEntry.date.ilike(f"%{date_part}%"))
            if time_part:
                time_part = time_part.split(':')[0] + ':%' if ':' in time_part else time_part + ':%'
                query = query.filter(LogEntry.time.ilike(f"%{time_part}%"))
        
        # Handle separate date/time queries
        if 'date' in args:
            query = query.filter(LogEntry.date.ilike(f"%{args['date']}%"))
        if 'time' in args:
            time_val = args['time']
            if ':' not in time_val:
                time_val += ':%'
            query = query.filter(LogEntry.time.ilike(f"%{time_val}%"))
        
        # Handle other filters
        filter_columns = ['policy_identity', 'internal_ip', 'external_ip', 'action', 'destination']
        for col in filter_columns:
            if col in args:
                col_attr = getattr(LogEntry, col)
                query = query.filter(col_attr.ilike(f"%{args[col]}%"))
        
        return query
    
    def count_entries(self, args: Dict[str, Any]) -> int:
        """Count entries with filters"""
        session = self.get_session()
        try:
            query = self._build_query(session, args)
            return query.count()
        finally:
            session.close()
    
    def get_entries(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get entries with filters"""
        session = self.get_session()
        try:
            query = self._build_query(session, args)
            entries = query.all()
            return [{
                'id': e.id,
                'date': e.date,
                'time': e.time,
                'policy_identity': e.policy_identity,
                'internal_ip': e.internal_ip,
                'external_ip': e.external_ip,
                'action': e.action,
                'destination': e.destination,
                'categories': e.categories
            } for e in entries]
        finally:
            session.close()
    
    def add_log_entry(self, entry_data: Dict[str, Any]) -> None:
        """Add a new log entry"""
        session = self.get_session()
        try:
            entry = LogEntry(**entry_data)
            session.add(entry)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def is_file_processed(self, filename: str) -> bool:
        """Check if a file has been processed"""
        session = self.get_session()
        try:
            return session.query(ProcessedFile).filter_by(filename=filename).first() is not None
        finally:
            session.close()
    
    def mark_file_processed(self, filename: str) -> None:
        """Mark a file as processed"""
        session = self.get_session()
        try:
            processed_file = ProcessedFile(filename=filename)
            session.add(processed_file)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
