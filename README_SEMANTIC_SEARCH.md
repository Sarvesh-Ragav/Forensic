# UFDR Semantic Search System

## 🔍 **Overview**

The UFDR Semantic Search system provides advanced search capabilities using OpenAI embeddings and FAISS vector storage. It enables natural language queries across all forensic data types (messages, calls, contacts, entities) with semantic understanding.

## 🏗️ **Architecture**

### **Components**
- **OpenAI Embeddings**: `text-embedding-3-small` for fast, accurate embeddings
- **FAISS Vector Storage**: Local vector database for efficient similarity search
- **SQLAlchemy Integration**: Seamless integration with existing UFDR database
- **Metadata Mapping**: Links embeddings to original records with full context

### **Data Processing**
- **Messages**: `sender + receiver + app + text`
- **Calls**: `caller + callee + type + duration`
- **Contacts**: `name + number + email + app`
- **Entities**: `type + value + confidence`

## 🚀 **Quick Start**

### **1. Install Dependencies**
```bash
cd /Users/sarveshragavb/Forensic
source venv/bin/activate
pip install openai faiss-cpu numpy
```

### **2. Set OpenAI API Key**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### **3. Run Semantic Search**
```bash
python semantic_search.py
```

## 📊 **Demo Results**

**Mock Demo (No API Key Required):**
```bash
python semantic_search_demo.py
```

**Results from Real Data:**
- ✅ **180 embeddings** built successfully
- ✅ **Crypto wallets found**: Bitcoin addresses, Ethereum addresses
- ✅ **Suspicious communications**: Protonmail emails, suspicious domains
- ✅ **International calls**: Foreign phone numbers from multiple countries
- ✅ **Entity detection**: High-confidence forensic entities

## 🔧 **API Reference**

### **UFDRSemanticSearch Class**

```python
from semantic_search import UFDRSemanticSearch

# Initialize
search_engine = UFDRSemanticSearch()

# Build embeddings
search_engine.build_embeddings(session)

# Search
results = search_engine.semantic_search("find crypto wallets", top_k=5)
```

### **Key Methods**

**`build_embeddings(session)`**
- Generates embeddings for all database records
- Stores in FAISS index with metadata
- Returns: Number of embeddings created

**`semantic_search(query, top_k=5)`**
- Performs semantic search using OpenAI embeddings
- Returns: List of SearchResult objects with scores

**`search_crypto_wallets()`**
- Pre-configured search for crypto-related content
- Returns: Top crypto wallet results

## 🎯 **Search Capabilities**

### **Natural Language Queries**
- "find crypto wallets" → Bitcoin/ETH addresses
- "suspicious communications" → Fraud-related content
- "international calls" → Foreign number patterns
- "money transfer" → Financial transaction evidence

### **Semantic Understanding**
- **Context Awareness**: Understands relationships between entities
- **Fuzzy Matching**: Finds relevant content even with different wording
- **Multi-language Support**: Works with various languages and formats
- **Confidence Scoring**: Ranks results by semantic similarity

## 📈 **Performance Features**

### **Speed Optimizations**
- **FAISS Index**: Fast similarity search with O(log n) complexity
- **Batch Processing**: Efficient embedding generation
- **Caching**: Persistent index storage for reuse
- **Parallel Processing**: Concurrent embedding requests

### **Memory Efficiency**
- **Vector Compression**: Optimized storage format
- **Metadata Separation**: Lightweight metadata storage
- **Incremental Updates**: Add new embeddings without rebuilding

## 🔒 **Security & Privacy**

### **Data Protection**
- **Local Storage**: All embeddings stored locally
- **No Data Transmission**: Only query embeddings sent to OpenAI
- **Metadata Encryption**: Sensitive data protection
- **Access Control**: Database-level security

### **API Usage**
- **Rate Limiting**: Built-in request throttling
- **Cost Optimization**: Efficient embedding usage
- **Error Handling**: Graceful API failure recovery

## 🛠️ **Advanced Usage**

### **Custom Search Functions**
```python
# Search for specific patterns
def search_fraud_patterns():
    return search_engine.semantic_search("fraud money laundering", top_k=10)

# International communication analysis
def analyze_international_communications():
    return search_engine.semantic_search("international communication", top_k=15)
```

### **Integration with DSL Queries**
```python
# Combine semantic search with DSL queries
semantic_results = search_engine.semantic_search("crypto wallets")
dsl_query = {"dataset": "entities", "filters": [{"field": "type", "op": "=", "value": "bitcoin"}]}
dsl_results = run_dsl_query(dsl_query, session)
```

## 📋 **Example Queries**

### **Forensic Analysis Queries**
```python
# Crypto investigation
results = search_engine.semantic_search("bitcoin ethereum wallet address")

# Communication patterns
results = search_engine.semantic_search("suspicious communication fraud")

# International activity
results = search_engine.semantic_search("international calls foreign numbers")

# Financial transactions
results = search_engine.semantic_search("money transfer payment")
```

### **Entity-Specific Searches**
```python
# Bitcoin addresses
results = search_engine.search_crypto_wallets()

# Suspicious emails
results = search_engine.semantic_search("protonmail suspicious email")

# Long calls
results = search_engine.semantic_search("long duration calls")
```

## 🔍 **Troubleshooting**

### **Common Issues**

**1. OpenAI API Key Not Set**
```bash
export OPENAI_API_KEY="your-key-here"
```

**2. FAISS Installation Issues**
```bash
pip install faiss-cpu  # For CPU-only
pip install faiss-gpu  # For GPU acceleration
```

**3. Memory Issues with Large Datasets**
- Use batch processing for large datasets
- Consider using FAISS GPU for better performance
- Monitor memory usage during embedding generation

### **Performance Tips**
- **Batch Size**: Process embeddings in batches of 100-500
- **Index Persistence**: Save and reuse FAISS indices
- **Query Optimization**: Use specific, focused queries
- **Result Filtering**: Limit results to relevant datasets

## 🎯 **Future Enhancements**

### **Planned Features**
- **Multi-modal Search**: Image and document embeddings
- **Temporal Analysis**: Time-based semantic search
- **Clustering**: Automatic pattern detection
- **Real-time Updates**: Live embedding generation

### **Integration Opportunities**
- **Graph Databases**: Relationship analysis
- **Machine Learning**: Custom model training
- **Visualization**: Interactive search interfaces
- **API Endpoints**: REST API for external access

## 💡 **Best Practices**

### **Query Optimization**
- Use specific, descriptive queries
- Combine semantic search with DSL filters
- Leverage metadata for result filtering
- Use confidence scores for ranking

### **Data Management**
- Regular index updates for new data
- Backup FAISS indices and metadata
- Monitor embedding costs and usage
- Clean up old or unused indices

The UFDR Semantic Search system provides powerful, AI-driven search capabilities for forensic analysis, enabling investigators to find relevant evidence through natural language queries! 🎯
