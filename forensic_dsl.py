"""
Forensic UFDR Query DSL (Domain-Specific Language)

This module provides a JSON-based DSL for querying forensic data with
Pydantic validation and SQL generation capabilities.
"""

from typing import List, Union, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import re


class DatasetType(str, Enum):
    """Supported dataset types."""
    MESSAGES = "messages"
    CALLS = "calls"
    CONTACTS = "contacts"
    ENTITIES = "entities"


class FilterOperator(str, Enum):
    """Supported filter operators."""
    EQUALS = "="
    NOT_EQUALS = "!="
    CONTAINS = "contains"
    REGEX = "regex"
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    COUNTRY = "country"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class SortDirection(str, Enum):
    """Sort direction options."""
    ASC = "asc"
    DESC = "desc"


class FilterCondition(BaseModel):
    """Individual filter condition."""
    field: str = Field(..., description="Column name to filter on")
    op: FilterOperator = Field(..., description="Filter operator")
    value: Optional[Union[str, int, float, List[Union[str, int, float]]]] = Field(
        None, description="Filter value (not required for null checks)"
    )
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v, info):
        """Validate value based on operator."""
        op = info.data.get('op')
        
        # Operators that don't require values
        if op in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            if v is not None:
                raise ValueError(f"Operator '{op}' does not require a value")
            return v
        
        # Operators that require values
        if op in [FilterOperator.EQUALS, FilterOperator.NOT_EQUALS, 
                 FilterOperator.CONTAINS, FilterOperator.REGEX, 
                 FilterOperator.GREATER_THAN, FilterOperator.LESS_THAN,
                 FilterOperator.GREATER_EQUAL, FilterOperator.LESS_EQUAL,
                 FilterOperator.COUNTRY]:
            if v is None:
                raise ValueError(f"Operator '{op}' requires a value")
        
        # Operators that require list values
        if op in [FilterOperator.BETWEEN, FilterOperator.IN, FilterOperator.NOT_IN]:
            if not isinstance(v, list) or len(v) < 2:
                raise ValueError(f"Operator '{op}' requires a list with at least 2 values")
        
        # Validate regex patterns
        if op == FilterOperator.REGEX and isinstance(v, str):
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
        
        return v


class SortCondition(BaseModel):
    """Sort condition."""
    field: str = Field(..., description="Column name to sort by")
    direction: SortDirection = Field(default=SortDirection.ASC, description="Sort direction")


class ForensicQuery(BaseModel):
    """Main DSL query model."""
    dataset: DatasetType = Field(..., description="Dataset to query")
    filters: List[FilterCondition] = Field(default=[], description="List of filter conditions")
    limit: Optional[int] = Field(None, ge=1, le=10000, description="Maximum number of results")
    sort: Optional[List[SortCondition]] = Field(default=[], description="Sort conditions")
    
    @field_validator('filters')
    @classmethod
    def validate_filters(cls, v):
        """Validate that filters are not empty if provided."""
        if v is None:
            return []
        return v
    
    @field_validator('sort')
    @classmethod
    def validate_sort(cls, v):
        """Validate sort conditions."""
        if v is None:
            return []
        return v


# Field mappings for each dataset
FIELD_MAPPINGS = {
    DatasetType.MESSAGES: {
        "id", "sender", "receiver", "app", "timestamp", "text"
    },
    DatasetType.CALLS: {
        "id", "caller", "callee", "timestamp", "duration", "type"
    },
    DatasetType.CONTACTS: {
        "id", "name", "number", "email", "app"
    },
    DatasetType.ENTITIES: {
        "id", "type", "value", "linked_message_id", "linked_call_id", "confidence"
    }
}

