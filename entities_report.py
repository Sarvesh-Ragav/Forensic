#!/usr/bin/env python3
"""
Suspicious Entities Report Generator

Generates a clean report of suspicious entities from the database.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from models import init_db, Entity


def generate_entities_report(database_url: str = "sqlite:///forensic_data.db") -> None:
    """
    Generate and print a suspicious entities report.
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
        
        # Process each entity type
        for entity_type, count, values_str in entity_stats:
            # Format entity type name
            if entity_type == 'bitcoin':
                display_name = 'BTC Wallets'
            elif entity_type == 'ethereum':
                display_name = 'ETH Wallets'
            elif entity_type == 'foreign_number':
                display_name = 'UAE Numbers'
            elif entity_type == 'email':
                display_name = 'Emails'
            else:
                display_name = entity_type.title()
            
            print(f"{display_name}: {count}")
            
            # Show up to 3 sample values
            if values_str:
                values = values_str.split('|')[:3]
                for value in values:
                    print(f"   - {value}")
            else:
                print("   - No values found")
        
        print("---")
        
    finally:
        session.close()


if __name__ == "__main__":
    generate_entities_report()
