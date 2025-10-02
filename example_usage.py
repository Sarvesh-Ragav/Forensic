#!/usr/bin/env python3
"""
Example usage of the Forensic UFDR SQLAlchemy models.

This script demonstrates how to use the database models for forensic data analysis.
"""

from datetime import datetime
from models import init_db, Message, Call, Contact, Entity
from database_utils import ForensicDB


def main():
    """Demonstrate the forensic database models."""
    
    # Initialize database
    print("Initializing database...")
    engine, Session = init_db("sqlite:///example_forensic.db")
    session = Session()
    
    # Create ForensicDB instance
    db = ForensicDB(session)
    
    # Add sample forensic data
    print("\nAdding sample forensic data...")
    
    # Add messages
    msg1 = db.add_message(
        sender="+1234567890",
        receiver="+0987654321", 
        app="WhatsApp",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        text="Hey, can you send me your Bitcoin address for the payment?"
    )
    
    msg2 = db.add_message(
        sender="+0987654321",
        receiver="+1234567890",
        app="WhatsApp", 
        timestamp=datetime(2024, 1, 15, 10, 32, 0),
        text="Sure! My Bitcoin address is 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa. Also, my email is john@example.com"
    )
    
    # Add calls
    call1 = db.add_call(
        caller="+1234567890",
        callee="+0987654321",
        timestamp=datetime(2024, 1, 15, 11, 0, 0),
        duration=300,  # 5 minutes
        call_type="outgoing"
    )
    
    # Add contacts
    contact1 = db.add_contact(
        name="John Doe",
        number="+0987654321",
        email="john@example.com",
        app="WhatsApp"
    )
    
    # Add entities (extracted from messages)
    entity1 = db.add_entity(
        entity_type="bitcoin",
        value="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        confidence=0.95,
        linked_message_id=msg2.id
    )
    
    entity2 = db.add_entity(
        entity_type="email",
        value="john@example.com",
        confidence=1.0,
        linked_message_id=msg2.id
    )
    
    entity3 = db.add_entity(
        entity_type="foreign_number",
        value="+0987654321",
        confidence=1.0,
        linked_message_id=msg1.id
    )
    
    print("Sample data added successfully!")
    
    # Demonstrate queries
    print("\n=== Forensic Analysis Queries ===")
    
    # Get all Bitcoin addresses
    bitcoin_addresses = db.get_bitcoin_addresses()
    print(f"\nBitcoin addresses found: {len(bitcoin_addresses)}")
    for addr in bitcoin_addresses:
        print(f"  - {addr.value} (confidence: {addr.confidence})")
    
    # Get all email addresses
    emails = db.get_emails()
    print(f"\nEmail addresses found: {len(emails)}")
    for email in emails:
        print(f"  - {email.value} (confidence: {email.confidence})")
    
    # Get conversation between two participants
    conversation = db.get_conversation("+1234567890", "+0987654321")
    print(f"\nConversation between +1234567890 and +0987654321:")
    for msg in conversation:
        print(f"  [{msg.timestamp}] {msg.sender} -> {msg.receiver}: {msg.text}")
    
    # Search for messages containing "Bitcoin"
    bitcoin_messages = db.search_messages("Bitcoin")
    print(f"\nMessages containing 'Bitcoin': {len(bitcoin_messages)}")
    for msg in bitcoin_messages:
        print(f"  - {msg.text}")
    
    # Get database statistics
    stats = db.get_statistics()
    print(f"\n=== Database Statistics ===")
    print(f"Total messages: {stats['total_messages']}")
    print(f"Total calls: {stats['total_calls']}")
    print(f"Total contacts: {stats['total_contacts']}")
    print(f"Total entities: {stats['total_entities']}")
    print(f"Messages by app: {stats['messages_by_app']}")
    print(f"Calls by type: {stats['calls_by_type']}")
    print(f"Entities by type: {stats['entities_by_type']}")
    
    # Get timeline for a specific date range
    start_date = datetime(2024, 1, 15, 0, 0, 0)
    end_date = datetime(2024, 1, 15, 23, 59, 59)
    timeline = db.get_timeline(start_date, end_date)
    print(f"\n=== Timeline for {start_date.date()} ===")
    print(f"Messages: {len(timeline['messages'])}")
    print(f"Calls: {len(timeline['calls'])}")
    
    # Close database connection
    db.close()
    print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