# Country code mappings for phone numbers
COUNTRY_CODES = {
    "UAE": ["+971"],
    "USA": ["+1"],
    "UK": ["+44"],
    "INDIA": ["+91"],
    "CHINA": ["+86"],
    "GERMANY": ["+49"],
    "FRANCE": ["+33"],
    "JAPAN": ["+81"],
    "BRAZIL": ["+55"],
    "RUSSIA": ["+7"],
    "CANADA": ["+1"],
    "AUSTRALIA": ["+61"],
    "SOUTH_KOREA": ["+82"],
    "ITALY": ["+39"],
    "SPAIN": ["+34"],
    "NETHERLANDS": ["+31"],
    "SWEDEN": ["+46"],
    "NORWAY": ["+47"],
    "DENMARK": ["+45"],
    "FINLAND": ["+358"],
    "POLAND": ["+48"],
    "TURKEY": ["+90"],
    "SAUDI_ARABIA": ["+966"],
    "EGYPT": ["+20"],
    "SOUTH_AFRICA": ["+27"],
    "NIGERIA": ["+234"],
    "KENYA": ["+254"],
    "MOROCCO": ["+212"],
    "ALGERIA": ["+213"],
    "TUNISIA": ["+216"],
    "LIBYA": ["+218"],
    "SUDAN": ["+249"],
    "ETHIOPIA": ["+251"],
    "UGANDA": ["+256"],
    "TANZANIA": ["+255"],
    "GHANA": ["+233"],
    "IVORY_COAST": ["+225"],
    "SENEGAL": ["+221"],
    "MALI": ["+223"],
    "BURKINA_FASO": ["+226"],
    "NIGER": ["+227"],
    "CHAD": ["+235"],
    "CAMEROON": ["+237"],
    "CENTRAL_AFRICAN_REPUBLIC": ["+236"],
    "CONGO": ["+242"],
    "DEMOCRATIC_REPUBLIC_OF_CONGO": ["+243"],
    "GABON": ["+241"],
    "EQUATORIAL_GUINEA": ["+240"],
    "SAO_TOME_AND_PRINCIPE": ["+239"],
    "CAPE_VERDE": ["+238"],
    "GUINEA": ["+224"],
    "GUINEA_BISSAU": ["+245"],
    "SIERRA_LEONE": ["+232"],
    "LIBERIA": ["+231"],
    "GAMBIA": ["+220"],
    "MAURITANIA": ["+222"],
    "MALI": ["+223"],
    "BURKINA_FASO": ["+226"],
    "NIGER": ["+227"],
    "CHAD": ["+235"],
    "CAMEROON": ["+237"],
    "CENTRAL_AFRICAN_REPUBLIC": ["+236"],
    "CONGO": ["+242"],
    "DEMOCRATIC_REPUBLIC_OF_CONGO": ["+243"],
    "GABON": ["+241"],
    "EQUATORIAL_GUINEA": ["+240"],
    "SAO_TOME_AND_PRINCIPE": ["+239"],
    "CAPE_VERDE": ["+238"],
    "GUINEA": ["+224"],
    "GUINEA_BISSAU": ["+245"],
    "SIERRA_LEONE": ["+232"],
    "LIBERIA": ["+231"],
    "GAMBIA": ["+220"],
    "MAURITANIA": ["+222"]
}


def validate_field_for_dataset(dataset: DatasetType, field: str) -> bool:
    """Validate if a field exists for the given dataset."""
    return field in FIELD_MAPPINGS.get(dataset, set())


