#!/usr/bin/env python3
"""
CSV file ingestion and monitoring
"""
import os
import pandas as pd
import streamlit as st
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Optional
from database.operations import DatabaseManager

class CSVHandler(FileSystemEventHandler):
    """File system event handler for CSV files"""
    
    def __init__(self, db_manager: DatabaseManager, csv_separator: str = ";"):
        self.db_manager = db_manager
        self.csv_separator = csv_separator
    
    def on_created(self, event):
        """Handle new CSV file creation"""
        if event.src_path.endswith('.csv'):
            self.ingest_csv(event.src_path)

class CSVWatcher:
    """CSV file watcher and processor"""
    
    def __init__(self, watch_directory: str, db_manager: DatabaseManager, csv_separator: str = ";"):
        self.watch_directory = watch_directory
        self.db_manager = db_manager
        self.csv_separator = csv_separator
        self.observer = None
        self.handler = CSVHandler(db_manager, csv_separator)
    
    def start(self):
        """Start watching for CSV files"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.watch_directory, exist_ok=True)
            
            # Process existing files
            self.process_existing_files()
            
            # Start file watcher
            self.observer = Observer()
            self.observer.schedule(self.handler, self.watch_directory, recursive=False)
            self.observer.start()
            
            st.success(f"✅ CSV watcher started for directory: {self.watch_directory}")
            
        except Exception as e:
            st.error(f"Failed to start CSV watcher: {str(e)}")
            raise
    
    def stop(self):
        """Stop the CSV watcher"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
    
    def process_existing_files(self):
        """Process existing CSV files in the watch directory"""
        if not os.path.exists(self.watch_directory):
            return
        
        processed_count = 0
        for filename in os.listdir(self.watch_directory):
            if filename.lower().endswith('.csv'):
                file_path = os.path.join(self.watch_directory, filename)  # FIXED: was os.path.jo
                if self.ingest_csv(file_path):
                    processed_count += 1
        
        if processed_count > 0:
            st.info(f"📁 Processed {processed_count} existing CSV files")
    
    def ingest_csv(self, file_path: str) -> bool:
        """Ingest a single CSV file into the database"""
        filename = os.path.basename(file_path)
        
        try:
            # Check if file already processed
            if self.db_manager.is_file_processed(filename):
                return False
            
            # Read CSV file
            df = pd.read_csv(file_path, sep=self.csv_separator)
            
            # Validate required columns
            required_columns = [
                'Date', 'Time', 'Policy Identity', 'Internal IP Address',
                'External IP Address', 'Action', 'Destination', 'Categories'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.error(f"CSV file {filename} missing required columns: {missing_columns}")
                return False
            
            # Process each row
            for _, row in df.iterrows():
                entry_data = {
                    'date': row['Date'],
                    'time': row['Time'],
                    'policy_identity': row['Policy Identity'],
                    'internal_ip': row['Internal IP Address'],
                    'external_ip': row['External IP Address'],
                    'action': row['Action'],
                    'destination': row['Destination'],
                    'categories': row['Categories'],
                    'source_file': filename
                }
                
                self.db_manager.add_log_entry(entry_data)
            
            # Mark file as processed
            self.db_manager.mark_file_processed(filename)
            
            st.success(f"✅ Ingested CSV file: {filename} ({len(df)} entries)")
            return True
            
        except Exception as e:
            st.error(f"Failed to ingest CSV file {filename}: {str(e)}")
            return False
