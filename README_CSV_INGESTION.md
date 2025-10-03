# UFDR CSV Data Ingestion Guide

## 🎯 **Quick Start**

Your CSV files have been successfully ingested! Here's what was processed:

### **Ingestion Results**
```
============================================================
UFDR CSV INGESTION SUMMARY
============================================================
MESSAGES       :       40 records
CALLS          :       35 records  
CONTACTS       :       40 records
ENTITIES       :       52 records
------------------------------------------------------------
TOTAL          :      167 records
============================================================
```

## 📁 **File Structure**

Place your CSV files in the Forensic directory:
```
/Users/sarveshragavb/Forensic/
├── Chats.csv          # Your chat data
├── Calls.csv          # Your call data  
├── Contacts.csv       # Your contact data
├── Entities.csv       # Your entity data
├── enhanced_csv_ingestion.py  # Ingestion script
└── ... (other files)
```

## 🚀 **Running the Ingestion**

### **Basic Usage**
```bash
cd /Users/sarveshragavb/Forensic
source venv/bin/activate
python enhanced_csv_ingestion.py
```

### **Python Usage**
```python
from enhanced_csv_ingestion import EnhancedUFDRCSVIngester

# Initialize ingester
ingester = EnhancedUFDRCSVIngester()

# Ingest all CSV files
record_counts = ingester.ingest_all_csvs()
print(f"Ingested {sum(record_counts.values())} total records")
```

## 📊 **Column Mapping**

The script automatically maps your CSV columns to database fields:

### **Chats.csv → Messages**
- `MessageID` → `id` (auto-increment)
- `SenderNumber` → `sender`
- `ReceiverNumber` → `receiver`
- `App` → `app`
- `Timestamp` → `timestamp`
- `MessageText` → `text`

### **Calls.csv → Calls**
- `CallID` → `id` (auto-increment)
- `CallerNumber` → `caller`
- `CalleeNumber` → `callee`
- `Timestamp` → `timestamp`
- `DurationSeconds` → `duration`
- `Type` → `type`

### **Contacts.csv → Contacts**
- `ContactID` → `id` (auto-increment)
- `Name` → `name`
- `PhoneNumber` → `number`
- `Email` → `email`
- `App` → `app`

### **Entities.csv → Entities**
- `EntityID` → `id` (auto-increment)
- `Type` → `type`
- `Value` → `value`
- `Label` → `confidence`

## 🔍 **Querying Your Data**

Use the DSL query system to analyze your data:

### **Find Long Calls**
```python
from forensic_dsl import run_dsl_query
from models import init_db

engine, Session = init_db()
session = Session()

query = {
    "dataset": "calls",
    "filters": [
        {"field": "duration", "op": ">", "value": 600}  # > 10 minutes
    ]
}
long_calls = run_dsl_query(query, session)
print(f"Found {len(long_calls)} long calls")
```

### **Find International Calls**
```python
query = {
    "dataset": "calls",
    "filters": [
        {"field": "caller", "op": "country", "value": "UAE"}
    ]
}
uae_calls = run_dsl_query(query, session)
```

### **Find Specific App Messages**
```python
query = {
    "dataset": "messages",
    "filters": [
        {"field": "app", "op": "=", "value": "WhatsApp"}
    ]
}
whatsapp_messages = run_dsl_query(query, session)
```

## 🛡️ **Error Handling**

The script handles common data issues:

- **Missing Values**: Rows with missing required fields are skipped
- **Invalid Timestamps**: Automatically converted or skipped
- **Data Type Issues**: Automatic type conversion with fallbacks
- **Duplicate IDs**: Uses auto-increment to avoid conflicts
- **Foreign Key Constraints**: Clears data in proper order

## 📈 **Performance Features**

- **Bulk Insert**: Uses `bulk_insert_mappings()` for speed
- **Auto-increment IDs**: Prevents primary key conflicts
- **Transaction Safety**: Full rollback on errors
- **Memory Efficient**: Processes large datasets without memory issues

## 🔧 **Advanced Options**

### **Preserve CSV IDs**
```python
record_counts = ingester.ingest_all_csvs(use_auto_id=False)
```

### **Don't Clear Existing Data**
```python
record_counts = ingester.ingest_all_csvs(clear_existing=False)
```

### **Custom Database**
```python
ingester = EnhancedUFDRCSVIngester("postgresql://user:pass@localhost/forensic_db")
```

## 🎯 **Verification**

Run the verification script to see your data:
```bash
python verify_real_data.py
```

This will show:
- Record counts for each table
- Suspicious activity analysis
- Communication patterns
- Entity confidence analysis
- Timeline analysis

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Missing CSV Files**: Ensure files are named exactly `Chats.csv`, `Calls.csv`, `Contacts.csv`, `Entities.csv`
2. **Column Mismatch**: Check that your CSV headers match the expected names
3. **Data Type Errors**: The script handles most conversions automatically
4. **Memory Issues**: For very large files, consider processing in chunks

### **Logs**

The script provides detailed logging:
- Data cleaning statistics
- Column mapping information
- Error details for failed rows
- Performance metrics

## 💡 **Next Steps**

1. **Explore Your Data**: Use the DSL query system to analyze patterns
2. **Custom Queries**: Create specific forensic analysis queries
3. **Export Results**: Use the query results for reporting
4. **Integration**: Connect with other forensic tools

Your UFDR data is now ready for comprehensive forensic analysis! 🎯
