"""
Database utility functions for the Forensic UFDR tool.

This module provides helper functions for common database operations
and forensic data analysis queries.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import List, Optional, Dict, Any
from models import Message, Call, Contact, Entity, Base


class ForensicDB:
    """
    Database operations class for forensic data analysis.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def add_message(self, sender: str, receiver: str, app: str, 
                   timestamp: datetime, text: str = None) -> Message:
        """Add a new message to the database."""
        message = Message(
            sender=sender,
            receiver=receiver,
            app=app,
            timestamp=timestamp,
            text=text
        )
        self.session.add(message)
        self.session.commit()
        return message
    
    def add_call(self, caller: str, callee: str, timestamp: datetime,
                duration: int = None, call_type: str = "outgoing") -> Call:
        """Add a new call record to the database."""
        call = Call(
            caller=caller,
            callee=callee,
            timestamp=timestamp,
            duration=duration,
            type=call_type
        )
        self.session.add(call)
        self.session.commit()
        return call
    
    def add_contact(self, name: str = None, number: str = None,
                   email: str = None, app: str = "unknown") -> Contact:
        """Add a new contact to the database."""
        contact = Contact(
            name=name,
            number=number,
            email=email,
            app=app
        )
        self.session.add(contact)
        self.session.commit()
        return contact
    
    def add_entity(self, entity_type: str, value: str, confidence: float = 1.0,
                  linked_message_id: int = None, linked_call_id: int = None) -> Entity:
        """Add a new extracted entity to the database."""
        entity = Entity(
            type=entity_type,
            value=value,
            confidence=confidence,
            linked_message_id=linked_message_id,
            linked_call_id=linked_call_id
        )
        self.session.add(entity)
        self.session.commit()
        return entity
    
    def get_messages_by_sender(self, sender: str, app: str = None) -> List[Message]:
        """Get all messages from a specific sender."""
        query = self.session.query(Message).filter(Message.sender == sender)
        if app:
            query = query.filter(Message.app == app)
        return query.order_by(desc(Message.timestamp)).all()
    
    def get_messages_by_receiver(self, receiver: str, app: str = None) -> List[Message]:
        """Get all messages to a specific receiver."""
        query = self.session.query(Message).filter(Message.receiver == receiver)
        if app:
            query = query.filter(Message.app == app)
        return query.order_by(desc(Message.timestamp)).all()
    
    def get_conversation(self, participant1: str, participant2: str, 
                        app: str = None) -> List[Message]:
        """Get conversation between two participants."""
        query = self.session.query(Message).filter(
            or_(
                and_(Message.sender == participant1, Message.receiver == participant2),
                and_(Message.sender == participant2, Message.receiver == participant1)
            )
        )
        if app:
            query = query.filter(Message.app == app)
        return query.order_by(asc(Message.timestamp)).all()
    
    def get_calls_by_participant(self, participant: str, 
                               call_type: str = None) -> List[Call]:
        """Get all calls involving a specific participant."""
        query = self.session.query(Call).filter(
            or_(Call.caller == participant, Call.callee == participant)
        )
        if call_type:
            query = query.filter(Call.type == call_type)
        return query.order_by(desc(Call.timestamp)).all()
    
    def get_entities_by_type(self, entity_type: str, 
                           min_confidence: float = 0.0) -> List[Entity]:
        """Get all entities of a specific type."""
        return self.session.query(Entity).filter(
            and_(
                Entity.type == entity_type,
                Entity.confidence >= min_confidence
            )
        ).all()
    
    def get_bitcoin_addresses(self, min_confidence: float = 0.8) -> List[Entity]:
        """Get all Bitcoin addresses found in the data."""
        return self.get_entities_by_type("bitcoin", min_confidence)
    
    def get_ethereum_addresses(self, min_confidence: float = 0.8) -> List[Entity]:
        """Get all Ethereum addresses found in the data."""
        return self.get_entities_by_type("ethereum", min_confidence)
    
    def get_foreign_numbers(self, min_confidence: float = 0.8) -> List[Entity]:
        """Get all foreign phone numbers found in the data."""
        return self.get_entities_by_type("foreign_number", min_confidence)
    
    def get_emails(self, min_confidence: float = 0.8) -> List[Entity]:
        """Get all email addresses found in the data."""
        return self.get_entities_by_type("email", min_confidence)
    
    def get_entities_from_message(self, message_id: int) -> List[Entity]:
        """Get all entities extracted from a specific message."""
        return self.session.query(Entity).filter(
            Entity.linked_message_id == message_id
        ).all()
    
    def get_entities_from_call(self, call_id: int) -> List[Entity]:
        """Get all entities extracted from a specific call."""
        return self.session.query(Entity).filter(
            Entity.linked_call_id == call_id
        ).all()
    
    def search_messages(self, search_term: str, app: str = None) -> List[Message]:
        """Search for messages containing a specific term."""
        query = self.session.query(Message).filter(
            Message.text.contains(search_term)
        )
        if app:
            query = query.filter(Message.app == app)
        return query.order_by(desc(Message.timestamp)).all()
    
    def get_timeline(self, start_date: datetime, end_date: datetime) -> Dict[str, List]:
        """Get all forensic data within a specific time range."""
        messages = self.session.query(Message).filter(
            and_(
                Message.timestamp >= start_date,
                Message.timestamp <= end_date
            )
        ).order_by(asc(Message.timestamp)).all()
        
        calls = self.session.query(Call).filter(
            and_(
                Call.timestamp >= start_date,
                Call.timestamp <= end_date
            )
        ).order_by(asc(Call.timestamp)).all()
        
        return {
            "messages": messages,
            "calls": calls
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {
            "total_messages": self.session.query(Message).count(),
            "total_calls": self.session.query(Call).count(),
            "total_contacts": self.session.query(Contact).count(),
            "total_entities": self.session.query(Entity).count(),
            "messages_by_app": {},
            "calls_by_type": {},
            "entities_by_type": {}
        }
        
        # Messages by app
        app_counts = self.session.query(
            Message.app, func.count(Message.id)
        ).group_by(Message.app).all()
        stats["messages_by_app"] = dict(app_counts)
        
        # Calls by type
        type_counts = self.session.query(
            Call.type, func.count(Call.id)
        ).group_by(Call.type).all()
        stats["calls_by_type"] = dict(type_counts)
        
        # Entities by type
        entity_counts = self.session.query(
            Entity.type, func.count(Entity.id)
        ).group_by(Entity.type).all()
        stats["entities_by_type"] = dict(entity_counts)
        
        return stats
    
    def get_contact_by_number(self, number: str) -> Optional[Contact]:
        """Find contact by phone number."""
        return self.session.query(Contact).filter(Contact.number == number).first()
    
    def get_contact_by_email(self, email: str) -> Optional[Contact]:
        """Find contact by email address."""
        return self.session.query(Contact).filter(Contact.email == email).first()
    
    def close(self):
        """Close the database session."""
        self.session.close()


def create_forensic_db(database_url: str = "sqlite:///forensic_data.db") -> ForensicDB:
    """
    Create a ForensicDB instance with a new session.
    
    Args:
        database_url: Database connection URL
    
    Returns:
        ForensicDB: Database operations instance
    """
    from models import init_db
    engine, Session = init_db(database_url)
    session = Session()
    return ForensicDB(session)


# Example usage
if __name__ == "__main__":
    # Create database instance
    db = create_forensic_db()
    
    # Get statistics
    stats = db.get_statistics()
    print("Database Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Close connection
    db.close()
