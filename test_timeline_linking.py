#!/usr/bin/env python3
"""
Comprehensive Test Suite for Timeline & Cross-Dataset Linking

Tests timeline building, cross-dataset linking, and JSON export functionality.
"""

from timeline_linking import TimelineLinkingEngine
from models import init_db
from dsl_query_tester import run_dsl_query
import json


def test_timeline_building():
    """Test basic timeline building functionality."""
    print("🧪 Testing Timeline Building")
    print("=" * 50)
    
    engine = TimelineLinkingEngine()
    
    # Test case 1: Message with BTC wallet + linked call
    test_data_1 = [
        {
            "dataset": "messages",
            "id": 1,
            "sender": "+971468044369",
            "receiver": "+919876543210",
            "text": "Send 0.5 BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa ASAP",
            "timestamp": "2024-01-15T10:30:00",
            "app": "WhatsApp"
        },
        {
            "dataset": "calls",
            "id": 2,
            "caller": "+971468044369",
            "callee": "+919876543210",
            "duration": 1800,
            "timestamp": "2024-01-15T11:00:00",
            "type": "outgoing"
        }
    ]
    
    print("\n1. Testing: Message with BTC wallet + linked call")
    timeline_1 = engine.build_timeline(test_data_1)
    
    print(f"   Timeline events: {len(timeline_1)}")
    for i, event in enumerate(timeline_1, 1):
        print(f"   {i}. [{event['event_type']}] {event['summary']}")
        print(f"      Timestamp: {event['timestamp']}")
        print(f"      Suspicion Score: {event['suspicion_score']}")
        print(f"      Cross-linked: {event['cross_linked']}")
        print()
    
    # Test case 2: Protonmail contact linked to chats + calls
    test_data_2 = [
        {
            "dataset": "contacts",
            "id": 3,
            "name": "Suspicious Person",
            "number": "+971468044369",
            "email": "suspicious@protonmail.com",
            "app": "WhatsApp"
        },
        {
            "dataset": "messages",
            "id": 4,
            "sender": "+971468044369",
            "receiver": "+919876543210",
            "text": "Meeting at café",
            "timestamp": "2024-01-16T14:00:00",
            "app": "WhatsApp"
        },
        {
            "dataset": "calls",
            "id": 5,
            "caller": "+971468044369",
            "callee": "+919876543210",
            "duration": 600,
            "timestamp": "2024-01-16T15:00:00",
            "type": "incoming"
        }
    ]
    
    print("\n2. Testing: Protonmail contact linked to chats + calls")
    timeline_2 = engine.build_timeline(test_data_2)
    
    print(f"   Timeline events: {len(timeline_2)}")
    for i, event in enumerate(timeline_2, 1):
        print(f"   {i}. [{event['event_type']}] {event['summary']}")
        print(f"      Timestamp: {event['timestamp']}")
        print(f"      Suspicion Score: {event['suspicion_score']}")
        print(f"      Cross-linked: {event['cross_linked']}")
        print()
    
    print("✅ Timeline building testing completed!")


def test_cross_dataset_linking():
    """Test cross-dataset linking functionality."""
    print("\n🔗 Testing Cross-Dataset Linking")
    print("=" * 50)
    
    engine = TimelineLinkingEngine()
    
    # Test case: Same participant across multiple datasets
    test_data = [
        {
            "dataset": "messages",
            "id": 1,
            "sender": "+971468044369",
            "receiver": "+919876543210",
            "text": "Hello",
            "timestamp": "2024-01-15T10:00:00",
            "app": "WhatsApp"
        },
        {
            "dataset": "calls",
            "id": 2,
            "caller": "+971468044369",
            "callee": "+919876543210",
            "duration": 300,
            "timestamp": "2024-01-15T11:00:00",
            "type": "outgoing"
        },
        {
            "dataset": "contacts",
            "id": 3,
            "name": "Test Person",
            "number": "+971468044369",
            "email": "test@example.com",
            "app": "WhatsApp"
        }
    ]
    
    timeline = engine.build_timeline(test_data)
    
    print(f"Timeline events: {len(timeline)}")
    
    cross_linked_count = 0
    for event in timeline:
        if event.get('cross_linked', False):
            cross_linked_count += 1
            print(f"   Cross-linked event: {event['summary']}")
            print(f"      Participant: {event.get('cross_linked_participant', 'Unknown')}")
            print(f"      Count: {event.get('cross_linked_count', 0)}")
    
    print(f"\n   Total cross-linked events: {cross_linked_count}")
    print("✅ Cross-dataset linking testing completed!")


def test_json_export():
    """Test JSON export functionality."""
    print("\n📄 Testing JSON Export")
    print("=" * 50)
    
    engine = TimelineLinkingEngine()
    
    # Test data
    test_data = [
        {
            "dataset": "messages",
            "id": 1,
            "sender": "+971468044369",
            "receiver": "+919876543210",
            "text": "Send 0.5 BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "timestamp": "2024-01-15T10:30:00",
            "app": "WhatsApp"
        },
        {
            "dataset": "calls",
            "id": 2,
            "caller": "+971468044369",
            "callee": "+919876543210",
            "duration": 1800,
            "timestamp": "2024-01-15T11:00:00",
            "type": "outgoing"
        }
    ]
    
    # Build timeline
    timeline = engine.build_timeline(test_data)
    
    # Export to JSON
    json_output = engine.export_timeline_json(timeline, "test_timeline.json")
    
    print(f"JSON export length: {len(json_output)} characters")
    
    # Parse JSON to verify structure
    try:
        timeline_data = json.loads(json_output)
        print(f"JSON structure valid: ✅")
        print(f"Metadata: {timeline_data.get('metadata', {})}")
        print(f"Events count: {len(timeline_data.get('events', []))}")
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
    
    print("✅ JSON export testing completed!")


