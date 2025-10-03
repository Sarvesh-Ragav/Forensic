#!/usr/bin/env python3
"""
Suspicion Scoring Engine for UFDR Forensic System

Analyzes query results and assigns suspicion scores (0-100) based on
forensic patterns and risk indicators.
"""

import re
from typing import List, Dict, Any, Set
from dataclasses import dataclass
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScoringRule:
    """Scoring rule definition."""
    name: str
    pattern: str
    weight: int
    description: str


class SuspicionScoringEngine:
    """
    Suspicion scoring engine for UFDR forensic analysis.
    """
    
    def __init__(self):
        """Initialize the scoring engine with rules."""
        self.rules = self._initialize_scoring_rules()
        self.suspicious_keywords = self._initialize_suspicious_keywords()
        self.suspicious_domains = self._initialize_suspicious_domains()
        self.foreign_country_codes = self._initialize_foreign_codes()
        
    def _initialize_scoring_rules(self) -> List[ScoringRule]:
        """Initialize scoring rules."""
        return [
            ScoringRule(
                name="crypto_wallet",
                pattern=r"[13][a-km-zA-HJ-NP-Z1-9]{25,34}|0x[a-fA-F0-9]{40}",
                weight=10,
                description="Cryptocurrency wallet addresses (BTC/ETH)"
            ),
            ScoringRule(
                name="foreign_number",
                pattern=r"\+971\d{7,9}|\+44\d{9,10}|\+1\d{10}",
                weight=7,
                description="Foreign phone numbers (UAE, UK, US)"
            ),
            ScoringRule(
                name="long_call",
                pattern=r"duration.*>.*1800",
                weight=5,
                description="Calls longer than 30 minutes"
            ),
            ScoringRule(
                name="suspicious_keywords",
                pattern=r"money|transfer|payment|urgent|asap|bitcoin|wallet",
                weight=6,
                description="Suspicious communication keywords"
            ),
            ScoringRule(
                name="suspicious_email",
                pattern=r"protonmail\.com|tutanota\.com|tempmail\.com",
                weight=8,
                description="Suspicious email domains"
            ),
            ScoringRule(
                name="cross_dataset",
                pattern=r"cross_reference",
                weight=9,
                description="Same contact across multiple datasets"
            )
        ]
    
    def _initialize_suspicious_keywords(self) -> List[str]:
        """Initialize suspicious keywords list."""
        return [
            "money", "transfer", "payment", "urgent", "asap", "bitcoin", "wallet",
            "crypto", "blockchain", "fraud", "scam", "illegal", "criminal",
            "confidential", "secret", "private", "encrypted", "secure",
            "transaction", "deposit", "withdraw", "account", "balance"
        ]
    
    def _initialize_suspicious_domains(self) -> List[str]:
        """Initialize suspicious email domains."""
        return [
            "protonmail.com", "tutanota.com", "tempmail.com", "guerrillamail.com",
            "10minutemail.com", "temp-mail.org", "mailinator.com", "yopmail.com"
        ]
    
    def _initialize_foreign_codes(self) -> List[str]:
        """Initialize foreign country codes."""
        return ["+971", "+44", "+1", "+86", "+33", "+49", "+81", "+61"]
    
    def score_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score query results for suspicion level.
        
        Args:
            results: List of query result dictionaries
            
        Returns:
            List[Dict[str, Any]]: Results with suspicion_score field added
        """
        logger.info(f"Scoring {len(results)} results for suspicion level")
        
        if not results:
            return results
        
        # Calculate base scores for each result
        scored_results = []
        for result in results:
            score = self._calculate_base_score(result)
            result['suspicion_score'] = score
            scored_results.append(result)
        
        # Apply cross-dataset scoring
        scored_results = self._apply_cross_dataset_scoring(scored_results)
        
        # Normalize scores to 0-100 range
        scored_results = self._normalize_scores(scored_results)
        
        # Sort by suspicion score (descending)
        scored_results.sort(key=lambda x: x.get('suspicion_score', 0), reverse=True)
        
        logger.info(f"Scoring completed. Top score: {max(r.get('suspicion_score', 0) for r in scored_results)}")
        return scored_results
    
    def _calculate_base_score(self, result: Dict[str, Any]) -> int:
        """Calculate base suspicion score for a single result."""
        score = 0
        dataset = result.get('dataset', '')
        
        # Crypto wallet detection
        if self._contains_crypto_wallet(result):
            score += 10
            logger.debug(f"Crypto wallet detected: +10 points")
        
        # Foreign number detection
        if self._contains_foreign_number(result):
            score += 7
            logger.debug(f"Foreign number detected: +7 points")
        
        # Long call detection
        if self._is_long_call(result):
            score += 5
            logger.debug(f"Long call detected: +5 points")
        
        # Suspicious keywords detection
        keyword_score = self._count_suspicious_keywords(result)
        if keyword_score > 0:
            score += min(keyword_score * 2, 6)  # Cap at 6 points
            logger.debug(f"Suspicious keywords detected: +{min(keyword_score * 2, 6)} points")
        
        # Suspicious email domain detection
        if self._has_suspicious_email(result):
            score += 8
            logger.debug(f"Suspicious email domain detected: +8 points")
        
        return score
    
    def _contains_crypto_wallet(self, result: Dict[str, Any]) -> bool:
        """Check if result contains cryptocurrency wallet patterns."""
        text_fields = ['text', 'message', 'content', 'value']
        
        for field in text_fields:
            if field in result and result[field]:
                text = str(result[field]).lower()
                # BTC pattern
                if re.search(r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}', text):
                    return True
                # ETH pattern
                if re.search(r'0x[a-fA-F0-9]{40}', text):
                    return True
        
        return False
    
    def _contains_foreign_number(self, result: Dict[str, Any]) -> bool:
        """Check if result contains foreign phone numbers."""
        number_fields = ['sender', 'receiver', 'caller', 'callee', 'number', 'phone']
        
        for field in number_fields:
            if field in result and result[field]:
                number = str(result[field])
                for code in self.foreign_country_codes:
                    if number.startswith(code):
                        return True
        
        return False
    
    def _is_long_call(self, result: Dict[str, Any]) -> bool:
        """Check if result represents a long call."""
        if result.get('dataset') == 'calls' and 'duration' in result:
            duration = result['duration']
            if isinstance(duration, (int, float)) and duration > 1800:  # 30 minutes
                return True
        return False
    
    def _count_suspicious_keywords(self, result: Dict[str, Any]) -> int:
        """Count suspicious keywords in result text."""
        text_fields = ['text', 'message', 'content', 'value', 'name', 'email']
        keyword_count = 0
        
        for field in text_fields:
            if field in result and result[field]:
                text = str(result[field]).lower()
                for keyword in self.suspicious_keywords:
                    if keyword in text:
                        keyword_count += 1
        
        return keyword_count
    
    def _has_suspicious_email(self, result: Dict[str, Any]) -> bool:
        """Check if result has suspicious email domain."""
        email_fields = ['email', 'sender_email', 'receiver_email']
        
        for field in email_fields:
            if field in result and result[field]:
                email = str(result[field]).lower()
                for domain in self.suspicious_domains:
                    if domain in email:
                        return True
        
        return False
    
    def _apply_cross_dataset_scoring(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply cross-dataset scoring for contacts appearing in multiple datasets."""
        # Track contacts across datasets
        contact_occurrences = defaultdict(list)
        
        for i, result in enumerate(results):
            # Extract contact identifiers
            contact_ids = self._extract_contact_identifiers(result)
            for contact_id in contact_ids:
                contact_occurrences[contact_id].append(i)
        
        # Apply cross-dataset bonus
        for contact_id, indices in contact_occurrences.items():
            if len(indices) > 1:  # Contact appears in multiple datasets
                for idx in indices:
                    results[idx]['suspicion_score'] += 9
                    logger.debug(f"Cross-dataset contact {contact_id}: +9 points")
        
        return results
    
    def _extract_contact_identifiers(self, result: Dict[str, Any]) -> List[str]:
        """Extract contact identifiers from result."""
        identifiers = []
        
        # Phone numbers
        phone_fields = ['sender', 'receiver', 'caller', 'callee', 'number']
        for field in phone_fields:
            if field in result and result[field]:
                identifiers.append(f"phone:{result[field]}")
        
        # Email addresses
        email_fields = ['email', 'sender_email', 'receiver_email']
        for field in email_fields:
            if field in result and result[field]:
                identifiers.append(f"email:{result[field]}")
        
        # Names
        if 'name' in result and result['name']:
            identifiers.append(f"name:{result['name']}")
        
        return identifiers
    
    def _normalize_scores(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize suspicion scores to 0-100 range."""
        if not results:
            return results
        
        scores = [r.get('suspicion_score', 0) for r in results]
        max_score = max(scores) if scores else 1
        
        # Handle case where all scores are 0
        if max_score == 0:
            for result in results:
                result['suspicion_score'] = 0
            return results
        
        for result in results:
            current_score = result.get('suspicion_score', 0)
            # Normalize to 0-100 range
            normalized_score = min(100, int((current_score / max_score) * 100))
            result['suspicion_score'] = normalized_score
        
        return results
    
    def get_suspicion_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics for suspicion scores."""
        if not results:
            return {"total_results": 0}
        
        scores = [r.get('suspicion_score', 0) for r in results]
        
        return {
            "total_results": len(results),
            "high_suspicion": len([s for s in scores if s >= 70]),
            "medium_suspicion": len([s for s in scores if 30 <= s < 70]),
            "low_suspicion": len([s for s in scores if s < 30]),
            "max_score": max(scores),
            "avg_score": sum(scores) / len(scores),
            "top_suspicious": [r for r in results[:5] if r.get('suspicion_score', 0) > 0]
        }


def test_suspicion_scoring():
    """Test the suspicion scoring engine with sample data."""
    print("🧪 Testing Suspicion Scoring Engine")
    print("=" * 60)
    
    engine = SuspicionScoringEngine()
    
    # Test case 1: Message with BTC wallet + foreign number
    test_case_1 = {
        "dataset": "messages",
        "id": 1,
        "sender": "+971468044369",
        "receiver": "+919876543210",
        "text": "Send 0.5 BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa ASAP",
        "app": "WhatsApp"
    }
    
    # Test case 2: Long call with no suspicious entities
    test_case_2 = {
        "dataset": "calls",
        "id": 2,
        "caller": "+919876543210",
        "callee": "+919876543211",
        "duration": 3600,  # 60 minutes
        "type": "outgoing"
    }
    
    # Test case 3: Contact with Protonmail account
    test_case_3 = {
        "dataset": "contacts",
        "id": 3,
        "name": "Suspicious Person",
        "number": "+919876543212",
        "email": "suspicious@protonmail.com",
        "app": "WhatsApp"
    }
    
    # Test case 4: Cross-dataset contact
    test_case_4a = {
        "dataset": "messages",
        "id": 4,
        "sender": "+971468044369",
        "receiver": "+919876543210",
        "text": "Meeting at café",
        "app": "WhatsApp"
    }
    
    test_case_4b = {
        "dataset": "calls",
        "id": 5,
        "caller": "+971468044369",
        "callee": "+919876543210",
        "duration": 300,
        "type": "incoming"
    }
    
    # Test cases
    test_cases = [
        ("Message with BTC wallet + foreign number", [test_case_1]),
        ("Long call with no suspicious entities", [test_case_2]),
        ("Contact with Protonmail account", [test_case_3]),
        ("Cross-dataset contact", [test_case_4a, test_case_4b])
    ]
    
    for name, test_data in test_cases:
        print(f"\n🔍 Test Case: {name}")
        print("-" * 40)
        
        scored_results = engine.score_results(test_data)
        
        for result in scored_results:
            print(f"   Score: {result['suspicion_score']}")
            print(f"   Data: {result}")
        
        # Get summary
        summary = engine.get_suspicion_summary(scored_results)
        print(f"   Summary: {summary}")
    
    print("\n✅ Suspicion scoring testing completed!")


def demo_suspicion_scoring():
    """Demo the suspicion scoring engine with real data."""
    print("\n🚀 Suspicion Scoring Engine Demo")
    print("=" * 60)
    
    # Initialize database
    from models import init_db
    engine_db, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    try:
        # Get some real data for scoring
        from dsl_query_tester import run_dsl_query
        
        # Query for messages
        messages_query = {"dataset": "messages", "filters": [], "limit": 10}
        messages = run_dsl_query(messages_query, session)
        
        # Query for calls
        calls_query = {"dataset": "calls", "filters": [], "limit": 10}
        calls = run_dsl_query(calls_query, session)
        
        # Query for contacts
        contacts_query = {"dataset": "contacts", "filters": [], "limit": 10}
        contacts = run_dsl_query(contacts_query, session)
        
        # Combine results
        all_results = messages + calls + contacts
        
        # Initialize scoring engine
        scoring_engine = SuspicionScoringEngine()
        
        # Score results
        print(f"📊 Scoring {len(all_results)} results...")
        scored_results = scoring_engine.score_results(all_results)
        
        # Show top suspicious results
        print(f"\n🎯 Top 5 Most Suspicious Results:")
        for i, result in enumerate(scored_results[:5], 1):
            score = result.get('suspicion_score', 0)
            dataset = result.get('dataset', 'unknown')
            print(f"  {i}. [{dataset}] Score: {score}")
            if 'text' in result:
                print(f"     Text: {result['text'][:50]}...")
            elif 'name' in result:
                print(f"     Name: {result['name']}")
            print()
        
        # Get summary
        summary = scoring_engine.get_suspicion_summary(scored_results)
        print(f"📈 Suspicion Summary:")
        print(f"   Total results: {summary['total_results']}")
        print(f"   High suspicion (≥70): {summary['high_suspicion']}")
        print(f"   Medium suspicion (30-69): {summary['medium_suspicion']}")
        print(f"   Low suspicion (<30): {summary['low_suspicion']}")
        print(f"   Max score: {summary['max_score']}")
        print(f"   Average score: {summary['avg_score']:.1f}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    print("\n✅ Suspicion scoring demo completed!")


if __name__ == "__main__":
    test_suspicion_scoring()
    demo_suspicion_scoring()
