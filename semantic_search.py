#!/usr/bin/env python3
"""
Semantic Search Module for UFDR System

Provides semantic search capabilities using OpenAI embeddings and FAISS vector storage.
"""

import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import faiss
import openai
from sqlalchemy.orm import Session
from sqlalchemy import text

from models import init_db, Message, Call, Contact, Entity


@dataclass
class SearchResult:
    """Search result container."""
    id: int
    dataset: str
    text: str
    score: float
    metadata: Dict[str, Any]


class UFDRSemanticSearch:
    """
    Semantic search engine for UFDR forensic data.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, index_path: str = "ufdr_embeddings.faiss"):
        """
        Initialize the semantic search engine.
        
        Args:
            openai_api_key: OpenAI API key (if None, will try to get from environment)
            index_path: Path to store FAISS index
        """
        self.index_path = Path(index_path)
        self.metadata_path = self.index_path.with_suffix('.metadata')
        
        # Initialize OpenAI client
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass openai_api_key parameter.")
        
        self.client = openai.OpenAI(api_key=api_key)
        
        # Initialize FAISS index
        self.index = None
        self.metadata = []
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create new one."""
        if self.index_path.exists() and self.metadata_path.exists():
            print("Loading existing FAISS index...")
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            print(f"Loaded index with {self.index.ntotal} vectors")
        else:
            print("Creating new FAISS index...")
            # Create index with 1536 dimensions (text-embedding-3-small)
            self.index = faiss.IndexFlatIP(1536)  # Inner product for cosine similarity
            self.metadata = []
    
    def _save_index(self):
        """Save FAISS index and metadata."""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        print(f"Saved index with {self.index.ntotal} vectors")
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using OpenAI API."""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return np.zeros(1536, dtype=np.float32)
    
    def _prepare_text_for_embedding(self, dataset: str, record: Dict[str, Any]) -> str:
        """
        Prepare text for embedding based on dataset type.
        
        Args:
            dataset: Type of dataset (messages, calls, contacts, entities)
            record: Record data dictionary
            
        Returns:
            str: Prepared text for embedding
        """
        if dataset == "messages":
            return f"Message from {record.get('sender', '')} to {record.get('receiver', '')} via {record.get('app', '')}: {record.get('text', '')}"
        
        elif dataset == "calls":
            duration_min = record.get('duration', 0) // 60 if record.get('duration') else 0
            return f"Call from {record.get('caller', '')} to {record.get('callee', '')} ({record.get('type', '')}) lasting {duration_min} minutes"
        
        elif dataset == "contacts":
            return f"Contact: {record.get('name', '')} - {record.get('number', '')} - {record.get('email', '')} ({record.get('app', '')})"
        
        elif dataset == "entities":
            return f"Entity: {record.get('type', '')} - {record.get('value', '')} (confidence: {record.get('confidence', 0)})"
        
        else:
            return str(record)
    
    def build_embeddings(self, session: Session) -> int:
        """
        Build embeddings for all records in the database.
        
        Args:
            session: SQLAlchemy session
            
        Returns:
            int: Number of embeddings created
        """
        print("Building embeddings for all UFDR data...")
        
        total_embeddings = 0
        
        # Process messages
        print("Processing messages...")
        messages = session.query(Message).all()
        for msg in messages:
            text = self._prepare_text_for_embedding("messages", {
                'sender': msg.sender,
                'receiver': msg.receiver,
                'app': msg.app,
                'text': msg.text or ''
            })
            embedding = self._get_embedding(text)
            self.index.add(embedding.reshape(1, -1))
            self.metadata.append({
                'id': msg.id,
                'dataset': 'messages',
                'text': text,
                'original_data': {
                    'sender': msg.sender,
                    'receiver': msg.receiver,
                    'app': msg.app,
                    'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
                    'text': msg.text
                }
            })
            total_embeddings += 1
        
        # Process calls
        print("Processing calls...")
        calls = session.query(Call).all()
        for call in calls:
            text = self._prepare_text_for_embedding("calls", {
                'caller': call.caller,
                'callee': call.callee,
                'type': call.type,
                'duration': call.duration
            })
            embedding = self._get_embedding(text)
            self.index.add(embedding.reshape(1, -1))
            self.metadata.append({
                'id': call.id,
                'dataset': 'calls',
                'text': text,
                'original_data': {
                    'caller': call.caller,
                    'callee': call.callee,
                    'type': call.type,
                    'timestamp': call.timestamp.isoformat() if call.timestamp else None,
                    'duration': call.duration
                }
            })
            total_embeddings += 1
        
        # Process contacts
        print("Processing contacts...")
        contacts = session.query(Contact).all()
        for contact in contacts:
            text = self._prepare_text_for_embedding("contacts", {
                'name': contact.name or '',
                'number': contact.number or '',
                'email': contact.email or '',
                'app': contact.app
            })
            embedding = self._get_embedding(text)
            self.index.add(embedding.reshape(1, -1))
            self.metadata.append({
                'id': contact.id,
                'dataset': 'contacts',
                'text': text,
                'original_data': {
                    'name': contact.name,
                    'number': contact.number,
                    'email': contact.email,
                    'app': contact.app
                }
            })
            total_embeddings += 1
        
        # Process entities
        print("Processing entities...")
        entities = session.query(Entity).all()
        for entity in entities:
            text = self._prepare_text_for_embedding("entities", {
                'type': entity.type,
                'value': entity.value,
                'confidence': entity.confidence
            })
            embedding = self._get_embedding(text)
            self.index.add(embedding.reshape(1, -1))
            self.metadata.append({
                'id': entity.id,
                'dataset': 'entities',
                'text': text,
                'original_data': {
                    'type': entity.type,
                    'value': entity.value,
                    'confidence': entity.confidence,
                    'linked_message_id': entity.linked_message_id,
                    'linked_call_id': entity.linked_call_id
                }
            })
            total_embeddings += 1
        
        # Save index
        self._save_index()
        
        print(f"Built {total_embeddings} embeddings successfully!")
        return total_embeddings
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        Perform semantic search on the indexed data.
        
        Args:
            query: Search query string
            top_k: Number of top results to return
            
        Returns:
            List[SearchResult]: List of search results
        """
        if self.index.ntotal == 0:
            print("No embeddings found. Run build_embeddings() first.")
            return []
        
        # Get embedding for query
        query_embedding = self._get_embedding(query)
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding.reshape(1, -1), top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.metadata):
                metadata = self.metadata[idx]
                result = SearchResult(
                    id=metadata['id'],
                    dataset=metadata['dataset'],
                    text=metadata['text'],
                    score=float(score),
                    metadata=metadata['original_data']
                )
                results.append(result)
        
        return results
    
    def search_crypto_wallets(self) -> List[SearchResult]:
        """Search for crypto wallet related content."""
        return self.semantic_search("crypto wallets bitcoin ethereum blockchain", top_k=10)
    
    def search_suspicious_communications(self) -> List[SearchResult]:
        """Search for suspicious communication patterns."""
        return self.semantic_search("suspicious communication fraud money transfer", top_k=10)
    
    def search_international_calls(self) -> List[SearchResult]:
        """Search for international call patterns."""
        return self.semantic_search("international calls foreign numbers", top_k=10)


