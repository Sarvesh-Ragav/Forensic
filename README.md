# Forensic UFDR Tool

A comprehensive forensic analysis project for digital investigation and evidence collection using SQLAlchemy ORM.

## Overview

This repository contains SQLAlchemy ORM models and utilities for forensic data analysis, including:

- **Messages**: Store and analyze messaging data from various apps (WhatsApp, Telegram, etc.)
- **Calls**: Track call records including duration, type, and participants
- **Contacts**: Manage contact information from multiple sources
- **Entities**: Extract and store forensic entities (Bitcoin addresses, emails, phone numbers, etc.)

## Database Schema

### Core Tables

1. **Messages Table**

   - `id`: Primary Key
   - `sender`: Sender identifier/phone number
   - `receiver`: Receiver identifier/phone number
   - `app`: Messaging application (WhatsApp, Telegram, etc.)
   - `timestamp`: Message timestamp
   - `text`: Message content

2. **Calls Table**

   - `id`: Primary Key
   - `caller`: Caller identifier/phone number
   - `callee`: Callee identifier/phone number
   - `timestamp`: Call timestamp
   - `duration`: Call duration in seconds
   - `type`: Call type (incoming/outgoing/missed)

3. **Contacts Table**

   - `id`: Primary Key
   - `name`: Contact name
   - `number`: Phone number
   - `email`: Email address
   - `app`: Source application

4. **Entities Table**
   - `id`: Primary Key
   - `type`: Entity type (bitcoin, ethereum, foreign_number, email)
   - `value`: Entity value
   - `linked_message_id`: Foreign key to Messages (optional)
   - `linked_call_id`: Foreign key to Calls (optional)
   - `confidence`: Extraction confidence score (0.0-1.0)

## Getting Started

### Prerequisites

- Python 3.7+
- SQLAlchemy 2.0+

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Sarvesh-Ragav/Forensic.git
cd Forensic
```

2. Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

### Usage

#### Basic Database Operations

```python
from models import init_db
from database_utils import ForensicDB

# Initialize database
engine, Session = init_db("sqlite:///forensic_data.db")
session = Session()
db = ForensicDB(session)

# Add a message
message = db.add_message(
    sender="+1234567890",
    receiver="+0987654321",
    app="WhatsApp",
    timestamp=datetime.now(),
    text="Sample message"
)

# Add an entity
entity = db.add_entity(
    entity_type="bitcoin",
    value="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    confidence=0.95,
    linked_message_id=message.id
)

# Query Bitcoin addresses
bitcoin_addresses = db.get_bitcoin_addresses()
```

#### Running Examples

```bash
# Run the basic model test
python models.py

# Run the comprehensive example
python example_usage.py

# Run database utilities test
python database_utils.py
```

## Features

- **Comprehensive ORM Models**: Full SQLAlchemy models with relationships and indexes
- **Forensic Analysis Queries**: Pre-built queries for common forensic analysis tasks
- **Entity Extraction**: Support for extracting and linking entities to messages/calls
- **Timeline Analysis**: Get chronological data for specific time ranges
- **Statistics**: Database statistics and analytics
- **Multi-Database Support**: Works with SQLite, PostgreSQL, MySQL

## Database Support

- **SQLite**: Default, no additional drivers needed
- **PostgreSQL**: Requires `psycopg2-binary`
- **MySQL**: Requires `PyMySQL`

## Project Structure

```
Forensic/
├── models.py              # SQLAlchemy ORM models
├── database_utils.py      # Database operations and queries
├── example_usage.py       # Usage examples
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── venv/                 # Virtual environment (created locally)
```

## License

[Add your license information here]
