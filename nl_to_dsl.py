#!/usr/bin/env python3
"""
Natural Language to DSL Translator for UFDR Forensic System

Converts natural language queries into structured DSL objects for forensic analysis.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from dsl_query_tester import run_dsl_query
from semantic_search_enhanced import UFDRSemanticSearchEnhanced

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DSLQuery:
    """Structured DSL query object."""
    dataset: str
    filters: List[Dict[str, Any]]
    limit: int = 20
    sort: Optional[List[Dict[str, str]]] = None


class NLToDSLTranslator:
    """
    Natural Language to DSL translator for UFDR forensic queries.
    """
    
    def __init__(self):
        """Initialize the translator with pattern definitions."""
        self.patterns = self._initialize_patterns()
        self.semantic_search = None
    
    def _initialize_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize query patterns and mappings."""
        return {
            # Dataset mappings
            'datasets': {
                'chats': 'messages',
                'messages': 'messages', 
                'calls': 'calls',
                'contacts': 'contacts',
                'entities': 'entities'
            },
            
            # Keyword patterns
            'keywords': {
                'crypto': ['crypto', 'cryptocurrency', 'bitcoin', 'btc', 'ethereum', 'eth', 'wallet'],
                'email': ['email', 'mail', 'protonmail', 'gmail', 'outlook'],
                'suspicious': ['suspicious', 'fraud', 'scam', 'illegal', 'criminal'],
                'international': ['international', 'foreign', 'overseas', 'global'],
                'encrypted': ['encrypted', 'secure', 'private', 'confidential']
            },
            
            # Number patterns
            'number_patterns': {
                'uae': r'\+971\d{7,9}',
                'uk': r'\+44\d{9,10}',
                'us': r'\+1\d{10}',
                'foreign': r'\+\d{10,15}'
            },
            
            # Duration patterns
            'duration_patterns': {
                r'longer than (\d+) minutes?': '>',
                r'more than (\d+) minutes?': '>',
                r'over (\d+) minutes?': '>',
                r'less than (\d+) minutes?': '<',
                r'shorter than (\d+) minutes?': '<',
                r'under (\d+) minutes?': '<',
                r'exactly (\d+) minutes?': '=',
                r'(\d+) minutes? or more': '>=',
                r'at least (\d+) minutes?': '>='
            },
            
            # Date patterns
            'date_patterns': {
                r'in (\w+) (\d{4})': 'month_year',
                r'during (\w+) (\d{4})': 'month_year',
                r'since (\w+) (\d{4})': 'since_month_year',
                r'from (\w+) (\d{4})': 'from_month_year',
                r'after (\w+) (\d{4})': 'after_month_year',
                r'before (\w+) (\d{4})': 'before_month_year'
            },
            
            # App patterns
            'app_patterns': {
                'whatsapp': ['whatsapp', 'wa'],
                'telegram': ['telegram', 'tg'],
                'signal': ['signal'],
                'sms': ['sms', 'text', 'message']
            }
        }
    
    def translate(self, query: str, use_semantic_fallback: bool = True) -> Tuple[DSLQuery, bool]:
        """
        Translate natural language query to DSL.
        
        Args:
            query: Natural language query string
            use_semantic_fallback: Whether to use semantic search as fallback
            
        Returns:
            Tuple[DSLQuery, bool]: (DSL query object, success flag)
        """
        logger.info(f"Translating query: '{query}'")
        
        # Normalize query
        normalized_query = self._normalize_query(query)
        
        # Extract dataset
        dataset = self._extract_dataset(normalized_query)
        if not dataset:
            if use_semantic_fallback:
                logger.info("No dataset found, using semantic search fallback")
                return self._semantic_fallback(query)
            return None, False
        
        # Extract filters
        filters = self._extract_filters(normalized_query, dataset)
        
        # Extract limit
        limit = self._extract_limit(normalized_query)
        
        # Extract sort
        sort = self._extract_sort(normalized_query)
        
        # Create DSL query
        dsl_query = DSLQuery(
            dataset=dataset,
            filters=filters,
            limit=limit,
            sort=sort
        )
        
        logger.info(f"Translated to DSL: {dsl_query}")
        return dsl_query, True
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for processing."""
        return query.lower().strip()
    
    def _extract_dataset(self, query: str) -> Optional[str]:
        """Extract dataset from query."""
        datasets = self.patterns['datasets']
        
        for keyword, dataset in datasets.items():
            if keyword in query:
                return dataset
        
        # Default to messages if no specific dataset mentioned
        if any(word in query for word in ['chat', 'message', 'text', 'conversation']):
            return 'messages'
        
        return None
    
    def _extract_filters(self, query: str, dataset: str) -> List[Dict[str, Any]]:
        """Extract filters from query."""
        filters = []
        
        # Keyword filters
        filters.extend(self._extract_keyword_filters(query, dataset))
        
        # Number pattern filters
        filters.extend(self._extract_number_filters(query, dataset))
        
        # Duration filters
        filters.extend(self._extract_duration_filters(query, dataset))
        
        # Date filters
        filters.extend(self._extract_date_filters(query, dataset))
        
        # App filters
        filters.extend(self._extract_app_filters(query, dataset))
        
        return filters
    
    def _extract_keyword_filters(self, query: str, dataset: str) -> List[Dict[str, Any]]:
        """Extract keyword-based filters."""
        filters = []
        keywords = self.patterns['keywords']
        
        for category, words in keywords.items():
            for word in words:
                if word in query:
                    if category == 'crypto' and dataset == 'entities':
                        filters.append({
                            'field': 'type',
                            'op': 'in',
                            'value': ['bitcoin', 'ethereum', 'crypto']
                        })
                    elif category == 'email' and dataset == 'entities':
                        filters.append({
                            'field': 'type',
                            'op': '=',
                            'value': 'email'
                        })
                    elif category == 'email' and dataset == 'messages':
                        filters.append({
                            'field': 'text',
                            'op': 'contains',
                            'value': 'protonmail'
                        })
                    elif category == 'suspicious' and dataset == 'entities':
                        filters.append({
                            'field': 'type',
                            'op': '=',
                            'value': 'suspicious'
                        })
                    break
        
        # Special handling for Protonmail in contacts
        if 'protonmail' in query and dataset == 'contacts':
            filters.append({
                'field': 'email',
                'op': 'contains',
                'value': 'protonmail'
            })
        
        return filters
    
    def _extract_number_filters(self, query: str, dataset: str) -> List[Dict[str, Any]]:
        """Extract number pattern filters."""
        filters = []
        number_patterns = self.patterns['number_patterns']
        
        for pattern_name, pattern in number_patterns.items():
            if pattern_name in query or re.search(pattern, query):
                if dataset == 'messages':
                    filters.append({
                        'field': 'sender',
                        'op': 'contains',
                        'value': '+971'
                    })
                    filters.append({
                        'field': 'receiver',
                        'op': 'contains',
                        'value': '+971'
                    })
                elif dataset == 'calls':
                    filters.append({
                        'field': 'caller',
                        'op': 'contains',
                        'value': '+971'
                    })
                    filters.append({
                        'field': 'callee',
                        'op': 'contains',
                        'value': '+971'
                    })
                elif dataset == 'contacts':
                    filters.append({
                        'field': 'number',
                        'op': 'contains',
                        'value': '+971'
                    })
        
        return filters
    
    def _extract_duration_filters(self, query: str, dataset: str) -> List[Dict[str, Any]]:
        """Extract duration-based filters."""
        filters = []
        duration_patterns = self.patterns['duration_patterns']
        
        if dataset == 'calls':
            for pattern, operator in duration_patterns.items():
                match = re.search(pattern, query)
                if match:
                    duration_minutes = int(match.group(1))
                    duration_seconds = duration_minutes * 60
                    
                    filters.append({
                        'field': 'duration',
                        'op': operator,
                        'value': duration_seconds
                    })
                    break
        
        return filters
    
    def _extract_date_filters(self, query: str, dataset: str) -> List[Dict[str, Any]]:
        """Extract date-based filters."""
        filters = []
        date_patterns = self.patterns['date_patterns']
        
        for pattern, pattern_type in date_patterns.items():
            match = re.search(pattern, query)
            if match:
                month = match.group(1)
                year = int(match.group(2))
                
                # Convert month name to number
                month_map = {
                    'january': 1, 'jan': 1, 'february': 2, 'feb': 2,
                    'march': 3, 'mar': 3, 'april': 4, 'apr': 4,
                    'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
                    'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
                    'october': 10, 'oct': 10, 'november': 11, 'nov': 11,
                    'december': 12, 'dec': 12
                }
                
                month_num = month_map.get(month.lower(), 1)
                
                if pattern_type == 'month_year':
                    start_date = f"{year}-{month_num:02d}-01"
                    if month_num == 12:
                        end_date = f"{year + 1}-01-01"
                    else:
                        end_date = f"{year}-{month_num + 1:02d}-01"
                    
                    filters.append({
                        'field': 'timestamp',
                        'op': 'between',
                        'value': [start_date, end_date]
                    })
                elif pattern_type == 'since_month_year':
                    start_date = f"{year}-{month_num:02d}-01"
                    filters.append({
                        'field': 'timestamp',
                        'op': '>=',
                        'value': start_date
                    })
        
        return filters
    
    def _extract_app_filters(self, query: str, dataset: str) -> List[Dict[str, Any]]:
        """Extract app-based filters."""
        filters = []
        app_patterns = self.patterns['app_patterns']
        
        if dataset == 'messages':
            for app_name, keywords in app_patterns.items():
                for keyword in keywords:
                    if keyword in query:
                        filters.append({
                            'field': 'app',
                            'op': '=',
                            'value': app_name.title()
                        })
                        break
        
        return filters
    
    def _extract_limit(self, query: str) -> int:
        """Extract limit from query."""
        # Look for explicit limit
        limit_match = re.search(r'(?:limit|show|display|get)\s+(\d+)', query)
        if limit_match:
            return int(limit_match.group(1))
        
        # Look for "all" or "everything"
        if 'all' in query or 'everything' in query:
            return 1000
        
        # Default limit
        return 20
    
    def _extract_sort(self, query: str) -> Optional[List[Dict[str, str]]]:
        """Extract sort preferences from query."""
        sort = []
        
        if 'newest' in query or 'recent' in query:
            sort.append({'field': 'timestamp', 'direction': 'desc'})
        elif 'oldest' in query:
            sort.append({'field': 'timestamp', 'direction': 'asc'})
        elif 'longest' in query and 'call' in query:
            sort.append({'field': 'duration', 'direction': 'desc'})
        elif 'shortest' in query and 'call' in query:
            sort.append({'field': 'duration', 'direction': 'asc'})
        
        return sort if sort else None
    
    def _semantic_fallback(self, query: str) -> Tuple[DSLQuery, bool]:
        """Use semantic search as fallback."""
        logger.info("Using semantic search fallback")
        
        # Initialize semantic search if not already done
        if not self.semantic_search:
            try:
                self.semantic_search = UFDRSemanticSearchEnhanced(use_local=True)
            except Exception as e:
                logger.error(f"Failed to initialize semantic search: {e}")
                return None, False
        
        # Create a generic DSL query that will use semantic search
        dsl_query = DSLQuery(
            dataset='messages',  # Default dataset
            filters=[{
                'field': 'text',
                'op': 'semantic_search',
                'value': query
            }],
            limit=20
        )
        
        return dsl_query, True
    
    def execute_query(self, query: str, session) -> List[Dict[str, Any]]:
        """
        Execute natural language query and return results.
        
        Args:
            query: Natural language query
            session: SQLAlchemy session
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        # Translate to DSL
        dsl_query, success = self.translate(query)
        
        if not success or not dsl_query:
            logger.error("Failed to translate query to DSL")
            return []
        
        # Check if semantic search fallback is needed
        if dsl_query.filters and any(f.get('op') == 'semantic_search' for f in dsl_query.filters):
            return self._execute_semantic_search(query, session)
        
        # Execute DSL query
        try:
            dsl_dict = {
                'dataset': dsl_query.dataset,
                'filters': dsl_query.filters,
                'limit': dsl_query.limit
            }
            if dsl_query.sort:
                dsl_dict['sort'] = dsl_query.sort
            
            results = run_dsl_query(dsl_dict, session)
            return results
        
        except Exception as e:
            logger.error(f"Failed to execute DSL query: {e}")
            return self._execute_semantic_search(query, session)
    
    def _execute_semantic_search(self, query: str, session) -> List[Dict[str, Any]]:
        """Execute semantic search fallback."""
        try:
            if not self.semantic_search:
                self.semantic_search = UFDRSemanticSearchEnhanced(use_local=True)
            
            results = self.semantic_search.semantic_search(query, top_k=20)
            
            # Convert to dict format
            return [{
                'id': r.id,
                'dataset': r.dataset,
                'text': r.text,
                'score': r.score,
                'metadata': r.metadata
            } for r in results]
        
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []


