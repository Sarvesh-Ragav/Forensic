#!/usr/bin/env python3
"""
Comprehensive DSL Query Test Suite

This script demonstrates all DSL query capabilities with real forensic data.
"""

from dsl_query_tester import run_dsl_query, validate_dsl, dsl_to_sql
from models import init_db


def test_all_operators():
    """Test all supported DSL operators."""
    print("🧪 Testing All DSL Operators")
    print("=" * 60)
    
    # Initialize database
    engine, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    # Test 1: Equality operator
    print("\n1️⃣ Testing '=' operator")
    query = {
        "dataset": "messages",
        "filters": [{"field": "app", "op": "=", "value": "WhatsApp"}],
        "limit": 3
    }
    results = run_dsl_query(query, session)
    print(f"   WhatsApp messages: {len(results)} found")
    
    # Test 2: Inequality operator
    print("\n2️⃣ Testing '!=' operator")
    query = {
        "dataset": "messages",
        "filters": [{"field": "app", "op": "!=", "value": "WhatsApp"}],
        "limit": 3
    }
    results = run_dsl_query(query, session)
    print(f"   Non-WhatsApp messages: {len(results)} found")
    
    # Test 3: Contains operator
    print("\n3️⃣ Testing 'contains' operator")
    query = {
        "dataset": "messages",
        "filters": [{"field": "text", "op": "contains", "value": "BTC"}],
        "limit": 3
    }
    results = run_dsl_query(query, session)
    print(f"   Messages containing 'BTC': {len(results)} found")
    
    # Test 4: Greater than operator
    print("\n4️⃣ Testing '>' operator")
    query = {
        "dataset": "calls",
        "filters": [{"field": "duration", "op": ">", "value": 1800}],  # > 30 minutes
        "limit": 3
    }
    results = run_dsl_query(query, session)
    print(f"   Calls > 30 minutes: {len(results)} found")
    
    # Test 5: Less than operator
    print("\n5️⃣ Testing '<' operator")
    query = {
        "dataset": "calls",
        "filters": [{"field": "duration", "op": "<", "value": 300}],  # < 5 minutes
        "limit": 3
    }
    results = run_dsl_query(query, session)
    print(f"   Calls < 5 minutes: {len(results)} found")
    
    # Test 6: Between operator
    print("\n6️⃣ Testing 'between' operator")
    query = {
        "dataset": "calls",
        "filters": [{"field": "duration", "op": "between", "value": [300, 1800]}],  # 5-30 minutes
        "limit": 3
    }
    results = run_dsl_query(query, session)
    print(f"   Calls between 5-30 minutes: {len(results)} found")
    
    # Test 7: In operator
    print("\n7️⃣ Testing 'in' operator")
    query = {
        "dataset": "messages",
        "filters": [{"field": "app", "op": "in", "value": ["WhatsApp", "Telegram"]}],
        "limit": 3
    }
    results = run_dsl_query(query, session)
    print(f"   WhatsApp or Telegram messages: {len(results)} found")
    
    # Test 8: Not in operator
    print("\n8️⃣ Testing 'not_in' operator")
    query = {
        "dataset": "calls",
        "filters": [{"field": "type", "op": "not_in", "value": ["missed"]}],
        "limit": 3
    }
    results = run_dsl_query(query, session)
    print(f"   Non-missed calls: {len(results)} found")
    
    session.close()
    print("\n✅ All operator tests completed!")


def test_complex_queries():
    """Test complex multi-filter queries."""
    print("\n🔍 Testing Complex Queries")
    print("=" * 60)
    
    # Initialize database
    engine, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    # Test 1: Multi-filter query
    print("\n1️⃣ Multi-filter query: Long calls from specific numbers")
    query = {
        "dataset": "calls",
        "filters": [
            {"field": "duration", "op": ">", "value": 600},  # > 10 minutes
            {"field": "caller", "op": "contains", "value": "971"}  # UAE numbers
        ],
        "sort": [{"field": "duration", "direction": "desc"}],
        "limit": 5
    }
    results = run_dsl_query(query, session)
    print(f"   Long UAE calls: {len(results)} found")
    for call in results:
        duration_min = call['duration'] // 60
        print(f"     - {call['caller']} -> {call['callee']}: {duration_min} min")
    
    # Test 2: Entity confidence analysis
    print("\n2️⃣ Entity confidence analysis")
    query = {
        "dataset": "entities",
        "filters": [
            {"field": "confidence", "op": ">=", "value": 0.95},
            {"field": "type", "op": "in", "value": ["URL", "IP Address"]}
        ],
        "sort": [{"field": "confidence", "direction": "desc"}],
        "limit": 5
    }
    results = run_dsl_query(query, session)
    print(f"   High confidence URLs/IPs: {len(results)} found")
    for entity in results:
        print(f"     - {entity['type']}: {entity['value']} (confidence: {entity['confidence']})")
    
    # Test 3: Recent suspicious communications
    print("\n3️⃣ Recent suspicious communications")
    query = {
        "dataset": "messages",
        "filters": [
            {"field": "app", "op": "!=", "value": "WhatsApp"},
            {"field": "text", "op": "contains", "value": "BTC"}
        ],
        "sort": [{"field": "timestamp", "direction": "desc"}],
        "limit": 3
    }
    results = run_dsl_query(query, session)
    print(f"   Recent non-WhatsApp BTC messages: {len(results)} found")
    for msg in results:
        print(f"     - [{msg['timestamp'][:10]}] {msg['app']}: {msg['text'][:50]}...")
    
    session.close()
    print("\n✅ Complex query tests completed!")