def demo_semantic_search():
    """Demo function for semantic search capabilities."""
    print("🔍 UFDR Semantic Search Demo")
    print("=" * 50)
    
    # Initialize database
    engine, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    try:
        # Initialize semantic search
        search_engine = UFDRSemanticSearch()
        
        # Build embeddings if not already built
        if search_engine.index.ntotal == 0:
            print("Building embeddings...")
            search_engine.build_embeddings(session)
        else:
            print(f"Using existing embeddings ({search_engine.index.ntotal} vectors)")
        
        # Demo 1: Search for crypto wallets
        print("\n💰 Searching for crypto wallets...")
        crypto_results = search_engine.search_crypto_wallets()
        
        print(f"Found {len(crypto_results)} crypto-related results:")
        for i, result in enumerate(crypto_results[:5], 1):
            print(f"  {i}. [{result.dataset}] Score: {result.score:.3f}")
            print(f"     {result.text[:100]}...")
            if result.metadata:
                print(f"     Metadata: {result.metadata}")
            print()
        
        # Demo 2: Search for suspicious communications
        print("\n🚨 Searching for suspicious communications...")
        suspicious_results = search_engine.semantic_search("suspicious communication fraud", top_k=5)
        
        print(f"Found {len(suspicious_results)} suspicious results:")
        for i, result in enumerate(suspicious_results, 1):
            print(f"  {i}. [{result.dataset}] Score: {result.score:.3f}")
            print(f"     {result.text[:100]}...")
            print()
        
        # Demo 3: Search for international calls
        print("\n🌍 Searching for international calls...")
        international_results = search_engine.semantic_search("international calls foreign numbers", top_k=5)
        
        print(f"Found {len(international_results)} international results:")
        for i, result in enumerate(international_results, 1):
            print(f"  {i}. [{result.dataset}] Score: {result.score:.3f}")
            print(f"     {result.text[:100]}...")
            print()
        
        print("✅ Semantic search demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("Make sure you have set the OPENAI_API_KEY environment variable")
    finally:
        session.close()


if __name__ == "__main__":
    demo_semantic_search()
