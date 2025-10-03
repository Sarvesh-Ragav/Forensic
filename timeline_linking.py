#!/usr/bin/env python3
"""
Timeline & Cross-Dataset Linking Module for UFDR Forensic System

This module provides functionality to build chronological timelines from query results
across multiple datasets (messages, calls, contacts) with cross-dataset linking and
entity enrichment.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TimelineEvent:
    """Represents a single event in the timeline."""
    event_id: str
    event_type: str  # 'message', 'call', 'contact'
    timestamp: datetime
    dataset: str
    data: Dict[str, Any]
    linked_entities: List[Dict[str, Any]]
    cross_linked: bool = False
    suspicion_score: int = 0


class TimelineBuilder:
    """
    Timeline builder for UFDR forensic analysis.
    """
    
    def __init__(self):
        """Initialize the timeline builder."""
        self.contact_identifiers = defaultdict(set)  # Track contacts across datasets
        self.entity_cache = {}  # Cache for entity lookups
        
    def build_timeline(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build chronological timeline from query results.
        
        Args:
            results: List of query result dictionaries from multiple datasets
            
        Returns:
            List[Dict[str, Any]]: Chronological timeline events in JSON format
        """
        logger.info(f"Building timeline from {len(results)} results")
        
        if not results:
            return []
        
        # Step 1: Extract and categorize events
        events = self._extract_events(results)
        
        # Step 2: Build contact identifier mapping for cross-linking
        self._build_contact_mapping(events)
        
        # Step 3: Enrich events with linked entities and cross-linking
        enriched_events = self._enrich_events(events)
        
        # Step 4: Sort events chronologically
        sorted_events = sorted(enriched_events, key=lambda x: x.timestamp)
        
        # Step 5: Convert to JSON format
        timeline_json = self._convert_to_json(sorted_events)
        
        logger.info(f"Timeline built with {len(timeline_json)} events")
        return timeline_json
    
    def _extract_events(self, results: List[Dict[str, Any]]) -> List[TimelineEvent]:
        """Extract and categorize events from query results."""
        events = []
        
        for result in results:
            event_type = self._determine_event_type(result)
            if not event_type:
                continue
                
            # Create timeline event
            event = TimelineEvent(
                event_id=self._generate_event_id(result),
                event_type=event_type,
                timestamp=self._extract_timestamp(result),
                dataset=result.get('dataset', 'unknown'),
                data=result,
                linked_entities=[],
                cross_linked=False,
                suspicion_score=result.get('suspicion_score', 0)
            )
            
            events.append(event)
        
        return events
    
    def _determine_event_type(self, result: Dict[str, Any]) -> Optional[str]:
        """Determine the event type from result data."""
        dataset = result.get('dataset', '').lower()
        
        if dataset == 'messages':
            return 'message'
        elif dataset == 'calls':
            return 'call'
        elif dataset == 'contacts':
            return 'contact'
        
        # Fallback: determine by data structure
        if 'text' in result or 'message' in result:
            return 'message'
        elif 'duration' in result or 'caller' in result or 'callee' in result:
            return 'call'
        elif 'name' in result and ('number' in result or 'email' in result):
            return 'contact'
        
        return None
    
    def _generate_event_id(self, result: Dict[str, Any]) -> str:
        """Generate unique event ID."""
        dataset = result.get('dataset', 'unknown')
        record_id = result.get('id', result.get('MessageID', result.get('CallID', result.get('ContactID', 'unknown'))))
        return f"{dataset}_{record_id}"
    
    def _extract_timestamp(self, result: Dict[str, Any]) -> datetime:
        """Extract timestamp from result data."""
        # Try different timestamp field names
        timestamp_fields = ['timestamp', 'Timestamp', 'created_at', 'date']
        
        for field in timestamp_fields:
            if field in result and result[field]:
                timestamp_str = str(result[field])
                try:
                    # Handle different timestamp formats
                    if 'T' in timestamp_str:
                        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        # Handle format like "2024-09-10 04:47"
                        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    continue
        
        # Fallback to current time if no valid timestamp found
        logger.warning(f"No valid timestamp found for result: {result.get('id', 'unknown')}")
        return datetime.now()
    
    def _build_contact_mapping(self, events: List[TimelineEvent]):
        """Build mapping of contact identifiers across datasets."""
        self.contact_identifiers.clear()
        
        for event in events:
            identifiers = self._extract_contact_identifiers(event.data)
            for identifier in identifiers:
                self.contact_identifiers[identifier].add(event.event_id)
    
    def _extract_contact_identifiers(self, data: Dict[str, Any]) -> List[str]:
        """Extract contact identifiers from event data."""
        identifiers = []
        
        # Phone numbers
        phone_fields = ['sender', 'receiver', 'caller', 'callee', 'number', 'phone', 
                       'SenderNumber', 'ReceiverNumber', 'CallerNumber', 'CalleeNumber', 'PhoneNumber']
        for field in phone_fields:
            if field in data and data[field]:
                identifiers.append(f"phone:{data[field]}")
        
        # Email addresses
        email_fields = ['email', 'Email']
        for field in email_fields:
            if field in data and data[field]:
                identifiers.append(f"email:{data[field]}")
        
        # Names
        if 'name' in data and data['name']:
            identifiers.append(f"name:{data['name']}")
        
        return identifiers
    
    def _enrich_events(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """Enrich events with linked entities and cross-linking information."""
        enriched_events = []
        
        for event in events:
            # Add linked entities
            event.linked_entities = self._get_linked_entities(event)
            
            # Check for cross-linking
            event.cross_linked = self._check_cross_linking(event)
            
            enriched_events.append(event)
        
        return enriched_events
    
    def _get_linked_entities(self, event: TimelineEvent) -> List[Dict[str, Any]]:
        """Get linked entities for an event."""
        entities = []
        
        # Extract entities from the event data
        if event.event_type == 'message':
            entities.extend(self._extract_message_entities(event.data))
        elif event.event_type == 'call':
            entities.extend(self._extract_call_entities(event.data))
        elif event.event_type == 'contact':
            entities.extend(self._extract_contact_entities(event.data))
        
        return entities
    
    def _extract_message_entities(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract entities from message data."""
        entities = []
        text = data.get('text', data.get('MessageText', ''))
        
        if text:
            # Bitcoin addresses
            import re
            btc_pattern = r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}'
            btc_matches = re.findall(btc_pattern, text)
            for match in btc_matches:
                entities.append({
                    'type': 'bitcoin',
                    'value': match,
                    'confidence': 0.95
                })
            
            # Ethereum addresses
            eth_pattern = r'0x[a-fA-F0-9]{40}'
            eth_matches = re.findall(eth_pattern, text)
            for match in eth_matches:
                entities.append({
                    'type': 'ethereum',
                    'value': match,
                    'confidence': 0.95
                })
            
            # Suspicious keywords
            suspicious_keywords = ['bitcoin', 'btc', 'crypto', 'transfer', 'payment', 'urgent', 'asap']
            for keyword in suspicious_keywords:
                if keyword.lower() in text.lower():
                    entities.append({
                        'type': 'suspicious_keyword',
                        'value': keyword,
                        'confidence': 0.8
                    })
        
        return entities
    
    def _extract_call_entities(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract entities from call data."""
        entities = []
        
        # Long call detection
        duration = data.get('duration', data.get('DurationSeconds', 0))
        if isinstance(duration, (int, float)) and duration > 1800:  # 30 minutes
            entities.append({
                'type': 'long_call',
                'value': f"{duration} seconds",
                'confidence': 1.0
            })
        
        # Foreign numbers
        caller = data.get('caller', data.get('CallerNumber', ''))
        callee = data.get('callee', data.get('CalleeNumber', ''))
        
        for number in [caller, callee]:
            if number and self._is_foreign_number(number):
                entities.append({
                    'type': 'foreign_number',
                    'value': number,
                    'confidence': 1.0
                })
        
        return entities
    
    def _extract_contact_entities(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract entities from contact data."""
        entities = []
        
        # Suspicious email domains
        email = data.get('email', data.get('Email', ''))
        if email and self._is_suspicious_email(email):
            entities.append({
                'type': 'suspicious_email',
                'value': email,
                'confidence': 1.0
            })
        
        # Foreign numbers
        number = data.get('number', data.get('PhoneNumber', ''))
        if number and self._is_foreign_number(number):
            entities.append({
                'type': 'foreign_number',
                'value': number,
                'confidence': 1.0
            })
        
        return entities
    
    def _is_foreign_number(self, number: str) -> bool:
        """Check if number is foreign."""
        foreign_codes = ['+971', '+44', '+1', '+86', '+33', '+49', '+81', '+61', '+7']
        return any(number.startswith(code) for code in foreign_codes)
    
    def _is_suspicious_email(self, email: str) -> bool:
        """Check if email domain is suspicious."""
        suspicious_domains = ['protonmail.com', 'tutanota.com', 'tempmail.com', 'darkmail.pro']
        return any(domain in email.lower() for domain in suspicious_domains)
    
    def _check_cross_linking(self, event: TimelineEvent) -> bool:
        """Check if event is cross-linked with other datasets."""
        identifiers = self._extract_contact_identifiers(event.data)
        
        for identifier in identifiers:
            if identifier in self.contact_identifiers:
                # Check if this identifier appears in other datasets
                other_events = self.contact_identifiers[identifier]
                other_datasets = set()
                for other_event_id in other_events:
                    if other_event_id != event.event_id:
                        # Find the dataset of the other event
                        for other_event in self._get_all_events():
                            if other_event.event_id == other_event_id:
                                other_datasets.add(other_event.dataset)
                                break
                
                if len(other_datasets) > 0:
                    return True
        
        return False
    
    def _get_all_events(self) -> List[TimelineEvent]:
        """Get all events (used for cross-linking check)."""
        # This is a simplified version - in a real implementation,
        # you'd want to store events in the class for this lookup
        return []
    
    def _convert_to_json(self, events: List[TimelineEvent]) -> List[Dict[str, Any]]:
        """Convert timeline events to JSON format."""
        timeline_json = []
        
        for event in events:
            event_json = {
                'event_id': event.event_id,
                'event_type': event.event_type,
                'timestamp': event.timestamp.isoformat(),
                'dataset': event.dataset,
                'data': event.data,
                'linked_entities': event.linked_entities,
                'cross_linked': event.cross_linked,
                'suspicion_score': event.suspicion_score
            }
            timeline_json.append(event_json)
        
        return timeline_json


def create_demo_timeline():
    """Create a demo timeline with BTC wallet and Protonmail examples."""
    print("🚀 Creating Demo Timeline")
    print("=" * 60)
    
    # Demo data simulating query results
    demo_results = [
        # Message with BTC wallet
        {
            "dataset": "messages",
            "id": "M0008",
            "MessageID": "M0008",
            "SenderNumber": "+971468044369",
            "ReceiverNumber": "+912681177589",
            "App": "Telegram",
            "Timestamp": "2024-07-29 13:34",
            "MessageText": "Send 0.75 BTC to 3VB5INM1MjeBsrdFtCdZe11MFCIX3BYOtDj ASAP",
            "Suspicious": True,
            "Notes": "contains BTC address",
            "suspicion_score": 85
        },
        # Call by same number
        {
            "dataset": "calls",
            "id": "C0009",
            "CallID": "C0009",
            "CallerNumber": "+971468044369",
            "CalleeNumber": "+442419049663",
            "Timestamp": "2024-01-26 09:28",
            "DurationSeconds": 116,
            "Type": "Incoming",
            "Suspicious": True,
            "Notes": "Foreign or suspicious contact",
            "suspicion_score": 75
        },
        # Protonmail contact
        {
            "dataset": "contacts",
            "id": "CT002",
            "ContactID": "CT002",
            "Name": "Hxjebruzw Whqjjfgy",
            "PhoneNumber": "+911559407816",
            "Email": "hxjebruzw@protonmail.com",
            "App": "Telegram",
            "Suspicious": True,
            "Notes": "protonmail",
            "suspicion_score": 90
        },
        # Another message from Protonmail contact
        {
            "dataset": "messages",
            "id": "M0009",
            "MessageID": "M0009",
            "SenderNumber": "+915466889373",
            "ReceiverNumber": "+912681177589",
            "App": "SMS",
            "Timestamp": "2024-01-26 13:20",
            "MessageText": "Contact at 85e4e9oe94@protonmail.com for encrypted details.",
            "Suspicious": True,
            "Notes": "suspicious email domain",
            "suspicion_score": 80
        },
        # Call involving Protonmail contact
        {
            "dataset": "calls",
            "id": "C0010",
            "CallID": "C0010",
            "CallerNumber": "+911559407816",
            "CalleeNumber": "+919876543210",
            "Timestamp": "2024-01-26 14:30",
            "DurationSeconds": 300,
            "Type": "Outgoing",
            "Suspicious": False,
            "Notes": "",
            "suspicion_score": 20
        }
    ]
    
    # Build timeline
    builder = TimelineBuilder()
    timeline = builder.build_timeline(demo_results)
    
    print(f"📅 Timeline created with {len(timeline)} events")
    print("\n🔍 Timeline Events (Chronological):")
    print("-" * 60)
    
    for i, event in enumerate(timeline, 1):
        print(f"\n{i}. {event['event_type'].upper()} - {event['timestamp']}")
        print(f"   Dataset: {event['dataset']}")
        print(f"   Suspicion Score: {event['suspicion_score']}")
        print(f"   Cross-linked: {event['cross_linked']}")
        
        if event['event_type'] == 'message':
            print(f"   Text: {event['data'].get('MessageText', '')[:50]}...")
        elif event['event_type'] == 'call':
            print(f"   Call: {event['data'].get('CallerNumber', '')} → {event['data'].get('CalleeNumber', '')}")
            print(f"   Duration: {event['data'].get('DurationSeconds', 0)}s")
        elif event['event_type'] == 'contact':
            print(f"   Contact: {event['data'].get('Name', '')}")
            print(f"   Email: {event['data'].get('Email', '')}")
        
        if event['linked_entities']:
            print(f"   Entities: {[e['type'] for e in event['linked_entities']]}")
    
    # Save timeline to JSON file
    with open('/Users/sarveshragavb/Forensic/demo_timeline.json', 'w') as f:
        json.dump(timeline, f, indent=2, default=str)
    
    print(f"\n💾 Timeline saved to demo_timeline.json")
    print("\n✅ Demo timeline creation completed!")
    
    return timeline


def test_timeline_builder():
    """Test the timeline builder with sample data."""
    print("🧪 Testing Timeline Builder")
    print("=" * 60)
    
    # Test data
    test_results = [
        {
            "dataset": "messages",
            "id": 1,
            "sender": "+1234567890",
            "receiver": "+0987654321",
            "text": "Send Bitcoin to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "timestamp": "2024-01-15 10:30:00",
            "suspicion_score": 85
        },
        {
            "dataset": "calls",
            "id": 2,
            "caller": "+1234567890",
            "callee": "+0987654321",
            "timestamp": "2024-01-15 11:00:00",
            "duration": 300,
            "type": "outgoing",
            "suspicion_score": 60
        },
        {
            "dataset": "contacts",
            "id": 3,
            "name": "John Doe",
            "number": "+1234567890",
            "email": "john@protonmail.com",
            "timestamp": "2024-01-15 09:00:00",
            "suspicion_score": 70
        }
    ]
    
    # Build timeline
    builder = TimelineBuilder()
    timeline = builder.build_timeline(test_results)
    
    print(f"📊 Timeline created with {len(timeline)} events")
    
    for event in timeline:
        print(f"\nEvent: {event['event_type']} - {event['timestamp']}")
        print(f"  Cross-linked: {event['cross_linked']}")
        print(f"  Entities: {len(event['linked_entities'])}")
        print(f"  Suspicion: {event['suspicion_score']}")
    
    print("\n✅ Timeline builder testing completed!")


if __name__ == "__main__":
    test_timeline_builder()
    create_demo_timeline()