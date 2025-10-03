#!/usr/bin/env python3
"""
Suspicious Entities Report Generator

Generates a comprehensive report of suspicious entities found in the database,
grouped by type with counts and sample values.
"""

from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import init_db, Entity


def generate_suspicious_entities_report(database_url: str = "sqlite:///forensic_data.db") -> str:
    """
    Generate a suspicious entities report from the Entities table.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        str: Formatted report string
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
        
        # Process results
        report_lines = ["---", "Suspicious Entities Report"]
        
        # Define entity type mappings for display
        type_mappings = {
            'bitcoin': 'BTC Wallets',
            'ethereum': 'ETH Wallets', 
            'foreign_number': 'UAE Numbers',
            'email': 'Emails'
        }
        
        # Sort by count (descending) for most suspicious first
        entity_stats_sorted = sorted(entity_stats, key=lambda x: x.count, reverse=True)
        
        for entity_type, count, values_str in entity_stats_sorted:
            display_name = type_mappings.get(entity_type, entity_type.title())
            report_lines.append(f"{display_name}: {count}")
            
            # Show up to 3 sample values
            if values_str:
                values = values_str.split('|')[:3]  # Take first 3
                for value in values:
                    report_lines.append(f"   - {value}")
            else:
                report_lines.append("   - No values found")
        
        report_lines.append("---")
        
        return "\n".join(report_lines)
        
    finally:
        session.close()


def print_suspicious_entities_report(database_url: str = "sqlite:///forensic_data.db") -> None:
    """
    Print the suspicious entities report to console.
    
    Args:
        database_url: Database connection URL
    """
    report = generate_suspicious_entities_report(database_url)
    print(report)


def get_entity_summary_stats(database_url: str = "sqlite:///forensic_data.db") -> Dict[str, int]:
    """
    Get summary statistics of entities by type.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        Dict[str, int]: Entity type counts
    """
    engine, Session = init_db(database_url)
    session = Session()
    
    try:
        entity_counts = session.query(
            Entity.type,
            func.count(Entity.id).label('count')
        ).group_by(Entity.type).all()
        
        return {entity_type: count for entity_type, count in entity_counts}
        
    finally:
        session.close()


def get_top_suspicious_entities(database_url: str = "sqlite:///forensic_data.db", 
                               limit: int = 10) -> List[Tuple[str, str, float]]:
    """
    Get top suspicious entities by confidence and frequency.
    
    Args:
        database_url: Database connection URL
        limit: Maximum number of entities to return
        
    Returns:
        List[Tuple[str, str, float]]: List of (type, value, confidence) tuples
    """
    engine, Session = init_db(database_url)
    session = Session()
    
    try:
        # Get entities ordered by confidence and value frequency
        entities = session.query(Entity).order_by(
            Entity.confidence.desc(),
            Entity.value
        ).limit(limit).all()
        
        return [(entity.type, entity.value, entity.confidence) for entity in entities]
        
    finally:
        session.close()


def analyze_entity_patterns(database_url: str = "sqlite:///forensic_data.db") -> Dict[str, any]:
    """
    Analyze patterns in the entities data.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        Dict: Analysis results
    """
    engine, Session = init_db(database_url)
    session = Session()
    
    try:
        # Total entities
        total_entities = session.query(Entity).count()
        
        # Entities by type
        type_counts = get_entity_summary_stats(database_url)
        
        # High confidence entities
        high_conf_entities = session.query(Entity).filter(
            Entity.confidence >= 0.9
        ).count()
        
        # Linked entities (connected to messages/calls)
        linked_entities = session.query(Entity).filter(
            (Entity.linked_message_id.isnot(None)) | 
            (Entity.linked_call_id.isnot(None))
        ).count()
        
        # Most common entity types
        most_common_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_entities': total_entities,
            'type_counts': type_counts,
            'high_confidence_count': high_conf_entities,
            'linked_entities_count': linked_entities,
            'most_common_types': most_common_types[:3],
            'confidence_rate': high_conf_entities / total_entities if total_entities > 0 else 0
        }
        
    finally:
        session.close()


def main():
    """Main function to run the suspicious entities report."""
    print("🔍 Generating Suspicious Entities Report")
    print("=" * 50)
    
    # Generate and print the main report
    print_suspicious_entities_report()
    
    print("\n📊 Additional Analysis:")
    
    # Get summary stats
    stats = get_entity_summary_stats()
    print(f"Total entities found: {sum(stats.values())}")
    
    # Analyze patterns
    analysis = analyze_entity_patterns()
    print(f"High confidence entities: {analysis['high_confidence_count']}")
    print(f"Linked to messages/calls: {analysis['linked_entities_count']}")
    print(f"Confidence rate: {analysis['confidence_rate']:.1%}")
    
    # Show most common types
    if analysis['most_common_types']:
        print("\nMost suspicious entity types:")
        for entity_type, count in analysis['most_common_types']:
            print(f"  - {entity_type}: {count}")
    
    # Show top suspicious entities
    print("\n🎯 Top Suspicious Entities:")
    top_entities = get_top_suspicious_entities(limit=5)
    for entity_type, value, confidence in top_entities:
        print(f"  - {entity_type}: {value} (confidence: {confidence})")


if __name__ == "__main__":
    main()
