#!/usr/bin/env python3
"""
Test script for the run_dsl_query function.

This script demonstrates how to use the DSL query execution with real database data.
"""

import json
from models import init_db
from database_utils import ForensicDB
from forensic_dsl import run_dsl_query, EXAMPLE_QUERIES


def test_run_dsl_queries():
    """Test the run_dsl_query function with various queries."""
    print("🔬 Testing run_dsl_query Function")
    print("=" * 60)
    
    # Initialize database and seed with data
    print("🌱 Setting up database with sample data...")
    engine, Session = init_db("sqlite:///test_forensic.db")
    session = Session()
    db = ForensicDB(session)
    
    # Clear existing data
    from models import Message, Call, Contact, Entity
    session.query(Entity).delete()
    session.query(Message).delete()
    session.query(Call).delete()
    session.query(Contact).delete()
    session.commit()
    
    # Add sample data
    from datetime import datetime, timedelta
    base_time = datetime.now() - timedelta(days=30)
    
    # Add messages
    msg1 = db.add_message(
        sender="+1234567890",
        receiver="+1987654321",
        app="WhatsApp",
        timestamp=base_time + timedelta(days=1, hours=10, minutes=30),
        text="Hey, are we still meeting for lunch tomorrow?"
    )
    
    msg2 = db.add_message(
        sender="+971501234567",  # UAE number
        receiver="+1234567890",
        app="Telegram",
        timestamp=base_time + timedelta(days=2, hours=14, minutes=15),
        text="Payment received. Send 0.5 BTC to: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
    )
    
    msg3 = db.add_message(
        sender="+1234567890",
        receiver="+971509876543",  # UAE number
        app="Signal",
        timestamp=base_time + timedelta(days=5, hours=22, minutes=30),
        text="Transaction confirmed. New address: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
    )
    
    # Add calls
    call1 = db.add_call(
        caller="+971501234567",  # UAE number
        callee="+1234567890",
        timestamp=base_time + timedelta(days=2, hours=15, minutes=0),
        duration=750,  # 12.5 minutes
        call_type="incoming"
    )
    
    # Add contacts
    contact1 = db.add_contact(
        name="Ahmed Al-Rashid",
        number="+971501234567",
        email="ahmed.rashid@protonmail.com",
        app="Telegram"
    )
    
    # Add entities
    entity1 = db.add_entity(
        entity_type="bitcoin",
        value="1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
        confidence=0.98,
        linked_message_id=msg2.id
    )
    
    entity2 = db.add_entity(
        entity_type="bitcoin",
        value="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        confidence=0.95,
        linked_message_id=msg3.id
    )
    
    print("✅ Sample data added successfully!")
    
    # Test queries
    test_queries = [
        {
            "name": "WhatsApp Messages",
            "dsl": {
                "dataset": "messages",
                "filters": [
                    {"field": "app", "op": "=", "value": "WhatsApp"}
                ]
            }
        },
        {
            "name": "UAE Numbers in Messages",
            "dsl": {
                "dataset": "messages",
                "filters": [
                    {"field": "sender", "op": "country", "value": "UAE"}
                ]
            }
        },
        {
            "name": "Long Calls",
            "dsl": {
                "dataset": "calls",
                "filters": [
                    {"field": "duration", "op": ">", "value": 600}
                ]
            }
        },
        {
            "name": "ProtonMail Contacts",
            "dsl": {
                "dataset": "contacts",
                "filters": [
                    {"field": "email", "op": "contains", "value": "protonmail"}
                ]
            }
        },
        {
            "name": "Bitcoin Entities",
            "dsl": {
                "dataset": "entities",
                "filters": [
                    {"field": "type", "op": "=", "value": "bitcoin"}
                ],
                "sort": [{"field": "confidence", "direction": "desc"}]
            }
        },
        {
            "name": "Messages with Bitcoin",
            "dsl": {
                "dataset": "messages",
                "filters": [
                    {"field": "text", "op": "contains", "value": "bitcoin"}
                ]
            }
        },
        {
            "name": "Recent Messages with Limit",
            "dsl": {
                "dataset": "messages",
                "filters": [
                    {"field": "timestamp", "op": ">=", "value": "2024-01-01"}
                ],
                "sort": [{"field": "timestamp", "direction": "desc"}],
                "limit": 5
            }
        }
    ]
    
    # Execute each test query
    for test in test_queries:
        print(f"\n🔍 Testing: {test['name']}")
        print(f"DSL: {json.dumps(test['dsl'], indent=2)}")
        
        try:
            # Execute the query
            results = run_dsl_query(test['dsl'], session)
            
            print(f"✅ Query executed successfully")
            print(f"📊 Results: {len(results)} rows")
            
            if results:
                print("📋 Sample results:")
                for i, result in enumerate(results[:3]):  # Show first 3 results
                    print(f"  {i+1}. {result}")
                if len(results) > 3:
                    print(f"  ... and {len(results) - 3} more rows")
            else:
                print("📋 No results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test error handling
    print(f"\n⚠️  Testing Error Handling")
    print("=" * 40)
    
    # Test invalid dataset
    invalid_query = {
        "dataset": "invalid_table",
        "filters": [
            {"field": "app", "op": "=", "value": "WhatsApp"}
        ]
    }
    
    print(f"\n❌ Test: Invalid dataset")
    try:
        results = run_dsl_query(invalid_query, session)
        print(f"❌ Should have failed but didn't")
    except Exception as e:
        print(f"✅ Correctly caught error: {e}")
    
    # Test invalid field
    invalid_field_query = {
        "dataset": "messages",
        "filters": [
            {"field": "invalid_field", "op": "=", "value": "test"}
        ]
    }
    
    print(f"\n❌ Test: Invalid field")
    try:
        results = run_dsl_query(invalid_field_query, session)
        print(f"❌ Should have failed but didn't")
    except Exception as e:
        print(f"✅ Correctly caught error: {e}")
    
    # Close database connection
    db.close()
    print(f"\n🔒 Database connection closed.")


def test_example_queries():
    """Test the example queries from the DSL module."""
    print(f"\n📚 Testing Example Queries")
    print("=" * 50)
    
    # Initialize database
    engine, Session = init_db("sqlite:///test_forensic.db")
    session = Session()
    
    for name, query_dict in EXAMPLE_QUERIES.items():
        print(f"\n🔍 Example: {name}")
        print(f"DSL: {json.dumps(query_dict, indent=2)}")
        
        try:
            results = run_dsl_query(query_dict, session)
            print(f"✅ Executed successfully: {len(results)} results")
            
            if results:
                print("📋 First result:")
                print(f"  {results[0]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    session.close()


def main():
    """Run all tests."""
    print("🚀 Forensic DSL Query Execution Test Suite")
    print("=" * 70)
    
    test_run_dsl_queries()
    test_example_queries()
    
    print(f"\n🎯 All tests completed!")


if __name__ == "__main__":
    main()
