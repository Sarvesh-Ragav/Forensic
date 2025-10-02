#!/usr/bin/env python3
"""
Verification script to display seeded forensic data.

This script shows all the data that was inserted by the seeding script.
"""

from models import init_db, Message, Call, Contact, Entity
from database_utils import ForensicDB


def verify_seeded_data():
    """Display all seeded data for verification."""
    print("🔍 Verifying Seeded Forensic Data")
    print("=" * 50)
    
    # Initialize database
    engine, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    db = ForensicDB(session)
    
    # Get all data
    messages = session.query(Message).order_by(Message.timestamp).all()
    calls = session.query(Call).order_by(Call.timestamp).all()
    contacts = session.query(Contact).all()
    entities = session.query(Entity).all()
    
    print(f"\n📱 MESSAGES ({len(messages)} total):")
    for i, msg in enumerate(messages, 1):
        suspicious = "🚨" if any(e.type in ["bitcoin", "foreign_number"] for e in msg.entities) else "✅"
        print(f"  {i}. {suspicious} [{msg.timestamp.strftime('%Y-%m-%d %H:%M')}] {msg.app}")
        print(f"     {msg.sender} -> {msg.receiver}")
        print(f"     \"{msg.text}\"")
        if msg.entities:
            print(f"     Entities: {[f'{e.type}:{e.value}' for e in msg.entities]}")
        print()
    
    print(f"\n📞 CALLS ({len(calls)} total):")
    for i, call in enumerate(calls, 1):
        suspicious = "🚨" if call.duration and call.duration > 600 else "✅"
        duration_str = f"{call.duration//60}m {call.duration%60}s" if call.duration else "Unknown"
        print(f"  {i}. {suspicious} [{call.timestamp.strftime('%Y-%m-%d %H:%M')}] {call.type.title()}")
        print(f"     {call.caller} -> {call.callee}")
        print(f"     Duration: {duration_str}")
        if call.entities:
            print(f"     Entities: {[f'{e.type}:{e.value}' for e in call.entities]}")
        print()
    
    print(f"\n👥 CONTACTS ({len(contacts)} total):")
    for i, contact in enumerate(contacts, 1):
        suspicious = "🚨" if "protonmail" in contact.email.lower() else "✅"
        print(f"  {i}. {suspicious} {contact.name}")
        print(f"     Number: {contact.number}")
        print(f"     Email: {contact.email}")
        print(f"     App: {contact.app}")
        print()
    
    print(f"\n🔍 ENTITIES ({len(entities)} total):")
    for i, entity in enumerate(entities, 1):
        print(f"  {i}. {entity.type.upper()}: {entity.value}")
        print(f"     Confidence: {entity.confidence}")
        if entity.linked_message_id:
            print(f"     Linked to Message ID: {entity.linked_message_id}")
        if entity.linked_call_id:
            print(f"     Linked to Call ID: {entity.linked_call_id}")
        print()
    
    # Summary statistics
    stats = db.get_statistics()
    print(f"\n📊 SUMMARY STATISTICS:")
    print(f"  Total Messages: {stats['total_messages']}")
    print(f"  Total Calls: {stats['total_calls']}")
    print(f"  Total Contacts: {stats['total_contacts']}")
    print(f"  Total Entities: {stats['total_entities']}")
    
    # Suspicious activity summary
    print(f"\n🚨 SUSPICIOUS ACTIVITY SUMMARY:")
    btc_count = len(db.get_bitcoin_addresses())
    uae_count = len([e for e in entities if e.type == "foreign_number" and "+971" in e.value])
    protonmail_count = len([c for c in contacts if "protonmail" in c.email.lower()])
    long_calls = len([c for c in calls if c.duration and c.duration > 600])
    
    print(f"  Bitcoin Addresses: {btc_count}")
    print(f"  UAE Numbers: {uae_count}")
    print(f"  ProtonMail Contacts: {protonmail_count}")
    print(f"  Long Calls (>10min): {long_calls}")
    
    db.close()


if __name__ == "__main__":
    verify_seeded_data()