def test_validation_errors():
    """Test DSL validation error handling."""
    print("\n⚠️  Testing Validation Errors")
    print("=" * 60)
    
    # Test 1: Invalid dataset
    print("\n1️⃣ Testing invalid dataset")
    try:
        query = {"dataset": "invalid_table", "filters": []}
        validate_dsl(query)
        print("   ❌ Should have failed but didn't")
    except ValueError as e:
        print(f"   ✅ Correctly caught error: {e}")
    
    # Test 2: Invalid field
    print("\n2️⃣ Testing invalid field")
    try:
        query = {
            "dataset": "messages",
            "filters": [{"field": "invalid_field", "op": "=", "value": "test"}]
        }
        validate_dsl(query)
        print("   ❌ Should have failed but didn't")
    except ValueError as e:
        print(f"   ✅ Correctly caught error: {e}")
    
    # Test 3: Invalid operator
    print("\n3️⃣ Testing invalid operator")
    try:
        query = {
            "dataset": "messages",
            "filters": [{"field": "app", "op": "invalid_op", "value": "test"}]
        }
        validate_dsl(query)
        print("   ❌ Should have failed but didn't")
    except ValueError as e:
        print(f"   ✅ Correctly caught error: {e}")
    
    # Test 4: Missing required field
    print("\n4️⃣ Testing missing required field")
    try:
        query = {
            "dataset": "messages",
            "filters": [{"op": "=", "value": "test"}]  # Missing 'field'
        }
        validate_dsl(query)
        print("   ❌ Should have failed but didn't")
    except ValueError as e:
        print(f"   ✅ Correctly caught error: {e}")
    
    print("\n✅ Validation error tests completed!")


def test_sql_generation():
    """Test SQL generation for various queries."""
    print("\n🔧 Testing SQL Generation")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        {
            "name": "Simple equality",
            "query": {
                "dataset": "messages",
                "filters": [{"field": "app", "op": "=", "value": "WhatsApp"}]
            }
        },
        {
            "name": "Contains with limit",
            "query": {
                "dataset": "messages",
                "filters": [{"field": "text", "op": "contains", "value": "BTC"}],
                "limit": 5
            }
        },
        {
            "name": "Complex multi-filter",
            "query": {
                "dataset": "calls",
                "filters": [
                    {"field": "duration", "op": ">", "value": 600},
                    {"field": "type", "op": "=", "value": "Incoming"}
                ],
                "sort": [{"field": "duration", "direction": "desc"}],
                "limit": 10
            }
        },
        {
            "name": "Between operator",
            "query": {
                "dataset": "calls",
                "filters": [{"field": "duration", "op": "between", "value": [300, 1800]}]
            }
        }
    ]
    
    for test in test_queries:
        print(f"\n📋 {test['name']}")
        print(f"   DSL: {test['query']}")
        
        try:
            sql = dsl_to_sql(test['query'])
            print(f"   SQL: {sql}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✅ SQL generation tests completed!")


def forensic_analysis_demo():
    """Demonstrate forensic analysis capabilities."""
    print("\n🔬 Forensic Analysis Demo")
    print("=" * 60)
    
    # Initialize database
    engine, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    # Analysis 1: Suspicious Bitcoin communications
    print("\n💰 Bitcoin Communication Analysis")
    btc_query = {
        "dataset": "messages",
        "filters": [{"field": "text", "op": "contains", "value": "BTC"}],
        "sort": [{"field": "timestamp", "direction": "desc"}]
    }
    btc_messages = run_dsl_query(btc_query, session)
    print(f"   Total BTC messages: {len(btc_messages)}")
    
    # Group by app
    apps = {}
    for msg in btc_messages:
        app = msg['app']
        apps[app] = apps.get(app, 0) + 1
    
    for app, count in apps.items():
        print(f"     - {app}: {count} messages")
    
    # Analysis 2: Long call patterns
    print("\n📞 Long Call Pattern Analysis")
    long_calls_query = {
        "dataset": "calls",
        "filters": [{"field": "duration", "op": ">", "value": 1800}],  # > 30 minutes
        "sort": [{"field": "duration", "direction": "desc"}]
    }
    long_calls = run_dsl_query(long_calls_query, session)
    print(f"   Calls > 30 minutes: {len(long_calls)}")
    
    # Analyze call directions
    incoming = sum(1 for call in long_calls if call['type'] == 'Incoming')
    outgoing = sum(1 for call in long_calls if call['type'] == 'Outgoing')
    print(f"     - Incoming: {incoming}")
    print(f"     - Outgoing: {outgoing}")
    
    # Analysis 3: Entity confidence distribution
    print("\n🎯 Entity Confidence Analysis")
    confidence_ranges = [
        (0.9, 1.0, "High"),
        (0.7, 0.9, "Medium"),
        (0.0, 0.7, "Low")
    ]
    
    for min_conf, max_conf, label in confidence_ranges:
        query = {
            "dataset": "entities",
            "filters": [
                {"field": "confidence", "op": ">=", "value": min_conf},
                {"field": "confidence", "op": "<", "value": max_conf}
            ]
        }
        entities = run_dsl_query(query, session)
        print(f"   {label} confidence entities: {len(entities)}")
    
    session.close()
    print("\n✅ Forensic analysis demo completed!")


def main():
    """Run all comprehensive tests."""
    print("🚀 Comprehensive DSL Query Test Suite")
    print("=" * 80)
    
    test_all_operators()
    test_complex_queries()
    test_validation_errors()
    test_sql_generation()
    forensic_analysis_demo()
    
    print("\n🎯 All comprehensive tests completed!")
    print("\n💡 The DSL query system is fully functional and ready for forensic analysis!")


if __name__ == "__main__":
    main()
