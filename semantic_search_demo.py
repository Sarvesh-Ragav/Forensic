#!/usr/bin/env python3
"""
Semantic Search Demo for UFDR System

This demo shows how to use the semantic search capabilities without requiring
an OpenAI API key by using mock embeddings for demonstration.
"""

import os
import numpy as np
from typing import List, Dict, Any
from models import init_db, Message, Call, Contact, Entity


class MockSemanticSearch:
    """
    Mock semantic search for demonstration purposes.
    Uses simple text matching instead of real embeddings.
    """
    
    def __init__(self):
        self.index = {}
        self.metadata = []
    
    def build_embeddings(self, session) -> int:
        """Build mock embeddings for demonstration."""
        print("Building mock embeddings for demonstration...")
        
        total_embeddings = 0
        
        # Process messages
        print("Processing messages...")
        messages = session.query(Message).all()
        for msg in messages:
            text = f"Message from {msg.sender} to {msg.receiver} via {msg.app}: {msg.text or ''}"
            self.index[text] = {
                'id': msg.id,
                'dataset': 'messages',
                'text': text,
                'metadata': {
                    'sender': msg.sender,
                    'receiver': msg.receiver,
                    'app': msg.app,
                    'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
                    'text': msg.text
                }
            }
            total_embeddings += 1
        
        # Process calls
        print("Processing calls...")
        calls = session.query(Call).all()
        for call in calls:
            duration_min = call.duration // 60 if call.duration else 0
            text = f"Call from {call.caller} to {call.callee} ({call.type}) lasting {duration_min} minutes"
            self.index[text] = {
                'id': call.id,
                'dataset': 'calls',
                'text': text,
                'metadata': {
                    'caller': call.caller,
                    'callee': call.callee,
                    'type': call.type,
                    'timestamp': call.timestamp.isoformat() if call.timestamp else None,
                    'duration': call.duration
                }
            }
            total_embeddings += 1
        
        # Process contacts
        print("Processing contacts...")
        contacts = session.query(Contact).all()
        for contact in contacts:
            text = f"Contact: {contact.name or ''} - {contact.number or ''} - {contact.email or ''} ({contact.app})"
            self.index[text] = {
                'id': contact.id,
                'dataset': 'contacts',
                'text': text,
                'metadata': {
                    'name': contact.name,
                    'number': contact.number,
                    'email': contact.email,
                    'app': contact.app
                }
            }
            total_embeddings += 1
        
        # Process entities
        print("Processing entities...")
        entities = session.query(Entity).all()
        for entity in entities:
            text = f"Entity: {entity.type} - {entity.value} (confidence: {entity.confidence})"
            self.index[text] = {
                'id': entity.id,
                'dataset': 'entities',
                'text': text,
                'metadata': {
                    'type': entity.type,
                    'value': entity.value,
                    'confidence': entity.confidence,
                    'linked_message_id': entity.linked_message_id,
                    'linked_call_id': entity.linked_call_id
                }
            }
            total_embeddings += 1
        
        print(f"Built {total_embeddings} mock embeddings successfully!")
        return total_embeddings
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform mock semantic search using text matching."""
        if not self.index:
            print("No embeddings found. Run build_embeddings() first.")
            return []
        
        results = []
        query_lower = query.lower()
        
        # Simple text matching for demonstration
        for text, data in self.index.items():
            score = 0
            text_lower = text.lower()
            
            # Calculate simple relevance score
            for word in query_lower.split():
                if word in text_lower:
                    score += 1
            
            if score > 0:
                results.append({
                    'id': data['id'],
                    'dataset': data['dataset'],
                    'text': data['text'],
                    'score': score,
                    'metadata': data['metadata']
                })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def search_crypto_wallets(self) -> List[Dict[str, Any]]:
        """Search for crypto wallet related content."""
        return self.semantic_search("crypto wallets bitcoin ethereum blockchain", top_k=10)
    
    def search_suspicious_communications(self) -> List[Dict[str, Any]]:
        """Search for suspicious communication patterns."""
        return self.semantic_search("suspicious communication fraud money transfer", top_k=10)
    
    def search_international_calls(self) -> List[Dict[str, Any]]:
        """Search for international call patterns."""
        return self.semantic_search("international calls foreign numbers", top_k=10)


def demo_semantic_search():
    """Demo function for semantic search capabilities."""
    print("🔍 UFDR Semantic Search Demo (Mock Version)")
    print("=" * 60)
    print("Note: This is a mock demonstration using text matching.")
    print("For real semantic search, set OPENAI_API_KEY and use semantic_search.py")
    print()
    
    # Initialize database
    engine, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    try:
        # Initialize mock semantic search
        search_engine = MockSemanticSearch()
        
        # Build mock embeddings
        print("Building mock embeddings...")
        search_engine.build_embeddings(session)
        
        # Demo 1: Search for crypto wallets
        print("\n💰 Searching for crypto wallets...")
        crypto_results = search_engine.search_crypto_wallets()
        
        print(f"Found {len(crypto_results)} crypto-related results:")
        for i, result in enumerate(crypto_results[:5], 1):
            print(f"  {i}. [{result['dataset']}] Score: {result['score']}")
            print(f"     {result['text'][:100]}...")
            if result['metadata']:
                print(f"     Metadata: {result['metadata']}")
            print()
        
        # Demo 2: Search for suspicious communications
        print("\n🚨 Searching for suspicious communications...")
        suspicious_results = search_engine.semantic_search("suspicious communication fraud", top_k=5)
        
        print(f"Found {len(suspicious_results)} suspicious results:")
        for i, result in enumerate(suspicious_results, 1):
            print(f"  {i}. [{result['dataset']}] Score: {result['score']}")
            print(f"     {result['text'][:100]}...")
            print()
        
        # Demo 3: Search for international calls
        print("\n🌍 Searching for international calls...")
        international_results = search_engine.semantic_search("international calls foreign numbers", top_k=5)
        
        print(f"Found {len(international_results)} international results:")
        for i, result in enumerate(international_results, 1):
            print(f"  {i}. [{result['dataset']}] Score: {result['score']}")
            print(f"     {result['text'][:100]}...")
            print()
        
        # Demo 4: Search for specific crypto terms
        print("\n🔍 Searching for 'find crypto wallets'...")
        crypto_search_results = search_engine.semantic_search("find crypto wallets", top_k=5)
        
        print(f"Found {len(crypto_search_results)} results for 'find crypto wallets':")
        for i, result in enumerate(crypto_search_results, 1):
            print(f"  {i}. [{result['dataset']}] Score: {result['score']}")
            print(f"     {result['text'][:100]}...")
            print()
        
        print("✅ Mock semantic search demo completed!")
        print("\n💡 To use real semantic search with OpenAI embeddings:")
        print("   1. Set OPENAI_API_KEY environment variable")
        print("   2. Run: python semantic_search.py")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    demo_semantic_search()
