"""
SQLAlchemy ORM models for Forensic UFDR (Universal Forensic Data Recovery) tool.

This module defines the database schema for storing forensic data including
messages, calls, contacts, and extracted entities.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, ForeignKey, 
    create_engine, Index
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

# Create the declarative base
Base = declarative_base()


class Message(Base):
    """
    Model for storing message data from various messaging applications.
    
    Attributes:
        id: Primary key
        sender: Phone number or identifier of the sender
        receiver: Phone number or identifier of the receiver
        app: Messaging application (WhatsApp, Telegram, etc.)
        timestamp: When the message was sent/received
        text: Message content
        entities: Related entities extracted from this message
    """
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender = Column(String(255), nullable=False, index=True)
    receiver = Column(String(255), nullable=False, index=True)
    app = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    text = Column(Text, nullable=True)
    
    # Relationships
    entities = relationship("Entity", back_populates="linked_message", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_messages_sender_app', 'sender', 'app'),
        Index('idx_messages_receiver_app', 'receiver', 'app'),
        Index('idx_messages_timestamp_app', 'timestamp', 'app'),
    )
    
    def __repr__(self):
        return f"<Message(id={self.id}, sender='{self.sender}', receiver='{self.receiver}', app='{self.app}', timestamp='{self.timestamp}')>"


class Call(Base):
    """
    Model for storing call data including phone calls and VoIP calls.
    
    Attributes:
        id: Primary key
        caller: Phone number or identifier of the caller
        callee: Phone number or identifier of the callee
        timestamp: When the call was made/received
        duration: Call duration in seconds
        type: Call type (incoming/outgoing/missed)
        entities: Related entities extracted from this call
    """
    __tablename__ = 'calls'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    caller = Column(String(255), nullable=False, index=True)
    callee = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    type = Column(String(20), nullable=False, index=True)  # incoming/outgoing/missed
    
    # Relationships
    entities = relationship("Entity", back_populates="linked_call", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_calls_caller_type', 'caller', 'type'),
        Index('idx_calls_callee_type', 'callee', 'type'),
        Index('idx_calls_timestamp_type', 'timestamp', 'type'),
    )
    
    def __repr__(self):
        return f"<Call(id={self.id}, caller='{self.caller}', callee='{self.callee}', type='{self.type}', timestamp='{self.timestamp}')>"


class Contact(Base):
    """
    Model for storing contact information from various sources.
    
    Attributes:
        id: Primary key
        name: Contact name
        number: Phone number
        email: Email address
        app: Source application
    """
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True, index=True)
    number = Column(String(50), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    app = Column(String(100), nullable=False, index=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_contacts_number_app', 'number', 'app'),
        Index('idx_contacts_email_app', 'email', 'app'),
        Index('idx_contacts_name_app', 'name', 'app'),
    )
    
    def __repr__(self):
        return f"<Contact(id={self.id}, name='{self.name}', number='{self.number}', email='{self.email}', app='{self.app}')>"


class Entity(Base):
    """
    Model for storing extracted entities from messages and calls.
    
    Attributes:
        id: Primary key
        type: Entity type (bitcoin, ethereum, foreign_number, email, etc.)
        value: The actual entity value
        linked_message_id: Foreign key to related message (optional)
        linked_call_id: Foreign key to related call (optional)
        confidence: Confidence score for the extraction (0.0 to 1.0)
        linked_message: Related message object
        linked_call: Related call object
    """
    __tablename__ = 'entities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False, index=True)
    value = Column(String(500), nullable=False, index=True)
    linked_message_id = Column(Integer, ForeignKey('messages.id'), nullable=True, index=True)
    linked_call_id = Column(Integer, ForeignKey('calls.id'), nullable=True, index=True)
    confidence = Column(Float, nullable=False, default=1.0)
    
    # Relationships
    linked_message = relationship("Message", back_populates="entities")
    linked_call = relationship("Call", back_populates="entities")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_entities_type_value', 'type', 'value'),
        Index('idx_entities_confidence', 'confidence'),
        Index('idx_entities_linked_message', 'linked_message_id'),
        Index('idx_entities_linked_call', 'linked_call_id'),
    )
    
    def __repr__(self):
        return f"<Entity(id={self.id}, type='{self.type}', value='{self.value}', confidence={self.confidence})>"


def init_db(database_url="sqlite:///forensic_data.db"):
    """
    Initialize the database and create all tables.
    
    Args:
        database_url (str): Database connection URL. Defaults to SQLite.
                           Examples:
                           - SQLite: "sqlite:///forensic_data.db"
                           - PostgreSQL: "postgresql://user:pass@localhost/forensic_db"
                           - MySQL: "mysql://user:pass@localhost/forensic_db"
    
    Returns:
        tuple: (engine, Session) - Database engine and session factory
    """
    # Create engine
    engine = create_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,  # Verify connections before use
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
    )
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session factory
    Session = sessionmaker(bind=engine)
    
    return engine, Session


def get_session(database_url="sqlite:///forensic_data.db"):
    """
    Get a database session for performing operations.
    
    Args:
        database_url (str): Database connection URL
    
    Returns:
        Session: SQLAlchemy session object
    """
    engine, Session = init_db(database_url)
    return Session()


# Example usage and utility functions
def create_sample_data(session):
    """
    Create sample data for testing purposes.
    
    Args:
        session: SQLAlchemy session object
    """
    # Sample messages
    messages = [
        Message(
            sender="+1234567890",
            receiver="+0987654321",
            app="WhatsApp",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            text="Hey, can you send me your Bitcoin address?"
        ),
        Message(
            sender="+0987654321",
            receiver="+1234567890",
            app="WhatsApp",
            timestamp=datetime(2024, 1, 15, 10, 32, 0),
            text="Sure! It's 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        ),
    ]
    
    # Sample calls
    calls = [
        Call(
            caller="+1234567890",
            callee="+0987654321",
            timestamp=datetime(2024, 1, 15, 11, 0, 0),
            duration=300,  # 5 minutes
            type="outgoing"
        ),
    ]
    
    # Sample contacts
    contacts = [
        Contact(
            name="John Doe",
            number="+1234567890",
            email="john@example.com",
            app="WhatsApp"
        ),
    ]
    
    # Sample entities
    entities = [
        Entity(
            type="bitcoin",
            value="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            linked_message_id=2,  # Links to the second message
            confidence=0.95
        ),
        Entity(
            type="foreign_number",
            value="+0987654321",
            linked_message_id=1,
            confidence=1.0
        ),
    ]
    
    # Add all to session
    session.add_all(messages + calls + contacts + entities)
    session.commit()
    
    print("Sample data created successfully!")


if __name__ == "__main__":
    # Initialize database
    engine, Session = init_db()
    session = Session()
    
    # Create sample data
    create_sample_data(session)
    
    # Query examples
    print("\n=== Sample Queries ===")
    
    # Get all messages
    messages = session.query(Message).all()
    print(f"Total messages: {len(messages)}")
    
    # Get all entities
    entities = session.query(Entity).all()
    print(f"Total entities: {len(entities)}")
    
    # Get Bitcoin addresses
    bitcoin_entities = session.query(Entity).filter(Entity.type == "bitcoin").all()
    print(f"Bitcoin addresses found: {len(bitcoin_entities)}")
    
    session.close()
