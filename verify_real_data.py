#!/usr/bin/env python3
"""
Verification script for real UFDR data ingestion.

This script demonstrates the ingested data and shows forensic analysis capabilities.
"""

from models import init_db
from forensic_dsl import run_dsl_query


def verify_real_data():
    """Verify the ingested real UFDR data."""
    print("🔍 Real UFDR Data Verification")
    print("=" * 60)
    
    # Initialize database
    engine, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    # Test 1: Overall statistics
    print("\n📊 Overall Statistics:")
    
    datasets = ["messages", "calls", "contacts", "entities"]
    for dataset in datasets:
        query = {"dataset": dataset, "filters": []}
        results = run_dsl_query(query, session)
        print(f"  {dataset.upper():<12}: {len(results):>4} records")
    
    # Test 2: Suspicious calls analysis
    print("\n🚨 Suspicious Calls Analysis:")
    
    # Long calls (>10 minutes)
    long_calls_query = {
        "dataset": "calls",
        "filters": [
            {"field": "duration", "op": ">", "value": 600}
        ],
        "sort": [{"field": "duration", "direction": "desc"}]
    }
    long_calls = run_dsl_query(long_calls_query, session)
    print(f"  Long calls (>10 min): {len(long_calls)}")
    
    for call in long_calls[:3]:  # Show top 3
        duration_min = call['duration'] // 60
        print(f"    - {call['caller']} -> {call['callee']}: {duration_min} min ({call['type']})")
    
    # Test 3: International calls
    print("\n🌍 International Calls:")
    
    # UAE calls
    uae_calls_query = {
        "dataset": "calls",
        "filters": [
            {"field": "caller", "op": "country", "value": "UAE"}
        ]
    }
    uae_calls = run_dsl_query(uae_calls_query, session)
    print(f"  UAE calls: {len(uae_calls)}")
    
    # UK calls
    uk_calls_query = {
        "dataset": "calls",
        "filters": [
            {"field": "caller", "op": "country", "value": "UK"}
        ]
    }
    uk_calls = run_dsl_query(uk_calls_query, session)
    print(f"  UK calls: {len(uk_calls)}")
    
    # Test 4: Message analysis
    print("\n📱 Message Analysis:")
    
    # WhatsApp messages
    whatsapp_query = {
        "dataset": "messages",
        "filters": [
            {"field": "app", "op": "=", "value": "WhatsApp"}
        ]
    }
    whatsapp_msgs = run_dsl_query(whatsapp_query, session)
    print(f"  WhatsApp messages: {len(whatsapp_msgs)}")
    
    # Telegram messages
    telegram_query = {
        "dataset": "messages",
        "filters": [
            {"field": "app", "op": "=", "value": "Telegram"}
        ]
    }
    telegram_msgs = run_dsl_query(telegram_query, session)
    print(f"  Telegram messages: {len(telegram_msgs)}")
    
    # Test 5: Entity analysis
    print("\n🔍 Entity Analysis:")
    
    # Bitcoin entities
    bitcoin_query = {
        "dataset": "entities",
        "filters": [
            {"field": "type", "op": "=", "value": "bitcoin"}
        ]
    }
    bitcoin_entities = run_dsl_query(bitcoin_query, session)
    print(f"  Bitcoin addresses: {len(bitcoin_entities)}")
    
    # Email entities
    email_query = {
        "dataset": "entities",
        "filters": [
            {"field": "type", "op": "=", "value": "email"}
        ]
    }
    email_entities = run_dsl_query(email_query, session)
    print(f"  Email addresses: {len(email_entities)}")
    
    # Phone number entities
    phone_query = {
        "dataset": "entities",
        "filters": [
            {"field": "type", "op": "=", "value": "phone_number"}
        ]
    }
    phone_entities = run_dsl_query(phone_query, session)
    print(f"  Phone numbers: {len(phone_entities)}")
    
    # Test 6: Contact analysis
    print("\n👥 Contact Analysis:")
    
    # All contacts
    contacts_query = {
        "dataset": "contacts",
        "filters": []
    }
    contacts = run_dsl_query(contacts_query, session)
    print(f"  Total contacts: {len(contacts)}")
    
    # Show sample contacts
    print("  Sample contacts:")
    for contact in contacts[:5]:
        print(f"    - {contact['name']}: {contact['number']} ({contact['app']})")
    
    # Test 7: Timeline analysis
    print("\n⏰ Timeline Analysis:")
    
    # Recent messages
    recent_messages_query = {
        "dataset": "messages",
        "filters": [
            {"field": "timestamp", "op": ">=", "value": "2024-01-01"}
        ],
        "sort": [{"field": "timestamp", "direction": "desc"}],
        "limit": 5
    }
    recent_messages = run_dsl_query(recent_messages_query, session)
    print(f"  Recent messages (since 2024): {len(recent_messages)}")
    
    for msg in recent_messages[:3]:
        print(f"    - [{msg['timestamp'][:10]}] {msg['sender']} -> {msg['receiver']} via {msg['app']}")
    
    session.close()
    print("\n✅ Real UFDR data verification completed!")


def forensic_analysis():
    """Perform forensic analysis on the ingested data."""
    print("\n🔬 Forensic Analysis")
    print("=" * 60)
    
    # Initialize database
    engine, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    # Analysis 1: Suspicious patterns
    print("\n🚨 Suspicious Activity Detection:")
    
    # Long international calls
    suspicious_calls_query = {
        "dataset": "calls",
        "filters": [
            {"field": "duration", "op": ">", "value": 1800},  # > 30 minutes
            {"field": "caller", "op": "country", "value": "UAE"}
        ]
    }
    suspicious_calls = run_dsl_query(suspicious_calls_query, session)
    print(f"  Long UAE calls (>30 min): {len(suspicious_calls)}")
    
    # Analysis 2: Communication patterns
    print("\n📊 Communication Patterns:")
    
    # Most active apps
    apps = ["WhatsApp", "Telegram", "Signal", "SMS"]
    for app in apps:
        app_query = {
            "dataset": "messages",
            "filters": [{"field": "app", "op": "=", "value": app}]
        }
        app_messages = run_dsl_query(app_query, session)
        print(f"  {app:<10}: {len(app_messages):>3} messages")
    
    # Analysis 3: Entity confidence analysis
    print("\n🎯 Entity Confidence Analysis:")
    
    high_confidence_query = {
        "dataset": "entities",
        "filters": [
            {"field": "confidence", "op": ">=", "value": 0.9}
        ]
    }
    high_conf_entities = run_dsl_query(high_confidence_query, session)
    print(f"  High confidence entities (≥0.9): {len(high_conf_entities)}")
    
    low_confidence_query = {
        "dataset": "entities",
        "filters": [
            {"field": "confidence", "op": "<", "value": 0.5}
        ]
    }
    low_conf_entities = run_dsl_query(low_confidence_query, session)
    print(f"  Low confidence entities (<0.5): {len(low_conf_entities)}")
    
    session.close()
    print("\n✅ Forensic analysis completed!")


def main():
    """Run all verification and analysis."""
    verify_real_data()
    forensic_analysis()
    
    print("\n🎯 All verification and analysis completed!")
    print("\n💡 You can now use the DSL query system to perform custom forensic analysis!")


if __name__ == "__main__":
    main()