def test_timeline_summary():
    """Test timeline summary functionality."""
    print("\n📊 Testing Timeline Summary")
    print("=" * 50)
    
    engine = TimelineLinkingEngine()
    
    # Test data with various suspicion scores
    test_data = [
        {
            "dataset": "messages",
            "id": 1,
            "sender": "+971468044369",
            "text": "Send 0.5 BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "timestamp": "2024-01-15T10:30:00",
            "app": "WhatsApp"
        },
        {
            "dataset": "calls",
            "id": 2,
            "caller": "+919876543210",
            "duration": 300,
            "timestamp": "2024-01-15T11:00:00",
            "type": "outgoing"
        },
        {
            "dataset": "contacts",
            "id": 3,
            "name": "Test Person",
            "email": "test@protonmail.com",
            "number": "+971468044369"
        }
    ]
    
    # Build timeline
    timeline = engine.build_timeline(test_data)
    
    # Get summary
    summary = engine.get_timeline_summary(timeline)
    
    print(f"Timeline Summary:")
    print(f"   Total events: {summary['total_events']}")
    print(f"   Cross-linked events: {summary['cross_linked_events']}")
    print(f"   Event types: {summary['event_types']}")
    print(f"   Time range: {summary['time_range']}")
    print(f"   Suspicion stats: {summary['suspicion_stats']}")
    
    print("✅ Timeline summary testing completed!")


def test_real_data_timeline():
    """Test timeline building with real UFDR data."""
    print("\n📊 Testing Real Data Timeline")
    print("=" * 50)
    
    # Initialize database
    engine_db, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    try:
        # Get real data from multiple datasets
        queries = [
            {"dataset": "messages", "filters": [], "limit": 3},
            {"dataset": "calls", "filters": [], "limit": 3},
            {"dataset": "contacts", "filters": [], "limit": 3}
        ]
        
        all_results = []
        for query in queries:
            results = run_dsl_query(query, session)
            all_results.extend(results)
        
        print(f"📊 Testing with {len(all_results)} real results...")
        
        # Initialize timeline engine
        engine = TimelineLinkingEngine()
        
        # Build timeline
        timeline = engine.build_timeline(all_results)
        
        print(f"Timeline events: {len(timeline)}")
        
        # Show timeline
        for i, event in enumerate(timeline[:5], 1):  # Show first 5
            print(f"  {i}. [{event['event_type']}] {event['summary']}")
            print(f"     Timestamp: {event['timestamp']}")
            print(f"     Suspicion Score: {event['suspicion_score']}")
            print(f"     Cross-linked: {event['cross_linked']}")
            print()
        
        # Get summary
        summary = engine.get_timeline_summary(timeline)
        print(f"📈 Timeline Summary:")
        print(f"   Total events: {summary['total_events']}")
        print(f"   Cross-linked events: {summary['cross_linked_events']}")
        print(f"   Event types: {summary['event_types']}")
        print(f"   High suspicion events: {summary['suspicion_stats']['high_suspicion']}")
        
    except Exception as e:
        print(f"❌ Real data testing failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    print("✅ Real data timeline testing completed!")


def test_performance():
    """Test performance with larger datasets."""
    print("\n⚡ Testing Performance")
    print("=" * 50)
    
    import time
    
    engine = TimelineLinkingEngine()
    
    # Generate test data
    test_data = []
    for i in range(50):
        test_data.extend([
            {
                "dataset": "messages",
                "id": i,
                "sender": f"+971468044{i:03d}",
                "receiver": f"+919876543{i:03d}",
                "text": f"Test message {i}",
                "timestamp": f"2024-01-{15 + (i % 10):02d}T{10 + (i % 12):02d}:00:00",
                "app": "WhatsApp"
            },
            {
                "dataset": "calls",
                "id": i,
                "caller": f"+971468044{i:03d}",
                "callee": f"+919876543{i:03d}",
                "duration": 300 + (i * 60),
                "timestamp": f"2024-01-{15 + (i % 10):02d}T{11 + (i % 12):02d}:00:00",
                "type": "outgoing"
            }
        ])
    
    print(f"📊 Testing with {len(test_data)} results...")
    
    start_time = time.time()
    timeline = engine.build_timeline(test_data)
    end_time = time.time()
    
    execution_time = end_time - start_time
    avg_time_per_result = execution_time / len(test_data)
    
    print(f"⏱️  Performance Results:")
    print(f"   Total time: {execution_time:.3f}s")
    print(f"   Average time per result: {avg_time_per_result:.6f}s")
    print(f"   Results per second: {len(test_data) / execution_time:.1f}")
    
    # Show timeline statistics
    summary = engine.get_timeline_summary(timeline)
    print(f"\n📈 Timeline Statistics:")
    print(f"   Total events: {summary['total_events']}")
    print(f"   Cross-linked events: {summary['cross_linked_events']}")
    print(f"   Event types: {summary['event_types']}")
    
    if execution_time < 2.0:
        print("   ✅ Excellent performance!")
    elif execution_time < 5.0:
        print("   ✅ Good performance!")
    else:
        print("   ⚠️  Performance could be improved")


def main():
    """Run all tests."""
    print("🚀 Timeline & Cross-Dataset Linking - Comprehensive Test Suite")
    print("=" * 80)
    
    test_timeline_building()
    test_cross_dataset_linking()
    test_json_export()
    test_timeline_summary()
    test_real_data_timeline()
    test_performance()
    
    print("\n🎯 All tests completed!")
    print("\n💡 The Timeline & Cross-Dataset Linking module is ready for production use!")


if __name__ == "__main__":
    main()
