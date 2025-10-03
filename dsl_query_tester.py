#!/usr/bin/env python3
"""
DSL Query Tester for SQLAlchemy Database

This module provides functions to test DSL queries against the SQLAlchemy database
with validation, SQL compilation, and execution capabilities.
"""

from typing import Dict, List, Any, Union
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

from models import Message, Call, Contact, Entity, init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Valid datasets and their corresponding models
DATASET_MODELS = {
    "messages": Message,
    "calls": Call,
    "contacts": Contact,
    "entities": Entity
}

# Valid fields for each dataset
DATASET_FIELDS = {
    "messages": {"id", "sender", "receiver", "app", "timestamp", "text"},
    "calls": {"id", "caller", "callee", "timestamp", "duration", "type"},
    "contacts": {"id", "name", "number", "email", "app"},
    "entities": {"id", "type", "value", "linked_message_id", "linked_call_id", "confidence"}
}

# Valid operators
VALID_OPERATORS = {"=", "!=", "contains", ">", "<", ">=", "<=", "between", "in", "not_in", "is_null", "is_not_null"}


def validate_dsl(dsl: Dict[str, Any]) -> bool:
    """
    Validate DSL query structure and content.
    
    Args:
        dsl: DSL query dictionary
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        ValueError: If DSL is invalid with specific error message
    """
    logger.info("Validating DSL query")
    
    # Check required top-level keys
    if "dataset" not in dsl:
        raise ValueError("Missing required field: 'dataset'")
    
    # Validate dataset
    dataset = dsl["dataset"]
    if dataset not in DATASET_MODELS:
        raise ValueError(f"Invalid dataset: '{dataset}'. Valid options: {list(DATASET_MODELS.keys())}")
    
    # Validate filters if present
    if "filters" in dsl:
        filters = dsl["filters"]
        if not isinstance(filters, list):
            raise ValueError("'filters' must be a list")
        
        valid_fields = DATASET_FIELDS[dataset]
        
        for i, filter_cond in enumerate(filters):
            if not isinstance(filter_cond, dict):
                raise ValueError(f"Filter {i} must be a dictionary")
            
            # Check required filter fields
            if "field" not in filter_cond:
                raise ValueError(f"Filter {i} missing required field: 'field'")
            if "op" not in filter_cond:
                raise ValueError(f"Filter {i} missing required field: 'op'")
            
            field = filter_cond["field"]
            op = filter_cond["op"]
            
            # Validate field
            if field not in valid_fields:
                raise ValueError(f"Filter {i}: Invalid field '{field}' for dataset '{dataset}'. Valid fields: {valid_fields}")
            
            # Validate operator
            if op not in VALID_OPERATORS:
                raise ValueError(f"Filter {i}: Invalid operator '{op}'. Valid operators: {VALID_OPERATORS}")
            
            # Validate value for operators that require it
            if op in {"=", "!=", "contains", ">", "<", ">=", "<="}:
                if "value" not in filter_cond:
                    raise ValueError(f"Filter {i}: Operator '{op}' requires a 'value'")
            elif op == "between":
                if "value" not in filter_cond or not isinstance(filter_cond["value"], list) or len(filter_cond["value"]) != 2:
                    raise ValueError(f"Filter {i}: Operator 'between' requires a list of exactly 2 values")
            elif op in {"in", "not_in"}:
                if "value" not in filter_cond or not isinstance(filter_cond["value"], list):
                    raise ValueError(f"Filter {i}: Operator '{op}' requires a list value")
            elif op in {"is_null", "is_not_null"}:
                if "value" in filter_cond:
                    raise ValueError(f"Filter {i}: Operator '{op}' should not have a 'value'")
    
    # Validate limit if present
    if "limit" in dsl:
        limit = dsl["limit"]
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("'limit' must be a positive integer")
    
    # Validate sort if present
    if "sort" in dsl:
        sort = dsl["sort"]
        if not isinstance(sort, list):
            raise ValueError("'sort' must be a list")
        
        valid_fields = DATASET_FIELDS[dataset]
        for i, sort_cond in enumerate(sort):
            if not isinstance(sort_cond, dict):
                raise ValueError(f"Sort condition {i} must be a dictionary")
            
            if "field" not in sort_cond:
                raise ValueError(f"Sort condition {i} missing required field: 'field'")
            
            field = sort_cond["field"]
            if field not in valid_fields:
                raise ValueError(f"Sort condition {i}: Invalid field '{field}' for dataset '{dataset}'")
            
            if "direction" in sort_cond:
                direction = sort_cond["direction"]
                if direction not in {"asc", "desc"}:
                    raise ValueError(f"Sort condition {i}: Invalid direction '{direction}'. Must be 'asc' or 'desc'")
    
    logger.info("DSL query validation successful")
    return True