def dsl_to_sql(dsl: Union[Dict[str, Any], ForensicQuery]) -> str:
    """
    Enhanced DSL to SQL compiler with improved country code detection and security.
    
    Rules:
    - dataset maps directly to table name (messages, calls, contacts, entities)
    - filters map to WHERE clauses with proper parameterization
    - '=' and '!=' → normal equality
    - 'contains' → LIKE '%value%'
    - 'regex' → REGEXP (database-specific)
    - '>' and '<' → numeric comparison
    - 'between' → value is [low, high], maps to BETWEEN
    - 'country' → detect by prefix (+971 → UAE, +44 → UK). Use LIKE filter
    
    Args:
        dsl: DSL query as dict or ForensicQuery object
        
    Returns:
        str: Safe parameterized SQL query
    """
    if isinstance(dsl, dict):
        query = ForensicQuery(**dsl)
    else:
        query = dsl
    
    # Validate dataset
    if query.dataset not in FIELD_MAPPINGS:
        raise ValueError(f"Invalid dataset: {query.dataset}")
    
    # Build SELECT clause - dataset maps directly to table name
    select_clause = f"SELECT * FROM {query.dataset.value}"
    
    # Build WHERE clause with enhanced parameter handling
    where_conditions = []
    param_counter = 0
    
    for filter_cond in query.filters:
        # Validate field exists for dataset
        if not validate_field_for_dataset(query.dataset, filter_cond.field):
            raise ValueError(f"Field '{filter_cond.field}' not valid for dataset '{query.dataset}'")
        
        param_counter += 1
        param_name = f"param_{param_counter}"
        
        # Handle each operator according to the rules
        if filter_cond.op == FilterOperator.EQUALS:
            # '=' → normal equality
            where_conditions.append(f"{filter_cond.field} = :{param_name}")
            
        elif filter_cond.op == FilterOperator.NOT_EQUALS:
            # '!=' → normal inequality
            where_conditions.append(f"{filter_cond.field} != :{param_name}")
            
        elif filter_cond.op == FilterOperator.CONTAINS:
            # 'contains' → LIKE '%value%'
            where_conditions.append(f"{filter_cond.field} LIKE :{param_name}")
            # Note: The % wrapping will be handled in parameter binding
            
        elif filter_cond.op == FilterOperator.REGEX:
            # 'regex' → REGEXP (database-specific implementation)
            # For SQLite, this requires a custom REGEXP function
            where_conditions.append(f"REGEXP(:{param_name}, {filter_cond.field})")
            
        elif filter_cond.op == FilterOperator.GREATER_THAN:
            # '>' → numeric comparison
            where_conditions.append(f"{filter_cond.field} > :{param_name}")
            
        elif filter_cond.op == FilterOperator.LESS_THAN:
            # '<' → numeric comparison
            where_conditions.append(f"{filter_cond.field} < :{param_name}")
            
        elif filter_cond.op == FilterOperator.GREATER_EQUAL:
            where_conditions.append(f"{filter_cond.field} >= :{param_name}")
            
        elif filter_cond.op == FilterOperator.LESS_EQUAL:
            where_conditions.append(f"{filter_cond.field} <= :{param_name}")
            
        elif filter_cond.op == FilterOperator.BETWEEN:
            # 'between' → value is [low, high], maps to BETWEEN
            if not isinstance(filter_cond.value, list) or len(filter_cond.value) != 2:
                raise ValueError("BETWEEN operator requires exactly 2 values [low, high]")
            where_conditions.append(f"{filter_cond.field} BETWEEN :{param_name}_1 AND :{param_name}_2")
            
        elif filter_cond.op == FilterOperator.IN:
            placeholders = ", ".join([f":{param_name}_{i}" for i in range(len(filter_cond.value))])
            where_conditions.append(f"{filter_cond.field} IN ({placeholders})")
            
        elif filter_cond.op == FilterOperator.NOT_IN:
            placeholders = ", ".join([f":{param_name}_{i}" for i in range(len(filter_cond.value))])
            where_conditions.append(f"{filter_cond.field} NOT IN ({placeholders})")
            
        elif filter_cond.op == FilterOperator.COUNTRY:
            # 'country' → detect by prefix (+971 → UAE, +44 → UK). Use LIKE filter
            country_codes = COUNTRY_CODES.get(filter_cond.value.upper(), [])
            if not country_codes:
                raise ValueError(f"Unknown country: {filter_cond.value}")
            
            # Check if field is a phone number field
            phone_fields = {"sender", "receiver", "caller", "callee", "number"}
            if filter_cond.field not in phone_fields:
                raise ValueError(f"Country filter can only be applied to phone number fields: {phone_fields}")
            
            # Build country conditions with LIKE filters
            country_conditions = []
            for code in country_codes:
                param_counter += 1
                country_param = f"param_{param_counter}"
                country_conditions.append(f"{filter_cond.field} LIKE :{country_param}")
            
            where_conditions.append(f"({' OR '.join(country_conditions)})")
            
        elif filter_cond.op == FilterOperator.IS_NULL:
            where_conditions.append(f"{filter_cond.field} IS NULL")
            
        elif filter_cond.op == FilterOperator.IS_NOT_NULL:
            where_conditions.append(f"{filter_cond.field} IS NOT NULL")
    
    # Build WHERE clause
    where_clause = ""
    if where_conditions:
        where_clause = f" WHERE {' AND '.join(where_conditions)}"
    
    # Build ORDER BY clause - if sort exists, add ORDER BY
    order_clause = ""
    if query.sort:
        sort_parts = []
        for sort_cond in query.sort:
            if not validate_field_for_dataset(query.dataset, sort_cond.field):
                raise ValueError(f"Field '{sort_cond.field}' not valid for dataset '{query.dataset}'")
            sort_parts.append(f"{sort_cond.field} {sort_cond.direction.value.upper()}")
        order_clause = f" ORDER BY {', '.join(sort_parts)}"
    
    # Build LIMIT clause - if limit exists, add LIMIT
    limit_clause = ""
    if query.limit:
        limit_clause = f" LIMIT {query.limit}"
    
    # Combine all clauses into safe SQL string
    sql = f"{select_clause}{where_clause}{order_clause}{limit_clause}"
    
    return sql


