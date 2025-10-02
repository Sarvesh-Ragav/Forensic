#!/usr/bin/env python3
"""
UFDR CSV Data Ingestion Script

This script ingests UFDR datasets from CSV files into SQLAlchemy ORM models.
It handles column mapping, bulk insertion, and error handling for missing values.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

from models import init_db, Message, Call, Contact, Entity
from sqlalchemy.orm import Session


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UFDRCSVIngester:
    """
    UFDR CSV Data Ingester for SQLAlchemy ORM models.
    """
    
    def __init__(self, database_url: str = "sqlite:///forensic_data.db"):
        """
        Initialize the CSV ingester.
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self.engine, self.Session = init_db(database_url)
        self.session = None
        
        # Column mapping definitions
        self.column_mappings = {
            'messages': {
                'MessageID': 'id',
                'SenderNumber': 'sender',
                'ReceiverNumber': 'receiver',
                'App': 'app',
                'Timestamp': 'timestamp',
                'MessageText': 'text'
            },
            'calls': {
                'CallID': 'id',
                'CallerNumber': 'caller',
                'CalleeNumber': 'callee',
                'Timestamp': 'timestamp',
                'DurationSeconds': 'duration',
                'Type': 'type'
            },
            'contacts': {
                'ContactID': 'id',
                'Name': 'name',
                'PhoneNumber': 'number',
                'Email': 'email',
                'App': 'app'
            },
            'entities': {
                'EntityID': 'id',
                'Type': 'type',
                'Value': 'value',
                'Label': 'confidence'
            }
        }
    
    def start_session(self):
        """Start a new database session."""
        self.session = self.Session()
        logger.info("Database session started")
    
    def close_session(self):
        """Close the database session."""
        if self.session:
            self.session.close()
            logger.info("Database session closed")
    
    def clean_dataframe(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Clean and prepare dataframe for insertion.
        
        Args:
            df: Input dataframe
            table_name: Target table name
            
        Returns:
            Cleaned dataframe
        """
        logger.info(f"Cleaning dataframe for {table_name} table")
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Handle specific table requirements
        if table_name == 'messages':
            # Ensure required fields are not null
            df = df.dropna(subset=['sender', 'receiver', 'app', 'timestamp'])
            
        elif table_name == 'calls':
            # Ensure required fields are not null
            df = df.dropna(subset=['caller', 'callee', 'timestamp'])
            # Convert duration to int, handle missing values
            df['duration'] = pd.to_numeric(df['duration'], errors='coerce')
            
        elif table_name == 'contacts':
            # At least one of name, number, or email should be present
            df = df.dropna(subset=['name', 'number', 'email'], how='all')
            
        elif table_name == 'entities':
            # Ensure required fields are not null
            df = df.dropna(subset=['type', 'value'])
            # Handle confidence field
            if 'confidence' in df.columns:
                df['confidence'] = pd.to_numeric(df['confidence'], errors='coerce')
                df['confidence'] = df['confidence'].fillna(1.0)
            else:
                df['confidence'] = 1.0
        
        logger.info(f"Cleaned dataframe: {len(df)} rows remaining")
        return df
    
    def map_columns(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Map CSV columns to ORM field names.
        
        Args:
            df: Input dataframe
            table_name: Target table name
            
        Returns:
            Dataframe with mapped column names
        """
        mapping = self.column_mappings.get(table_name, {})
        
        # Rename columns according to mapping
        df_mapped = df.rename(columns=mapping)
        
        # Log unmapped columns
        unmapped_cols = [col for col in df.columns if col not in mapping]
        if unmapped_cols:
            logger.warning(f"Unmapped columns in {table_name}: {unmapped_cols}")
        
        logger.info(f"Mapped columns for {table_name}: {list(mapping.keys())} -> {list(mapping.values())}")
        return df_mapped
    
    def process_timestamp(self, df: pd.DataFrame, timestamp_col: str = 'timestamp') -> pd.DataFrame:
        """
        Process timestamp column to ensure proper datetime format.
        
        Args:
            df: Input dataframe
            timestamp_col: Name of timestamp column
            
        Returns:
            Dataframe with processed timestamps
        """
        if timestamp_col in df.columns:
            try:
                # Try to parse timestamps
                df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
                # Remove rows with invalid timestamps
                invalid_timestamps = df[timestamp_col].isna().sum()
                if invalid_timestamps > 0:
                    logger.warning(f"Removing {invalid_timestamps} rows with invalid timestamps")
                    df = df.dropna(subset=[timestamp_col])
            except Exception as e:
                logger.error(f"Error processing timestamps: {e}")
        
        return df
    
    def ingest_csv(self, csv_path: str, table_name: str, model_class, use_auto_id: bool = True) -> int:
        """
        Ingest a single CSV file into the database.
        
        Args:
            csv_path: Path to CSV file
            table_name: Target table name
            model_class: SQLAlchemy model class
            use_auto_id: Whether to use auto-increment IDs (ignore CSV ID column)
            
        Returns:
            Number of records inserted
        """
        logger.info(f"Starting ingestion of {csv_path} into {table_name} table")
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded CSV: {len(df)} rows, {len(df.columns)} columns")
            
            # Map columns
            df = self.map_columns(df, table_name)
            
            # Remove ID column if using auto-increment
            if use_auto_id and 'id' in df.columns:
                df = df.drop('id', axis=1)
                logger.info("Removed ID column - using auto-increment")
            
            # Process timestamps
            df = self.process_timestamp(df)
            
            # Clean dataframe
            df = self.clean_dataframe(df, table_name)
            
            if len(df) == 0:
                logger.warning(f"No valid data to insert for {table_name}")
                return 0
            
            # Convert to list of dictionaries for bulk insert
            records = df.to_dict('records')
            
            # Use bulk_insert_mappings for speed
            self.session.bulk_insert_mappings(model_class, records)
            
            logger.info(f"Successfully prepared {len(records)} records for {table_name}")
            return len(records)
            
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_path}")
            return 0
        except Exception as e:
            logger.error(f"Error ingesting {csv_path}: {e}")
            return 0
    
    def clear_existing_data(self):
        """Clear existing data from all tables."""
        logger.info("Clearing existing data from all tables")
        
        try:
            # Clear in reverse order to respect foreign key constraints
            self.session.query(Entity).delete()
            self.session.query(Message).delete()
            self.session.query(Call).delete()
            self.session.query(Contact).delete()
            self.session.commit()
            logger.info("Existing data cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing existing data: {e}")
            self.session.rollback()
            raise
    
    def ingest_all_csvs(self, csv_directory: str = ".", clear_existing: bool = True, use_auto_id: bool = True) -> Dict[str, int]:
        """
        Ingest all UFDR CSV files from a directory.
        
        Args:
            csv_directory: Directory containing CSV files
            clear_existing: Whether to clear existing data before ingestion
            use_auto_id: Whether to use auto-increment IDs (ignore CSV ID column)
            
        Returns:
            Dictionary with record counts for each table
        """
        logger.info(f"Starting bulk CSV ingestion from {csv_directory}")
        
        # Define file mappings
        file_mappings = {
            'Chats.csv': ('messages', Message),
            'Calls.csv': ('calls', Call),
            'Contacts.csv': ('contacts', Contact),
            'Entities.csv': ('entities', Entity)
        }
        
        record_counts = {}
        
        # Start database session
        self.start_session()
        
        try:
            # Clear existing data if requested
            if clear_existing:
                self.clear_existing_data()
            
            for filename, (table_name, model_class) in file_mappings.items():
                csv_path = Path(csv_directory) / filename
                
                if csv_path.exists():
                    count = self.ingest_csv(str(csv_path), table_name, model_class, use_auto_id)
                    record_counts[table_name] = count
                else:
                    logger.warning(f"CSV file not found: {csv_path}")
                    record_counts[table_name] = 0
            
            # Commit all changes
            self.session.commit()
            logger.info("All changes committed to database")
            
        except Exception as e:
            logger.error(f"Error during bulk ingestion: {e}")
            self.session.rollback()
            logger.info("Rolled back all changes")
            raise
        finally:
            self.close_session()
        
        return record_counts
    
    def print_summary(self, record_counts: Dict[str, int]):
        """
        Print summary of ingestion results.
        
        Args:
            record_counts: Dictionary with record counts for each table
        """
        print("\n" + "="*60)
        print("UFDR CSV INGESTION SUMMARY")
        print("="*60)
        
        total_records = 0
        for table_name, count in record_counts.items():
            print(f"{table_name.upper():<15}: {count:>8,} records")
            total_records += count
        
        print("-"*60)
        print(f"{'TOTAL':<15}: {total_records:>8,} records")
        print("="*60)
        
        # Print success/failure status
        successful_tables = [name for name, count in record_counts.items() if count > 0]
        failed_tables = [name for name, count in record_counts.items() if count == 0]
        
        if successful_tables:
            print(f"✅ Successfully ingested: {', '.join(successful_tables)}")
        
        if failed_tables:
            print(f"❌ Failed to ingest: {', '.join(failed_tables)}")


