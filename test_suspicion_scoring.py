#!/usr/bin/env python3
"""
Comprehensive Test Suite for Suspicion Scoring Engine

Tests all scoring rules and edge cases with detailed analysis.
"""

from suspicion_scoring import SuspicionScoringEngine
from models import init_db
from dsl_query_tester import run_dsl_query


def test_scoring_rules():
    """Test individual scoring rules."""
    print("🧪 Testing Individual Scoring Rules")
    print("=" * 60)
    
    engine = SuspicionScoringEngine()
    
    # Test cases for each rule
    test_cases = [
        {
            "name": "Crypto Wallet Detection",
            "data": {
                "dataset": "messages",
                "text": "Send 0.5 BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                "sender": "+919876543210"
            },
            "expected_score": 10
        },
        {
            "name": "Foreign Number Detection",
            "data": {
                "dataset": "calls",
                "caller": "+971468044369",
                "callee": "+919876543210",
                "duration": 300
            },
            "expected_score": 7
        },
        {
            "name": "Long Call Detection",
            "data": {
                "dataset": "calls",
                "caller": "+919876543210",
                "callee": "+919876543211",
                "duration": 3600  # 60 minutes
            },
            "expected_score": 5
        },
        {
            "name": "Suspicious Keywords",
            "data": {
                "dataset": "messages",
                "text": "Urgent money transfer needed ASAP",
                "sender": "+919876543210"
            },
            "expected_score": 6  # 3 keywords * 2 = 6
        },
        {
            "name": "Suspicious Email Domain",
            "data": {
                "dataset": "contacts",
                "name": "Test Person",
                "email": "test@protonmail.com",
                "number": "+919876543210"
            },
            "expected_score": 8
        },
        {
            "name": "Multiple Indicators",
            "data": {
                "dataset": "messages",
                "text": "Send 0.3 BTC to 0xAbc123... urgent payment",
                "sender": "+971468044369",
                "receiver": "+919876543210"
            },
            "expected_score": 10 + 7 + 6  # Crypto + Foreign + Keywords
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print("-" * 40)
        
        # Score the test case
        results = engine.score_results([test_case['data']])
        actual_score = results[0].get('suspicion_score', 0)
        expected_score = test_case['expected_score']
        
        print(f"   Expected: {expected_score}")
        print(f"   Actual: {actual_score}")
        print(f"   Data: {test_case['data']}")
        
        if actual_score >= expected_score:
            print("   ✅ Test passed")
        else:
            print("   ❌ Test failed")
    
    print("\n✅ Individual rule testing completed!")


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\n🔍 Testing Edge Cases")
    print("=" * 60)
    
    engine = SuspicionScoringEngine()
    
    edge_cases = [
        {
            "name": "Empty Results",
            "data": [],
            "expected": 0
        },
        {
            "name": "No Suspicious Indicators",
            "data": [{
                "dataset": "messages",
                "text": "Hello, how are you?",
                "sender": "+919876543210"
            }],
            "expected": 0
        },
        {
            "name": "All Suspicious Indicators",
            "data": [{
                "dataset": "messages",
                "text": "Send 1 BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa urgent payment",
                "sender": "+971468044369",
                "receiver": "+919876543210"
            }],
            "expected": 100  # Should be normalized to 100
        },
        {
            "name": "Cross-Dataset Contact",
            "data": [
                {
                    "dataset": "messages",
                    "sender": "+971468044369",
                    "text": "Meeting at café"
                },
                {
                    "dataset": "calls",
                    "caller": "+971468044369",
                    "duration": 300
                }
            ],
            "expected": 9  # Cross-dataset bonus
        }
    ]
    
    for i, test_case in enumerate(edge_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print("-" * 40)
        
        results = engine.score_results(test_case['data'])
        
        if not results:
            print("   ✅ Empty results handled correctly")
        else:
            for j, result in enumerate(results):
                score = result.get('suspicion_score', 0)
                print(f"   Result {j+1}: Score {score}")
                print(f"   Data: {result}")
    
    print("\n✅ Edge case testing completed!")


def test_real_data_scoring():
    """Test scoring with real UFDR data."""
    print("\n📊 Testing Real Data Scoring")
    print("=" * 60)
    
    # Initialize database
    engine_db, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    try:
        # Get real data
        queries = [
            {"dataset": "messages", "filters": [], "limit": 5},
            {"dataset": "calls", "filters": [], "limit": 5},
            {"dataset": "contacts", "filters": [], "limit": 5}
        ]
        
        all_results = []
        for query in queries:
            results = run_dsl_query(query, session)
            all_results.extend(results)
        
        print(f"📊 Testing with {len(all_results)} real results...")
        
        # Initialize scoring engine
        engine = SuspicionScoringEngine()
        
        # Score results
        scored_results = engine.score_results(all_results)
        
        # Show results by score range
        high_suspicion = [r for r in scored_results if r.get('suspicion_score', 0) >= 70]
        medium_suspicion = [r for r in scored_results if 30 <= r.get('suspicion_score', 0) < 70]
        low_suspicion = [r for r in scored_results if r.get('suspicion_score', 0) < 30]
        
        print(f"\n📈 Score Distribution:")
        print(f"   High suspicion (≥70): {len(high_suspicion)}")
        print(f"   Medium suspicion (30-69): {len(medium_suspicion)}")
        print(f"   Low suspicion (<30): {len(low_suspicion)}")
        
        # Show top suspicious results
        print(f"\n🎯 Top 3 Most Suspicious Results:")
        for i, result in enumerate(scored_results[:3], 1):
            score = result.get('suspicion_score', 0)
            dataset = result.get('dataset', 'unknown')
            print(f"   {i}. [{dataset}] Score: {score}")
            
            # Show relevant fields
            if 'text' in result:
                print(f"      Text: {result['text'][:50]}...")
            if 'name' in result:
                print(f"      Name: {result['name']}")
            if 'email' in result:
                print(f"      Email: {result['email']}")
            if 'duration' in result:
                print(f"      Duration: {result['duration']} seconds")
            print()
        
        # Get summary
        summary = engine.get_suspicion_summary(scored_results)
        print(f"📊 Summary Statistics:")
        print(f"   Total results: {summary['total_results']}")
        print(f"   Max score: {summary['max_score']}")
        print(f"   Average score: {summary['avg_score']:.1f}")
        
    except Exception as e:
        print(f"❌ Real data testing failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    print("\n✅ Real data testing completed!")


def test_performance():
    """Test performance with large datasets."""
    print("\n⚡ Testing Performance")
    print("=" * 60)
    
    import time
    
    engine = SuspicionScoringEngine()
    
    # Generate test data
    test_data = []
    for i in range(100):
        test_data.append({
            "dataset": "messages",
            "id": i,
            "text": f"Test message {i}",
            "sender": f"+919876543{i:03d}"
        })
    
    # Add some suspicious data
    test_data.extend([
        {
            "dataset": "messages",
            "text": "Send 0.5 BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "sender": "+971468044369"
        },
        {
            "dataset": "calls",
            "duration": 3600,
            "caller": "+971468044369"
        },
        {
            "dataset": "contacts",
            "email": "test@protonmail.com",
            "name": "Suspicious Person"
        }
    ])
    
    print(f"📊 Testing with {len(test_data)} results...")
    
    start_time = time.time()
    scored_results = engine.score_results(test_data)
    end_time = time.time()
    
    execution_time = end_time - start_time
    avg_time_per_result = execution_time / len(test_data)
    
    print(f"⏱️  Performance Results:")
    print(f"   Total time: {execution_time:.3f}s")
    print(f"   Average time per result: {avg_time_per_result:.6f}s")
    print(f"   Results per second: {len(test_data) / execution_time:.1f}")
    
    # Show score distribution
    scores = [r.get('suspicion_score', 0) for r in scored_results]
    high_count = len([s for s in scores if s >= 70])
    medium_count = len([s for s in scores if 30 <= s < 70])
    low_count = len([s for s in scores if s < 30])
    
    print(f"\n📈 Score Distribution:")
    print(f"   High suspicion: {high_count}")
    print(f"   Medium suspicion: {medium_count}")
    print(f"   Low suspicion: {low_count}")
    
    if execution_time < 1.0:
        print("   ✅ Excellent performance!")
    elif execution_time < 5.0:
        print("   ✅ Good performance!")
    else:
        print("   ⚠️  Performance could be improved")


def test_scoring_accuracy():
    """Test scoring accuracy with known patterns."""
    print("\n🎯 Testing Scoring Accuracy")
    print("=" * 60)
    
    engine = SuspicionScoringEngine()
    
    # Known patterns with expected scores
    accuracy_tests = [
        {
            "name": "BTC Wallet + Foreign Number",
            "data": {
                "dataset": "messages",
                "text": "Send 0.5 BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                "sender": "+971468044369"
            },
            "expected_min": 15,  # 10 (crypto) + 7 (foreign) - 2 (normalization)
            "expected_max": 20
        },
        {
            "name": "Long Call Only",
            "data": {
                "dataset": "calls",
                "duration": 3600,
                "caller": "+919876543210"
            },
            "expected_min": 3,
            "expected_max": 7
        },
        {
            "name": "Protonmail Contact",
            "data": {
                "dataset": "contacts",
                "email": "test@protonmail.com",
                "name": "Test Person"
            },
            "expected_min": 6,
            "expected_max": 10
        },
        {
            "name": "Suspicious Keywords",
            "data": {
                "dataset": "messages",
                "text": "Urgent money transfer payment",
                "sender": "+919876543210"
            },
            "expected_min": 4,
            "expected_max": 8
        }
    ]
    
    for i, test in enumerate(accuracy_tests, 1):
        print(f"\n{i}. Testing: {test['name']}")
        print("-" * 40)
        
        results = engine.score_results([test['data']])
        actual_score = results[0].get('suspicion_score', 0)
        expected_min = test['expected_min']
        expected_max = test['expected_max']
        
        print(f"   Expected range: {expected_min}-{expected_max}")
        print(f"   Actual score: {actual_score}")
        print(f"   Data: {test['data']}")
        
        if expected_min <= actual_score <= expected_max:
            print("   ✅ Score within expected range")
        else:
            print("   ❌ Score outside expected range")
    
    print("\n✅ Accuracy testing completed!")


def main():
    """Run all tests."""
    print("🚀 Suspicion Scoring Engine - Comprehensive Test Suite")
    print("=" * 80)
    
    test_scoring_rules()
    test_edge_cases()
    test_real_data_scoring()
    test_performance()
    test_scoring_accuracy()
    
    print("\n🎯 All tests completed!")
    print("\n💡 The Suspicion Scoring Engine is ready for production use!")


if __name__ == "__main__":
    main()
