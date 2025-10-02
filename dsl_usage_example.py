#!/usr/bin/env python3
"""
Simple usage example for the Forensic DSL query engine.

This script demonstrates how to use the run_dsl_query function
for forensic data analysis.
"""

from models import init_db
from forensic_dsl import run_dsl_query


def main():
    """Demonstrate DSL query usage."""
    print("🔍 Forensic DSL Query Usage Example")
    print("=" * 50)
    
    # Initialize database
    engine, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    # Example 1: Find all WhatsApp messages
    print("\n📱 Example 1: Find all WhatsApp messages")
    whatsapp_query = {
        "dataset": "messages",
        "filters": [
            {"field": "app", "op": "=", "value": "WhatsApp"}
        ]
    }
    
    try:
        results = run_dsl_query(whatsapp_query, session)
        print(f"Found {len(results)} WhatsApp messages")
        for result in results:
            print(f"  - {result['sender']} -> {result['receiver']}: {result['text'][:50]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Find calls longer than 10 minutes
    print("\n📞 Example 2: Find calls longer than 10 minutes")
    long_calls_query = {
        "dataset": "calls",
        "filters": [
            {"field": "duration", "op": ">", "value": 600}
        ],
        "sort": [{"field": "duration", "direction": "desc"}]
    }
    
    try:
        results = run_dsl_query(long_calls_query, session)
        print(f"Found {len(results)} long calls")
        for result in results:
            duration_min = result['duration'] // 60
            print(f"  - {result['caller']} -> {result['callee']}: {duration_min} minutes")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Find Bitcoin addresses with high confidence
    print("\n💰 Example 3: Find Bitcoin addresses with high confidence")
    bitcoin_query = {
        "dataset": "entities",
        "filters": [
            {"field": "type", "op": "=", "value": "bitcoin"},
            {"field": "confidence", "op": ">=", "value": 0.9}
        ],
        "sort": [{"field": "confidence", "direction": "desc"}]
    }
    
    try:
        results = run_dsl_query(bitcoin_query, session)
        print(f"Found {len(results)} high-confidence Bitcoin addresses")
        for result in results:
            print(f"  - {result['value']} (confidence: {result['confidence']})")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 4: Find suspicious communications
    print("\n🚨 Example 4: Find suspicious communications")
    suspicious_query = {
        "dataset": "messages",
        "filters": [
            {"field": "app", "op": "in", "value": ["Telegram", "Signal"]},
            {"field": "text", "op": "contains", "value": "bitcoin"}
        ],
        "sort": [{"field": "timestamp", "direction": "desc"}],
        "limit": 10
    }
    
    try:
        results = run_dsl_query(suspicious_query, session)
        print(f"Found {len(results)} suspicious messages")
        for result in results:
            print(f"  - [{result['timestamp']}] {result['app']}: {result['text'][:60]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 5: Find UAE contacts
    print("\n🇦🇪 Example 5: Find UAE contacts")
    uae_query = {
        "dataset": "contacts",
        "filters": [
            {"field": "number", "op": "country", "value": "UAE"}
        ]
    }
    
    try:
        results = run_dsl_query(uae_query, session)
        print(f"Found {len(results)} UAE contacts")
        for result in results:
            print(f"  - {result['name']}: {result['number']} ({result['email']})")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 6: Complex query with multiple filters
    print("\n🔍 Example 6: Complex forensic analysis")
    complex_query = {
        "dataset": "messages",
        "filters": [
            {"field": "timestamp", "op": ">=", "value": "2024-01-01"},
            {"field": "app", "op": "!=", "value": "WhatsApp"},
            {"field": "text", "op": "contains", "value": "payment"}
        ],
        "sort": [
            {"field": "timestamp", "direction": "desc"},
            {"field": "sender", "direction": "asc"}
        ],
        "limit": 5
    }
    
    try:
        results = run_dsl_query(complex_query, session)
        print(f"Found {len(results)} messages matching complex criteria")
        for result in results:
            print(f"  - [{result['timestamp']}] {result['app']}: {result['sender']} -> {result['receiver']}")
    except Exception as e:
        print(f"Error: {e}")
    
    session.close()
    print(f"\n✅ All examples completed!")


if __name__ == "__main__":
    main()
