#!/usr/bin/env python3
"""
Test script for Forensic DSL functionality.

This script demonstrates and tests the DSL query engine with various scenarios.
"""

import json
from forensic_dsl import (
    ForensicQuery, FilterCondition, SortCondition, 
    validate_dsl_query, dsl_to_sql, EXAMPLE_QUERIES
)


def test_basic_queries():
    """Test basic DSL queries."""
    print("🧪 Testing Basic DSL Queries")
    print("=" * 50)
    
    # Test 1: WhatsApp messages with UAE numbers
    query1 = {
        "dataset": "messages",
        "filters": [
            {"field": "app", "op": "=", "value": "WhatsApp"},
            {"field": "receiver", "op": "country", "value": "UAE"}
        ]
    }
    
    print("\n📱 Query 1: WhatsApp messages with UAE numbers")
    print(f"DSL: {json.dumps(query1, indent=2)}")
    
    try:
        validated_query = validate_dsl_query(query1)
        sql = dsl_to_sql(validated_query)
        print(f"✅ Validated successfully")
        print(f"🔧 SQL: {sql}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Long calls
    query2 = {
        "dataset": "calls",
        "filters": [
            {"field": "duration", "op": ">", "value": 600}
        ]
    }
    
    print("\n📞 Query 2: Calls longer than 10 minutes")
    print(f"DSL: {json.dumps(query2, indent=2)}")
    
    try:
        validated_query = validate_dsl_query(query2)
        sql = dsl_to_sql(validated_query)
        print(f"✅ Validated successfully")
        print(f"🔧 SQL: {sql}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: ProtonMail contacts
    query3 = {
        "dataset": "contacts",
        "filters": [
            {"field": "email", "op": "contains", "value": "protonmail"}
        ]
    }
    
    print("\n👥 Query 3: Contacts with ProtonMail emails")
    print(f"DSL: {json.dumps(query3, indent=2)}")
    
    try:
        validated_query = validate_dsl_query(query3)
        sql = dsl_to_sql(validated_query)
        print(f"✅ Validated successfully")
        print(f"🔧 SQL: {sql}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_advanced_queries():
    """Test advanced DSL queries with multiple filters and sorting."""
    print("\n🚀 Testing Advanced DSL Queries")
    print("=" * 50)
    
    # Test 1: Complex message query with sorting and limit
    query1 = {
        "dataset": "messages",
        "filters": [
            {"field": "app", "op": "in", "value": ["Telegram", "Signal"]},
            {"field": "text", "op": "contains", "value": "bitcoin"},
            {"field": "timestamp", "op": ">=", "value": "2024-01-01"}
        ],
        "sort": [
            {"field": "timestamp", "direction": "desc"}
        ],
        "limit": 50
    }
    
    print("\n🔍 Query 1: Suspicious communications with sorting")
    print(f"DSL: {json.dumps(query1, indent=2)}")
    
    try:
        validated_query = validate_dsl_query(query1)
        sql = dsl_to_sql(validated_query)
        print(f"✅ Validated successfully")
        print(f"🔧 SQL: {sql}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Entity query with confidence filtering
    query2 = {
        "dataset": "entities",
        "filters": [
            {"field": "type", "op": "=", "value": "bitcoin"},
            {"field": "confidence", "op": ">=", "value": 0.8},
            {"field": "linked_message_id", "op": "is_not_null", "value": None}
        ],
        "sort": [
            {"field": "confidence", "direction": "desc"},
            {"field": "id", "direction": "asc"}
        ]
    }
    
    print("\n💰 Query 2: High-confidence Bitcoin entities")
    print(f"DSL: {json.dumps(query2, indent=2)}")
    
    try:
        validated_query = validate_dsl_query(query2)
        sql = dsl_to_sql(validated_query)
        print(f"✅ Validated successfully")
        print(f"🔧 SQL: {sql}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_error_handling():
    """Test error handling and validation."""
    print("\n⚠️  Testing Error Handling")
    print("=" * 50)
    
    # Test 1: Invalid dataset
    query1 = {
        "dataset": "invalid_dataset",
        "filters": [
            {"field": "app", "op": "=", "value": "WhatsApp"}
        ]
    }
    
    print("\n❌ Test 1: Invalid dataset")
    print(f"DSL: {json.dumps(query1, indent=2)}")
    
    try:
        validated_query = validate_dsl_query(query1)
        print(f"❌ Should have failed but didn't")
    except Exception as e:
        print(f"✅ Correctly caught error: {e}")
    
    # Test 2: Invalid field for dataset
    query2 = {
        "dataset": "messages",
        "filters": [
            {"field": "invalid_field", "op": "=", "value": "test"}
        ]
    }
    
    print("\n❌ Test 2: Invalid field for dataset")
    print(f"DSL: {json.dumps(query2, indent=2)}")
    
    try:
        validated_query = validate_dsl_query(query2)
        sql = dsl_to_sql(validated_query)
        print(f"❌ Should have failed but didn't")
    except Exception as e:
        print(f"✅ Correctly caught error: {e}")
    
    # Test 3: Invalid operator
    query3 = {
        "dataset": "messages",
        "filters": [
            {"field": "app", "op": "invalid_op", "value": "WhatsApp"}
        ]
    }
    
    print("\n❌ Test 3: Invalid operator")
    print(f"DSL: {json.dumps(query3, indent=2)}")
    
    try:
        validated_query = validate_dsl_query(query3)
        print(f"❌ Should have failed but didn't")
    except Exception as e:
        print(f"✅ Correctly caught error: {e}")
    
    # Test 4: Country filter on non-phone field
    query4 = {
        "dataset": "messages",
        "filters": [
            {"field": "text", "op": "country", "value": "UAE"}
        ]
    }
    
    print("\n❌ Test 4: Country filter on non-phone field")
    print(f"DSL: {json.dumps(query4, indent=2)}")
    
    try:
        validated_query = validate_dsl_query(query4)
        sql = dsl_to_sql(validated_query)
        print(f"❌ Should have failed but didn't")
    except Exception as e:
        print(f"✅ Correctly caught error: {e}")


def test_example_queries():
    """Test all example queries."""
    print("\n📚 Testing Example Queries")
    print("=" * 50)
    
    for name, query_dict in EXAMPLE_QUERIES.items():
        print(f"\n🔍 Example: {name}")
        print(f"DSL: {json.dumps(query_dict, indent=2)}")
        
        try:
            validated_query = validate_dsl_query(query_dict)
            sql = dsl_to_sql(validated_query)
            print(f"✅ Validated successfully")
            print(f"🔧 SQL: {sql}")
        except Exception as e:
            print(f"❌ Error: {e}")


def test_json_string_input():
    """Test DSL with JSON string input."""
    print("\n📄 Testing JSON String Input")
    print("=" * 50)
    
    json_query = '''
    {
        "dataset": "entities",
        "filters": [
            {"field": "type", "op": "=", "value": "bitcoin"},
            {"field": "confidence", "op": ">=", "value": 0.9}
        ],
        "sort": [{"field": "confidence", "direction": "desc"}],
        "limit": 10
    }
    '''
    
    print(f"JSON Input: {json_query}")
    
    try:
        validated_query = validate_dsl_query(json_query)
        sql = dsl_to_sql(validated_query)
        print(f"✅ Validated successfully")
        print(f"🔧 SQL: {sql}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all tests."""
    print("🔬 Forensic DSL Test Suite")
    print("=" * 60)
    
    test_basic_queries()
    test_advanced_queries()
    test_error_handling()
    test_example_queries()
    test_json_string_input()
    
    print("\n🎯 All tests completed!")


if __name__ == "__main__":
    main()
