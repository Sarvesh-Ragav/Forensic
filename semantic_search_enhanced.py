#!/usr/bin/env python3
"""
Enhanced Semantic Search Module for UFDR System

Provides semantic search with OpenAI embeddings (primary) and 
sentence-transformers fallback (offline).
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

import faiss
from sqlalchemy.orm import Session

from models import init_db, Message, Call, Contact, Entity


@dataclass
class SearchResult:
    """Search result container."""
    id: int
    dataset: str
    text: str
    score: float
    metadata: Dict[str, Any]


class UFDRSemanticSearchEnhanced:
    """
    Enhanced semantic search engine with OpenAI and sentence-transformers fallback.
    """
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None, 
                 index_path: str = "ufdr_embeddings.faiss",
                 use_local: bool = False):
        """
        Initialize the semantic search engine.
        
        Args:
            openai_api_key: OpenAI API key (if None, will try environment)
            index_path: Path to store FAISS index
            use_local: Force use of local sentence-transformers
        """
        self.index_path = Path(index_path)
        self.metadata_path = self.index_path.with_suffix('.metadata')
        self.use_local = use_local
        
        # Initialize embedding provider
        self._init_embedding_provider(openai_api_key)
        
        # Initialize FAISS index
        self.index = None
        self.metadata = []
        self._load_or_create_index()
    
    def _init_embedding_provider(self, openai_api_key: Optional[str] = None):
        """Initialize embedding provider (OpenAI or sentence-transformers)."""
        if not self.use_local:
            # Try OpenAI first
            try:
                import openai
                api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
                if api_key:
                    self.client = openai.OpenAI(api_key=api_key)
                    self.embedding_dim = 1536  # text-embedding-3-small
                    self.provider = "openai"
                    print("✅ Using OpenAI embeddings (text-embedding-3-small)")
                    return
            except Exception as e:
                print(f"⚠️  OpenAI not available: {e}")
        
        # Fallback to sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dim = 384  # all-MiniLM-L6-v2
            self.provider = "local"
            print("✅ Using sentence-transformers (all-MiniLM-L6-v2) - OFFLINE MODE")
        except Exception as e:
            raise RuntimeError(f"Could not initialize any embedding provider: {e}")
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create new one."""
        if self.index_path.exists() and self.metadata_path.exists():
            print("📂 Loading existing FAISS index...")
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            print(f"✅ Loaded index with {self.index.ntotal} vectors")
        else:
            print("🔨 Creating new FAISS index...")
            # Create index with appropriate dimensions
            self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
            self.metadata = []
    
    def _save_index(self):
        """Save FAISS index and metadata."""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        print(f"💾 Saved index with {self.index.ntotal} vectors")
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using configured provider."""
        if self.provider == "openai":
            try:
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                embedding = np.array(response.data[0].embedding, dtype=np.float32)
                # Normalize for cosine similarity
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                return embedding
            except Exception as e:
                print(f"⚠️  Error getting OpenAI embedding: {e}")
                return np.zeros(self.embedding_dim, dtype=np.float32)
        else:  # local
            embedding = self.model.encode(text, convert_to_numpy=True)
            embedding = embedding.astype(np.float32)
            # Normalize for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            return embedding
    
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
            return f"Contact: {record.get('name', '')} {record.get('number', '')} {record.get('email', '')} {record.get('app', '')}"
        
        elif dataset == "entities":
            return f"Entity: {record.get('type', '')} {record.get('value', '')} confidence {record.get('confidence', 0)}"
        
        else:
            return str(record)
    
    def build_embeddings(self, session: Session, batch_size: int = 50) -> int:
        """
        Build embeddings for all records in the database.
        
        Args:
            session: SQLAlchemy session
            batch_size: Number of records to process at once
            
        Returns:
            int: Number of embeddings created
        """
        print("🚀 Building embeddings for all UFDR data...")
        print(f"   Provider: {self.provider}")
        print(f"   Embedding dimension: {self.embedding_dim}")
        
        total_embeddings = 0
        
        # Process messages
        print("\n📱 Processing messages...")
        messages = session.query(Message).all()
        for i, msg in enumerate(messages):
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
            if (i + 1) % batch_size == 0:
                print(f"   Processed {i + 1}/{len(messages)} messages")
        print(f"   ✅ Completed {len(messages)} messages")
        
        # Process calls
        print("\n📞 Processing calls...")
        calls = session.query(Call).all()
        for i, call in enumerate(calls):
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
            if (i + 1) % batch_size == 0:
                print(f"   Processed {i + 1}/{len(calls)} calls")
        print(f"   ✅ Completed {len(calls)} calls")
        
        # Process contacts
        print("\n👥 Processing contacts...")
        contacts = session.query(Contact).all()
        for i, contact in enumerate(contacts):
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
            if (i + 1) % batch_size == 0:
                print(f"   Processed {i + 1}/{len(contacts)} contacts")
        print(f"   ✅ Completed {len(contacts)} contacts")
        
        # Process entities
        print("\n🔍 Processing entities...")
        entities = session.query(Entity).all()
        for i, entity in enumerate(entities):
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
            if (i + 1) % batch_size == 0:
                print(f"   Processed {i + 1}/{len(entities)} entities")
        print(f"   ✅ Completed {len(entities)} entities")
        
        # Save index
        self._save_index()
        
        print(f"\n✅ Built {total_embeddings} embeddings successfully!")
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
            print("⚠️  No embeddings found. Run build_embeddings() first.")
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


def demo_enhanced_semantic_search():
    """Demo function for enhanced semantic search."""
    print("🔍 UFDR Enhanced Semantic Search Demo")
    print("=" * 60)
    
    # Initialize database
    engine, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    try:
        # Initialize semantic search (will auto-detect OpenAI or fallback to local)
        search_engine = UFDRSemanticSearchEnhanced(use_local=True)  # Force local for demo
        
        # Build embeddings if not already built
        if search_engine.index.ntotal == 0:
            print("🔨 Building embeddings...")
            search_engine.build_embeddings(session)
        else:
            print(f"📂 Using existing embeddings ({search_engine.index.ntotal} vectors)")
        
        # Demo: Search for crypto wallets
        print("\n" + "=" * 60)
        print("💰 Query: 'Find crypto wallets'")
        print("=" * 60)
        
        results = search_engine.semantic_search("Find crypto wallets", top_k=5)
        
        print(f"\n📊 Found {len(results)} matches:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. [{result.dataset.upper()}] Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
            if result.metadata:
                print(f"   Metadata: {result.metadata}")
            print()
        
        # Additional searches
        print("=" * 60)
        print("🚨 Query: 'suspicious communication'")
        print("=" * 60)
        
        results = search_engine.semantic_search("suspicious communication", top_k=3)
        
        print(f"\n📊 Found {len(results)} matches:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. [{result.dataset.upper()}] Score: {result.score:.4f}")
            print(f"   Text: {result.text[:100]}...")
            print()
        
        print("✅ Enhanced semantic search demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    demo_enhanced_semantic_search()