def dsl_to_sql(dsl: Dict[str, Any]) -> str:
    """
    Convert DSL query to SQL string.
    
    Args:
        dsl: Validated DSL query dictionary
        
    Returns:
        str: Generated SQL query
        
    Raises:
        ValueError: If DSL compilation fails
    """
    logger.info("Converting DSL to SQL")
    
    dataset = dsl["dataset"]
    table_name = dataset
    
    # Build SELECT clause
    sql_parts = [f"SELECT * FROM {table_name}"]
    
    # Build WHERE clause
    where_conditions = []
    param_counter = 0
    
    if "filters" in dsl:
        for filter_cond in dsl["filters"]:
            field = filter_cond["field"]
            op = filter_cond["op"]
            param_counter += 1
            param_name = f"param_{param_counter}"
            
            if op == "=":
                where_conditions.append(f"{field} = :{param_name}")
            elif op == "!=":
                where_conditions.append(f"{field} != :{param_name}")
            elif op == "contains":
                where_conditions.append(f"{field} LIKE :{param_name}")
            elif op == ">":
                where_conditions.append(f"{field} > :{param_name}")
            elif op == "<":
                where_conditions.append(f"{field} < :{param_name}")
            elif op == ">=":
                where_conditions.append(f"{field} >= :{param_name}")
            elif op == "<=":
                where_conditions.append(f"{field} <= :{param_name}")
            elif op == "between":
                value = filter_cond["value"]
                where_conditions.append(f"{field} BETWEEN :{param_name}_1 AND :{param_name}_2")
            elif op == "in":
                value = filter_cond["value"]
                placeholders = ", ".join([f":{param_name}_{i}" for i in range(len(value))])
                where_conditions.append(f"{field} IN ({placeholders})")
            elif op == "not_in":
                value = filter_cond["value"]
                placeholders = ", ".join([f":{param_name}_{i}" for i in range(len(value))])
                where_conditions.append(f"{field} NOT IN ({placeholders})")
            elif op == "is_null":
                where_conditions.append(f"{field} IS NULL")
            elif op == "is_not_null":
                where_conditions.append(f"{field} IS NOT NULL")
    
    # Add WHERE clause if there are conditions
    if where_conditions:
        sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")
    
    # Build ORDER BY clause
    if "sort" in dsl:
        sort_parts = []
        for sort_cond in dsl["sort"]:
            field = sort_cond["field"]
            direction = sort_cond.get("direction", "asc").upper()
            sort_parts.append(f"{field} {direction}")
        sql_parts.append(f"ORDER BY {', '.join(sort_parts)}")
    
    # Build LIMIT clause
    if "limit" in dsl:
        sql_parts.append(f"LIMIT {dsl['limit']}")
    
    sql = " ".join(sql_parts)
    logger.info(f"Generated SQL: {sql}")
    return sql