def get_sql_parameters(dsl: Union[Dict[str, Any], ForensicQuery]) -> Dict[str, Any]:
    """
    Extract parameters for the SQL query generated by dsl_to_sql.
    
    Args:
        dsl: DSL query as dict or ForensicQuery object
        
    Returns:
        Dict[str, Any]: Parameter dictionary for SQL execution
    """
    if isinstance(dsl, dict):
        query = ForensicQuery(**dsl)
    else:
        query = dsl
    
    params = {}
    param_counter = 0
    
    for filter_cond in query.filters:
        param_counter += 1
        param_name = f"param_{param_counter}"
        
        if filter_cond.op == FilterOperator.CONTAINS:
            # Wrap contains values with % for LIKE
            params[param_name] = f"%{filter_cond.value}%"
            
        elif filter_cond.op == FilterOperator.BETWEEN:
            # Handle BETWEEN with two parameters
            params[f"{param_name}_1"] = filter_cond.value[0]
            params[f"{param_name}_2"] = filter_cond.value[1]
            
        elif filter_cond.op == FilterOperator.IN or filter_cond.op == FilterOperator.NOT_IN:
            # Handle IN/NOT IN with multiple parameters
            for i, val in enumerate(filter_cond.value):
                params[f"{param_name}_{i}"] = val
                
        elif filter_cond.op == FilterOperator.COUNTRY:
            # Handle country codes with LIKE patterns
            country_codes = COUNTRY_CODES.get(filter_cond.value.upper(), [])
            for code in country_codes:
                param_counter += 1
                country_param = f"param_{param_counter}"
                params[country_param] = f"{code}%"
                
        elif filter_cond.op in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            # No parameters needed for NULL checks
            continue
            
        else:
            # Standard parameter handling
            params[param_name] = filter_cond.value
    
    return params


