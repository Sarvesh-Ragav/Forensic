# Forensic UFDR Query DSL Documentation

## Overview

The Forensic UFDR Query DSL (Domain-Specific Language) is a JSON-based query language designed for forensic data analysis. It provides a structured way to query forensic databases with natural language-like syntax while maintaining type safety and validation.

## Features

- **JSON-based syntax** - Easy to read and write
- **Pydantic validation** - Type-safe query validation
- **SQL generation** - Converts DSL to parameterized SQL
- **Comprehensive operators** - Supports various filter operations
- **Country-based filtering** - Special handling for international phone numbers
- **Sorting and limiting** - Full query control
- **Error handling** - Detailed validation and error messages

## DSL Structure

### Top-Level Keys

```json
{
  "dataset": "messages|calls|contacts|entities",
  "filters": [...],
  "limit": 100,
  "sort": [...]
}
```

- **`dataset`** (required): The table to query
- **`filters`** (optional): List of filter conditions
- **`limit`** (optional): Maximum number of results (1-10000)
- **`sort`** (optional): List of sort conditions

## Datasets

### Messages
- `id`, `sender`, `receiver`, `app`, `timestamp`, `text`

### Calls
- `id`, `caller`, `callee`, `timestamp`, `duration`, `type`

### Contacts
- `id`, `name`, `number`, `email`, `app`

### Entities
- `id`, `type`, `value`, `linked_message_id`, `linked_call_id`, `confidence`

## Filter Operators

| Operator | Description | Value Type | Example |
|----------|-------------|------------|---------|
| `=` | Equals | string/number | `{"field": "app", "op": "=", "value": "WhatsApp"}` |
| `!=` | Not equals | string/number | `{"field": "type", "op": "!=", "value": "missed"}` |
| `contains` | Contains substring | string | `{"field": "text", "op": "contains", "value": "bitcoin"}` |
| `regex` | Regular expression | string | `{"field": "email", "op": "regex", "value": ".*@protonmail\\.com"}` |
| `>` | Greater than | number | `{"field": "duration", "op": ">", "value": 600}` |
| `<` | Less than | number | `{"field": "confidence", "op": "<", "value": 0.5}` |
| `>=` | Greater than or equal | number | `{"field": "timestamp", "op": ">=", "value": "2024-01-01"}` |
| `<=` | Less than or equal | number | `{"field": "duration", "op": "<=", "value": 300}` |
| `between` | Between two values | [min, max] | `{"field": "duration", "op": "between", "value": [300, 600]}` |
| `in` | In list of values | array | `{"field": "app", "op": "in", "value": ["WhatsApp", "Telegram"]}` |
| `not_in` | Not in list | array | `{"field": "type", "op": "not_in", "value": ["missed"]}` |
| `country` | Country code filter | string | `{"field": "sender", "op": "country", "value": "UAE"}` |
| `is_null` | Is null | null | `{"field": "linked_call_id", "op": "is_null", "value": null}` |
| `is_not_null` | Is not null | null | `{"field": "linked_message_id", "op": "is_not_null", "value": null}` |

## Sort Conditions

```json
{
  "field": "timestamp",
  "direction": "asc|desc"
}
```

## Example Queries

### 1. WhatsApp Messages with UAE Numbers

**Natural Language**: "Show all WhatsApp chats with UAE numbers"

**DSL**:
```json
{
  "dataset": "messages",
  "filters": [
    {"field": "app", "op": "=", "value": "WhatsApp"},
    {"field": "receiver", "op": "country", "value": "UAE"}
  ]
}
```

**Generated SQL**:
```sql
SELECT * FROM messages 
WHERE app = :param_1 
AND (receiver LIKE :param_3)
```

### 2. Long Calls

**Natural Language**: "List all calls longer than 10 minutes"

**DSL**:
```json
{
  "dataset": "calls",
  "filters": [
    {"field": "duration", "op": ">", "value": 600}
  ]
}
```

**Generated SQL**:
```sql
SELECT * FROM calls 
WHERE duration > :param_1
```

### 3. ProtonMail Contacts

**Natural Language**: "Find contacts with protonmail emails"

**DSL**:
```json
{
  "dataset": "contacts",
  "filters": [
    {"field": "email", "op": "contains", "value": "protonmail"}
  ]
}
```

**Generated SQL**:
```sql
SELECT * FROM contacts 
WHERE email LIKE :param_1
```

### 4. High-Confidence Bitcoin Entities

**Natural Language**: "Find Bitcoin addresses with high confidence scores"