def get_sql_parameters(dsl: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract parameters for the SQL query.
    
    Args:
        dsl: DSL query dictionary
        
    Returns:
        Dict[str, Any]: Parameter dictionary
    """
    params = {}
    param_counter = 0
    
    if "filters" in dsl:
        for filter_cond in dsl["filters"]:
            op = filter_cond["op"]
            param_counter += 1
            param_name = f"param_{param_counter}"
            
            if op == "contains":
                params[param_name] = f"%{filter_cond['value']}%"
            elif op == "between":
                value = filter_cond["value"]
                params[f"{param_name}_1"] = value[0]
                params[f"{param_name}_2"] = value[1]
            elif op in {"in", "not_in"}:
                value = filter_cond["value"]
                for i, val in enumerate(value):
                    params[f"{param_name}_{i}"] = val
            elif op not in {"is_null", "is_not_null"}:
                params[param_name] = filter_cond["value"]
    
    return params


def run_dsl_query(dsl: Dict[str, Any], session: Session) -> List[Dict[str, Any]]:
    """
    Execute a DSL query against the database.
    
    Args:
        dsl: DSL query dictionary
        session: SQLAlchemy session
        
    Returns:
        List[Dict[str, Any]]: Query results as list of dictionaries
        
    Raises:
        ValueError: If DSL validation fails
        Exception: If query execution fails
    """
    logger.info("Executing DSL query")
    
    try:
        # Step 1: Validate DSL
        validate_dsl(dsl)
        
        # Step 2: Convert to SQL
        sql = dsl_to_sql(dsl)
        
        # Step 3: Get parameters
        params = get_sql_parameters(dsl)
        
        # Step 4: Execute query
        result = session.execute(text(sql), params)
        
        # Step 5: Convert to list of dictionaries
        columns = result.keys()
        rows = result.fetchall()
        
        results = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                # Handle datetime objects
                if hasattr(value, 'isoformat'):
                    row_dict[column] = value.isoformat()
                else:
                    row_dict[column] = value
            results.append(row_dict)
        
        logger.info(f"Query executed successfully: {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"DSL query execution failed: {e}")
        raise


def demo_dsl_query():
    """
    Demo function to test DSL queries.
    """
    print("🔍 DSL Query Tester Demo")
    print("=" * 50)
    
    # Initialize database
    engine, Session = init_db("sqlite:///forensic_data.db")
    session = Session()
    
    try:
        # Demo query: Find messages containing "BTC" (limit 5)
        print("\n📱 Testing: Messages containing 'BTC' (limit 5)")
        
        dsl_query = {
            "dataset": "messages",
            "filters": [
                {"field": "text", "op": "contains", "value": "BTC"}
            ],
            "limit": 5
        }
        
        print(f"DSL Query: {dsl_query}")
        
        # Execute query
        results = run_dsl_query(dsl_query, session)
        
        print(f"\n✅ Query executed successfully!")
        print(f"📊 Results: {len(results)} messages found")
        
        if results:
            print("\n📋 Sample results:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. [{result['timestamp']}] {result['sender']} -> {result['receiver']}")
                print(f"     App: {result['app']}")
                print(f"     Text: {result['text'][:100]}...")
                print()
        else:
            print("   No messages containing 'BTC' found")
        
        # Additional demo queries
        print("\n🔍 Testing: Long calls (>10 minutes)")
        
        long_calls_query = {
            "dataset": "calls",
            "filters": [
                {"field": "duration", "op": ">", "value": 600}
            ],
            "sort": [{"field": "duration", "direction": "desc"}],
            "limit": 3
        }
        
        print(f"DSL Query: {long_calls_query}")
        
        results = run_dsl_query(long_calls_query, session)
        print(f"📊 Results: {len(results)} long calls found")
        
        for i, result in enumerate(results, 1):
            duration_min = result['duration'] // 60
            print(f"  {i}. {result['caller']} -> {result['callee']}: {duration_min} min ({result['type']})")
        
        print("\n🔍 Testing: High confidence entities")
        
        entities_query = {
            "dataset": "entities",
            "filters": [
                {"field": "confidence", "op": ">=", "value": 0.9}
            ],
            "sort": [{"field": "confidence", "direction": "desc"}],
            "limit": 5
        }
        
        print(f"DSL Query: {entities_query}")
        
        results = run_dsl_query(entities_query, session)
        print(f"📊 Results: {len(results)} high confidence entities found")
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['type']}: {result['value']} (confidence: {result['confidence']})")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        session.close()
    
    print("\n🎯 DSL Query Tester Demo completed!")


if __name__ == "__main__":
    demo_dsl_query()