def run_dsl_query(dsl: Dict[str, Any], session) -> List[Dict[str, Any]]:
    """
    Execute a DSL query using SQLAlchemy session and return results as list of dicts.
    
    Steps:
    1. Validate DSL with Pydantic
    2. Compile DSL to SQL using dsl_to_sql
    3. Execute query with SQLAlchemy session.execute()
    4. Return results as list of dicts
    
    Args:
        dsl: DSL query as dictionary
        session: SQLAlchemy session object
        
    Returns:
        List[Dict[str, Any]]: Query results as list of dictionaries
        
    Raises:
        ValueError: If DSL validation fails
        Exception: If SQL execution fails
    """
    from sqlalchemy import text
    
    try:
        # Step 1: Validate DSL with Pydantic
        validated_query = validate_dsl_query(dsl)
        
        # Step 2: Compile DSL to SQL using dsl_to_sql
        sql = dsl_to_sql(validated_query)
        
        # Step 3: Get parameters for the query
        params = get_sql_parameters(validated_query)
        
        # Step 4: Execute query with SQLAlchemy session.execute()
        # Use text() to create a proper SQLAlchemy text object
        result = session.execute(text(sql), params)
        
        # Step 5: Convert results to list of dictionaries
        columns = result.keys()
        rows = result.fetchall()
        
        # Convert each row to a dictionary
        results = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                # Handle datetime objects by converting to ISO format
                if hasattr(value, 'isoformat'):
                    row_dict[column] = value.isoformat()
                else:
                    row_dict[column] = value
            results.append(row_dict)
        
        return results
        
    except Exception as e:
        # Re-raise with more context
        raise Exception(f"DSL query execution failed: {str(e)}") from e


def validate_dsl_query(dsl: Union[Dict[str, Any], str]) -> ForensicQuery:
    """
    Validate and parse DSL query.
    
    Args:
        dsl: DSL query as dict, JSON string, or ForensicQuery object
        
    Returns:
        ForensicQuery: Validated query object
    """
    import json
    
    if isinstance(dsl, str):
        try:
            dsl = json.loads(dsl)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    if isinstance(dsl, dict):
        return ForensicQuery(**dsl)
    elif isinstance(dsl, ForensicQuery):
        return dsl
    else:
        raise ValueError("DSL must be a dict, JSON string, or ForensicQuery object")


# Example queries
EXAMPLE_QUERIES = {
    "whatsapp_uae": {
        "dataset": "messages",
        "filters": [
            {"field": "app", "op": "=", "value": "WhatsApp"},
            {"field": "receiver", "op": "country", "value": "UAE"}
        ]
    },
    "long_calls": {
        "dataset": "calls",
        "filters": [
            {"field": "duration", "op": ">", "value": 600}
        ]
    },
    "protonmail_contacts": {
        "dataset": "contacts",
        "filters": [
            {"field": "email", "op": "contains", "value": "protonmail"}
        ]
    },
    "bitcoin_entities": {
        "dataset": "entities",
        "filters": [
            {"field": "type", "op": "=", "value": "bitcoin"},
            {"field": "confidence", "op": ">=", "value": 0.8}
        ],
        "sort": [{"field": "confidence", "direction": "desc"}]
    },
    "recent_messages": {
        "dataset": "messages",
        "filters": [
            {"field": "timestamp", "op": ">=", "value": "2024-01-01"}
        ],
        "sort": [{"field": "timestamp", "direction": "desc"}],
        "limit": 100
    },
    "suspicious_communications": {
        "dataset": "messages",
        "filters": [
            {"field": "app", "op": "in", "value": ["Telegram", "Signal"]},
            {"field": "text", "op": "contains", "value": "bitcoin"}
        ]
    }
}


if __name__ == "__main__":
    # Test the DSL with example queries
    print("🔍 Testing Forensic DSL")
    print("=" * 50)
    
    for name, query_dict in EXAMPLE_QUERIES.items():
        print(f"\n📋 Example: {name}")
        print(f"DSL: {query_dict}")
        
        try:
            # Validate query
            query = validate_dsl_query(query_dict)
            print(f"✅ Validated: {query.dataset} with {len(query.filters)} filters")
            
            # Generate SQL
            sql = dsl_to_sql(query)
            print(f"🔧 SQL: {sql}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎯 DSL testing complete!")