def create_sample_csvs():
    """
    Create sample CSV files for testing the ingestion script.
    """
    logger.info("Creating sample CSV files for testing")
    
    # Sample Chats data
    chats_data = {
        'MessageID': [1, 2, 3, 4, 5],
        'SenderNumber': ['+1234567890', '+971501234567', '+1234567890', '+1987654321', '+1555123456'],
        'ReceiverNumber': ['+1987654321', '+1234567890', '+971509876543', '+1234567890', '+1234567890'],
        'App': ['WhatsApp', 'Telegram', 'Signal', 'WhatsApp', 'WhatsApp'],
        'Timestamp': [
            '2024-01-15 10:30:00',
            '2024-01-15 14:15:00',
            '2024-01-15 22:30:00',
            '2024-01-16 09:45:00',
            '2024-01-16 16:20:00'
        ],
        'MessageText': [
            'Hey, are we still meeting for lunch tomorrow?',
            'Payment received. Send 0.5 BTC to: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2',
            'Transaction confirmed. New address: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
            'Thanks for the coffee! Let\'s do it again soon.',
            'Can you send me the project files when you get a chance?'
        ]
    }
    
    # Sample Calls data
    calls_data = {
        'CallID': [1, 2, 3],
        'CallerNumber': ['+1234567890', '+971501234567', '+1234567890'],
        'CalleeNumber': ['+1987654321', '+1234567890', '+1555123456'],
        'Timestamp': [
            '2024-01-15 11:00:00',
            '2024-01-15 15:00:00',
            '2024-01-16 17:00:00'
        ],
        'DurationSeconds': [180, 750, 420],
        'Type': ['outgoing', 'incoming', 'outgoing']
    }
    
    # Sample Contacts data
    contacts_data = {
        'ContactID': [1, 2, 3],
        'Name': ['Sarah Johnson', 'Ahmed Al-Rashid', 'Mike Chen'],
        'PhoneNumber': ['+1987654321', '+971501234567', '+1555123456'],
        'Email': ['sarah.johnson@email.com', 'ahmed.rashid@protonmail.com', 'mike.chen@company.com'],
        'App': ['WhatsApp', 'Telegram', 'WhatsApp']
    }
    
    # Sample Entities data
    entities_data = {
        'EntityID': [1, 2, 3, 4],
        'Type': ['bitcoin', 'foreign_number', 'bitcoin', 'email'],
        'Value': [
            '1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2',
            '+971501234567',
            'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
            'ahmed.rashid@protonmail.com'
        ],
        'Label': [0.98, 1.0, 0.95, 1.0]
    }
    
    # Create CSV files
    datasets = {
        'Chats.csv': chats_data,
        'Calls.csv': calls_data,
        'Contacts.csv': contacts_data,
        'Entities.csv': entities_data
    }
    
    for filename, data in datasets.items():
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        logger.info(f"Created sample CSV: {filename} ({len(df)} rows)")


def main():
    """
    Main function to run the CSV ingestion process.
    """
    print("🔬 UFDR CSV Data Ingestion Tool")
    print("="*50)
    
    # Create sample CSV files if they don't exist
    csv_files = ['Chats.csv', 'Calls.csv', 'Contacts.csv', 'Entities.csv']
    missing_files = [f for f in csv_files if not Path(f).exists()]
    
    if missing_files:
        print(f"📁 Creating sample CSV files: {', '.join(missing_files)}")
        create_sample_csvs()
        print("✅ Sample CSV files created")
    
    # Initialize ingester
    ingester = UFDRCSVIngester()
    
    try:
        # Ingest all CSV files
        record_counts = ingester.ingest_all_csvs()
        
        # Print summary
        ingester.print_summary(record_counts)
        
        print("\n🎯 CSV ingestion completed successfully!")
        
    except Exception as e:
        logger.error(f"CSV ingestion failed: {e}")
        print(f"\n❌ CSV ingestion failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
