#!/usr/bin/env python3
"""
Simple Suspicious Entities Report

Generates a clean report matching the exact format requirements.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from models import init_db, Entity


def generate_simple_report(database_url: str = "sqlite:///forensic_data.db") -> None:
    """
    Generate and print a simple suspicious entities report.
    """
    engine, Session = init_db(database_url)
    session = Session()
    
    try:
        # Query entities grouped by type
        entity_stats = session.query(
            Entity.type,
            func.count(Entity.id).label('count'),
            func.group_concat(Entity.value, '|').label('values')
        ).group_by(Entity.type).all()
        
        print("---")
        print("Suspicious Entities Report")
        
        # Define entity type mappings for display
        type_mappings = {
            'bitcoin': 'BTC Wallets',
            'ethereum': 'ETH Wallets', 
            'foreign_number': 'UAE Numbers',
            'email': 'Emails'
        }
        
        # Process each entity type
        for entity_type, count, values_str in entity_stats:
            display_name = type_mappings.get(entity_type, entity_type.title())
            print(f"{display_name}: {count}")
            
            # Show up to 3 sample values
            if values_str:
                values = values_str.split('|')[:3]  # Take first 3
                for value in values:
                    print(f"   - {value}")
            else:
                print("   - No values found")
        
        print("---")
        
    finally:
        session.close()


if __name__ == "__main__":
    generate_simple_report()
