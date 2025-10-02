#!/usr/bin/env python3
"""
Database seeding script for Forensic UFDR tool.

This script populates the database with realistic forensic data including
suspicious activities, cryptocurrency addresses, and international communications.
"""

from datetime import datetime, timedelta
from models import init_db, Message, Call, Contact, Entity
from database_utils import ForensicDB


def seed_database(database_url="sqlite:///forensic_data.db"):
    """
    Seed the database with realistic forensic data.
    
    Args:
        database_url (str): Database connection URL
    """
    print("🌱 Seeding database with forensic data...")
    
    # Initialize database
    engine, Session = init_db(database_url)
    session = Session()
    db = ForensicDB(session)
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    print("🧹 Clearing existing data...")
    session.query(Entity).delete()
    session.query(Message).delete()
    session.query(Call).delete()
    session.query(Contact).delete()
    session.commit()
    
    # Sample data with realistic timestamps (last 30 days)
    base_time = datetime.now() - timedelta(days=30)
    
    print("📱 Adding sample messages...")
    
    # 1. Normal message
    msg1 = db.add_message(
        sender="+1234567890",
        receiver="+1987654321",
        app="WhatsApp",
        timestamp=base_time + timedelta(days=1, hours=10, minutes=30),
        text="Hey, are we still meeting for lunch tomorrow?"
    )
    
    # 2. Suspicious message with Bitcoin address
    msg2 = db.add_message(
        sender="+971501234567",  # UAE number
        receiver="+1234567890",
        app="Telegram",
        timestamp=base_time + timedelta(days=2, hours=14, minutes=15),
        text="Payment received. Send 0.5 BTC to: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
    )
    
    # 3. Normal message
    msg3 = db.add_message(
        sender="+1987654321",
        receiver="+1234567890",
        app="WhatsApp",
        timestamp=base_time + timedelta(days=3, hours=9, minutes=45),
        text="Thanks for the coffee! Let's do it again soon."
    )
    
    # 4. Suspicious message with UAE number and Bitcoin
    msg4 = db.add_message(
        sender="+1234567890",
        receiver="+971509876543",  # UAE number
        app="Signal",
        timestamp=base_time + timedelta(days=5, hours=22, minutes=30),
        text="Transaction confirmed. New address: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
    )
    
    # 5. Normal message
    msg5 = db.add_message(
        sender="+1555123456",
        receiver="+1234567890",
        app="WhatsApp",
        timestamp=base_time + timedelta(days=7, hours=16, minutes=20),
        text="Can you send me the project files when you get a chance?"
    )
    
    print("📞 Adding sample calls...")
    
    # 1. Normal call
    call1 = db.add_call(
        caller="+1234567890",
        callee="+1987654321",
        timestamp=base_time + timedelta(days=1, hours=11, minutes=0),
        duration=180,  # 3 minutes
        call_type="outgoing"
    )
    
    # 2. Suspicious long call with UAE number
    call2 = db.add_call(
        caller="+971501234567",  # UAE number
        callee="+1234567890",
        timestamp=base_time + timedelta(days=2, hours=15, minutes=0),
        duration=750,  # 12.5 minutes (over 10 minutes)
        call_type="incoming"
    )
    
    # 3. Normal call
    call3 = db.add_call(
        caller="+1234567890",
        callee="+1555123456",
        timestamp=base_time + timedelta(days=7, hours=17, minutes=0),
        duration=420,  # 7 minutes
        call_type="outgoing"
    )
    
    print("👥 Adding sample contacts...")
    
    # 1. Normal contact
    contact1 = db.add_contact(
        name="Sarah Johnson",
        number="+1987654321",
        email="sarah.johnson@email.com",
        app="WhatsApp"
    )
    
    # 2. Suspicious contact with ProtonMail
    contact2 = db.add_contact(
        name="Ahmed Al-Rashid",
        number="+971501234567",
        email="ahmed.rashid@protonmail.com",  # Suspicious ProtonMail
        app="Telegram"
    )
    
    # 3. Normal contact
    contact3 = db.add_contact(
        name="Mike Chen",
        number="+1555123456",
        email="mike.chen@company.com",
        app="WhatsApp"
    )
    
    print("🔍 Adding extracted entities...")
    
    # 1. Bitcoin address from message 2
    entity1 = db.add_entity(
        entity_type="bitcoin",
        value="1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
        confidence=0.98,
        linked_message_id=msg2.id
    )
    
    # 2. UAE number from message 2
    entity2 = db.add_entity(
        entity_type="foreign_number",
        value="+971501234567",
        confidence=1.0,
        linked_message_id=msg2.id
    )
    
    # 3. Bitcoin address from message 4
    entity3 = db.add_entity(
        entity_type="bitcoin",
        value="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        confidence=0.95,
        linked_message_id=msg4.id
    )
    
    # 4. UAE number from call 2
    entity4 = db.add_entity(
        entity_type="foreign_number",
        value="+971501234567",
        confidence=1.0,
        linked_call_id=call2.id
    )
    
    print("✅ Database seeding completed!")
    
    # Display summary
    print("\n📊 Seeding Summary:")
    print(f"  Messages: 5 (2 suspicious with BTC/UAE)")
    print(f"  Calls: 3 (1 with UAE number, 12.5 min duration)")
    print(f"  Contacts: 3 (1 with ProtonMail)")
    print(f"  Entities: 4 (2 Bitcoin addresses, 2 UAE numbers)")
    
    # Show suspicious activities
    print("\n🚨 Suspicious Activities Detected:")
    
    # Bitcoin addresses
    btc_addresses = db.get_bitcoin_addresses()
    print(f"  Bitcoin addresses: {len(btc_addresses)}")
    for addr in btc_addresses:
        print(f"    - {addr.value}")
    
    # UAE numbers
    uae_numbers = db.get_entities_by_type("foreign_number")
    print(f"  UAE numbers: {len(uae_numbers)}")
    for num in uae_numbers:
        print(f"    - {num.value}")
    
    # ProtonMail contacts
    protonmail_contacts = session.query(Contact).filter(
        Contact.email.contains("protonmail")
    ).all()
    print(f"  ProtonMail contacts: {len(protonmail_contacts)}")
    for contact in protonmail_contacts:
        print(f"    - {contact.name}: {contact.email}")
    
    # Long calls
    long_calls = session.query(Call).filter(Call.duration > 600).all()  # > 10 minutes
    print(f"  Long calls (>10 min): {len(long_calls)}")
    for call in long_calls:
        print(f"    - {call.caller} -> {call.callee}: {call.duration//60} min")
    
    # Close database connection
    db.close()
    print("\n🔒 Database connection closed.")


def main():
    """Main function to run the seeding script."""
    print("🔬 Forensic UFDR Database Seeder")
    print("=" * 40)
    
    # Seed the database
    seed_database()
    
    print("\n🎯 Seeding complete! You can now run forensic analysis queries.")
    print("Try running: python example_usage.py")


if __name__ == "__main__":
    main()