def test_nl_to_dsl():
    """Test the NL to DSL translator with example queries."""
    print("🧪 Testing Natural Language to DSL Translator")
    print("=" * 60)
    
    translator = NLToDSLTranslator()
    
    # Test queries
    test_queries = [
        "Find calls longer than 30 minutes",
        "Show me WhatsApp chats with UAE numbers", 
        "List all contacts with Protonmail accounts",
        "Show me all Bitcoin addresses",
        "Find messages from January 2024",
        "Display suspicious entities",
        "Get all international calls",
        "Show recent messages"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        dsl_query, success = translator.translate(query)
        
        if success and dsl_query:
            print(f"✅ Dataset: {dsl_query.dataset}")
            print(f"   Filters: {dsl_query.filters}")
            print(f"   Limit: {dsl_query.limit}")
            if dsl_query.sort:
                print(f"   Sort: {dsl_query.sort}")
        else:
            print("❌ Translation failed")
    
    print("\n✅ NL to DSL translator testing completed!")


def demo_nl_to_dsl():
    """Demo the complete NL to DSL pipeline."""
    print("🚀 Natural Language to DSL Demo")
    print("=" * 60)
    
    # Initialize database
    from models import init_db
    engine, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    try:
        # Initialize translator
        translator = NLToDSLTranslator()
        
        # Demo queries
        demo_queries = [
            "Find calls longer than 30 minutes",
            "Show me WhatsApp chats with UAE numbers",
            "List all contacts with Protonmail accounts"
        ]
        
        for query in demo_queries:
            print(f"\n" + "=" * 60)
            print(f"🔍 Query: '{query}'")
            print("=" * 60)
            
            # Execute query
            results = translator.execute_query(query, session)
            
            print(f"📊 Found {len(results)} results:")
            for i, result in enumerate(results[:5], 1):  # Show top 5
                print(f"  {i}. {result}")
            
            if len(results) > 5:
                print(f"  ... and {len(results) - 5} more results")
        
        print("\n✅ NL to DSL demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    test_nl_to_dsl()
    print("\n" + "=" * 60)
    demo_nl_to_dsl()