**DSL**:
```json
{
  "dataset": "entities",
  "filters": [
    {"field": "type", "op": "=", "value": "bitcoin"},
    {"field": "confidence", "op": ">=", "value": 0.8}
  ],
  "sort": [
    {"field": "confidence", "direction": "desc"}
  ]
}
```

**Generated SQL**:
```sql
SELECT * FROM entities 
WHERE type = :param_1 
AND confidence >= :param_2 
ORDER BY confidence DESC
```

### 5. Suspicious Communications

**Natural Language**: "Find messages from privacy apps containing Bitcoin references"

**DSL**:
```json
{
  "dataset": "messages",
  "filters": [
    {"field": "app", "op": "in", "value": ["Telegram", "Signal"]},
    {"field": "text", "op": "contains", "value": "bitcoin"}
  ],
  "sort": [
    {"field": "timestamp", "direction": "desc"}
  ],
  "limit": 50
}
```

**Generated SQL**:
```sql
SELECT * FROM messages 
WHERE app IN (:param_1_0, :param_1_1) 
AND text LIKE :param_2 
ORDER BY timestamp DESC 
LIMIT 50
```

## Country Code Support

The DSL supports country-based filtering for phone number fields. Supported countries include:

- **UAE**: `+971`
- **USA**: `+1`
- **UK**: `+44`
- **India**: `+91`
- **China**: `+86`
- **Germany**: `+49`
- **France**: `+33`
- **Japan**: `+81`
- **Brazil**: `+55`
- **Russia**: `+7`
- **Canada**: `+1`
- **Australia**: `+61`
- And many more...

## Usage in Python

### Basic Usage

```python
from forensic_dsl import validate_dsl_query, dsl_to_sql

# Define query
query = {
    "dataset": "messages",
    "filters": [
        {"field": "app", "op": "=", "value": "WhatsApp"},
        {"field": "text", "op": "contains", "value": "bitcoin"}
    ]
}

# Validate and convert to SQL
validated_query = validate_dsl_query(query)
sql = dsl_to_sql(validated_query)
print(sql)
```

### With JSON String

```python
import json
from forensic_dsl import validate_dsl_query, dsl_to_sql

json_query = '''
{
    "dataset": "entities",
    "filters": [
        {"field": "type", "op": "=", "value": "bitcoin"},
        {"field": "confidence", "op": ">=", "value": 0.9}
    ],
    "sort": [{"field": "confidence", "direction": "desc"}],
    "limit": 10
}
'''

validated_query = validate_dsl_query(json_query)
sql = dsl_to_sql(validated_query)
```

### Error Handling

```python
try:
    query = validate_dsl_query(invalid_query)
    sql = dsl_to_sql(query)
except ValueError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"SQL generation error: {e}")
```

## Validation Rules

1. **Dataset validation**: Must be one of: `messages`, `calls`, `contacts`, `entities`
2. **Field validation**: Fields must exist for the specified dataset
3. **Operator validation**: Operators must be valid for the field type
4. **Value validation**: Values must match operator requirements
5. **Country validation**: Country filters only work on phone number fields
6. **Limit validation**: Limit must be between 1 and 10000
7. **Sort validation**: Sort fields must exist for the dataset

## Security Features

- **Parameterized queries**: All values are parameterized to prevent SQL injection
- **Field validation**: Only valid fields can be queried
- **Operator validation**: Only safe operators are allowed
- **Type validation**: Values are validated against expected types
- **Limit enforcement**: Query results are limited to prevent resource exhaustion

## Performance Considerations

- **Indexed fields**: Use indexed fields for better performance
- **Limit usage**: Always use limits for large datasets
- **Efficient filters**: Use specific filters to reduce result sets
- **Sort optimization**: Sort on indexed fields when possible

## Testing

Run the test suite to verify functionality:

```bash
python test_dsl.py
```

This will test:
- Basic query validation
- Advanced query features
- Error handling
- Example queries
- JSON string input

## Integration

The DSL integrates with the Forensic UFDR database models:

```python
from models import init_db
from database_utils import ForensicDB
from forensic_dsl import validate_dsl_query, dsl_to_sql

# Initialize database
engine, Session = init_db()
session = Session()

# Create query
query = {"dataset": "messages", "filters": [...]}
validated_query = validate_dsl_query(query)
sql = dsl_to_sql(validated_query)

# Execute query
result = session.execute(sql)
```

## Future Enhancements

- **Aggregation functions**: COUNT, SUM, AVG, etc.
- **Join operations**: Cross-table queries
- **Date/time functions**: More sophisticated time filtering
- **Geographic filtering**: Location-based queries
- **Fuzzy matching**: Approximate text matching
- **Export formats**: CSV, JSON, XML export options
