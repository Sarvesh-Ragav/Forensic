#!/usr/bin/env python3
"""
Test script to verify CSV ingestion results.
"""

from models import init_db, Message, Call, Contact, Entity
from forensic_dsl import run_dsl_query


def test_csv_ingestion():
    """Test that CSV data was ingested correctly."""
    print("🔍 Testing CSV Ingestion Results")
    print("=" * 50)
    
    # Initialize database
    engine, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    # Test 1: Check message count
    print("\n📱 Testing Messages:")
    messages_query = {
        "dataset": "messages",
        "filters": []
    }
    messages = run_dsl_query(messages_query, session)
    print(f"  Total messages: {len(messages)}")
    
    # Show sample message
    if messages:
        sample_msg = messages[0]
        print(f"  Sample: {sample_msg['sender']} -> {sample_msg['receiver']} via {sample_msg['app']}")
    
    # Test 2: Check calls count
    print("\n📞 Testing Calls:")
    calls_query = {
        "dataset": "calls",
        "filters": []
    }
    calls = run_dsl_query(calls_query, session)
    print(f"  Total calls: {len(calls)}")
    
    # Show sample call
    if calls:
        sample_call = calls[0]
        duration_min = sample_call['duration'] // 60 if sample_call['duration'] else 0
        print(f"  Sample: {sample_call['caller']} -> {sample_call['callee']} ({duration_min} min)")
    
    # Test 3: Check contacts count
    print("\n👥 Testing Contacts:")
    contacts_query = {
        "dataset": "contacts",
        "filters": []
    }
    contacts = run_dsl_query(contacts_query, session)
    print(f"  Total contacts: {len(contacts)}")
    
    # Show sample contact
    if contacts:
        sample_contact = contacts[0]
        print(f"  Sample: {sample_contact['name']} ({sample_contact['number']})")
    
    # Test 4: Check entities count
    print("\n🔍 Testing Entities:")
    entities_query = {
        "dataset": "entities",
        "filters": []
    }
    entities = run_dsl_query(entities_query, session)
    print(f"  Total entities: {len(entities)}")
    
    # Show sample entity
    if entities:
        sample_entity = entities[0]
        print(f"  Sample: {sample_entity['type']} = {sample_entity['value']} (confidence: {sample_entity['confidence']})")
    
    # Test 5: Test specific queries
    print("\n🔎 Testing Specific Queries:")
    
    # Find Bitcoin entities
    bitcoin_query = {
        "dataset": "entities",
        "filters": [
            {"field": "type", "op": "=", "value": "bitcoin"}
        ]
    }
    bitcoin_entities = run_dsl_query(bitcoin_query, session)
    print(f"  Bitcoin entities: {len(bitcoin_entities)}")
    
    # Find UAE contacts
    uae_query = {
        "dataset": "contacts",
        "filters": [
            {"field": "number", "op": "country", "value": "UAE"}
        ]
    }
    uae_contacts = run_dsl_query(uae_query, session)
    print(f"  UAE contacts: {len(uae_contacts)}")
    
    # Find long calls
    long_calls_query = {
        "dataset": "calls",
        "filters": [
            {"field": "duration", "op": ">", "value": 600}
        ]
    }
    long_calls = run_dsl_query(long_calls_query, session)
    print(f"  Long calls (>10 min): {len(long_calls)}")
    
    session.close()
    print("\n✅ CSV ingestion test completed!")


if __name__ == "__main__":
    test_csv_ingestion()
