#!/usr/bin/env python3
"""
Entity Detection Module

Scans Messages, Calls, and Contacts for suspicious patterns and stores
matches in the Entities table, linking to the source records when possible.

Patterns:
- BTC wallet:    [13][a-km-zA-HJ-NP-Z1-9]{25,34}
- ETH wallet:    0x[a-fA-F0-9]{40}
- UAE numbers:   ^\+971\d{7,9}
- Proton/MailRu: .*@(protonmail|mail\.ru)$

Summary output example:
  BTC: 2 found | ETH: 1 found | UAE Numbers: 3 found | Emails: 4 found
"""

import re
from typing import Dict, Set, Tuple
from sqlalchemy.orm import Session
from models import init_db, Message, Call, Contact, Entity

# Compile regex patterns
RE_BTC = re.compile(r"[13][a-km-zA-HJ-NP-Z1-9]{25,34}")
RE_ETH = re.compile(r"0x[a-fA-F0-9]{40}")
# For content scans, allow match anywhere; for fields, we can also use full-string check
RE_UAE_ANY = re.compile(r"\+971\d{7,9}")
RE_UAE_ANCHORED = re.compile(r"^\+971\d{7,9}$")
RE_EMAIL_ANY = re.compile(r"[^\s@]+@(protonmail|mail\.ru)", re.IGNORECASE)
RE_EMAIL_ANCHORED = re.compile(r".*@(protonmail|mail\.ru)$", re.IGNORECASE)


def _entity_exists(session: Session, entity_type: str, value: str, linked_message_id=None, linked_call_id=None) -> bool:
    query = session.query(Entity).filter(
        Entity.type == entity_type,
        Entity.value == value,
        Entity.linked_message_id.is_(linked_message_id) if linked_message_id is None else Entity.linked_message_id == linked_message_id,
        Entity.linked_call_id.is_(linked_call_id) if linked_call_id is None else Entity.linked_call_id == linked_call_id,
    )
    return session.query(query.exists()).scalar()


def _insert_entity(session: Session, entity_type: str, value: str, linked_message_id=None, linked_call_id=None):
    if _entity_exists(session, entity_type, value, linked_message_id, linked_call_id):
        return False
    entity = Entity(
        type=entity_type,
        value=value,
        confidence=1.0,
        linked_message_id=linked_message_id,
        linked_call_id=linked_call_id,
    )
    session.add(entity)
    return True


def detect_in_messages(session: Session) -> Dict[str, int]:
    counts = {"BTC": 0, "ETH": 0, "UAE": 0, "EMAIL": 0}
    for msg in session.query(Message).all():
        # Text-based detections
        if msg.text:
            for m in RE_BTC.findall(msg.text):
                if _insert_entity(session, "bitcoin", m, linked_message_id=msg.id):
                    counts["BTC"] += 1
            for m in RE_ETH.findall(msg.text):
                if _insert_entity(session, "ethereum", m, linked_message_id=msg.id):
                    counts["ETH"] += 1
            for m in RE_UAE_ANY.findall(msg.text):
                if _insert_entity(session, "foreign_number", m, linked_message_id=msg.id):
                    counts["UAE"] += 1
            for m in RE_EMAIL_ANY.findall(msg.text):
                # RE_EMAIL_ANY returns only domain group if used directly; extract full matches via finditer
                pass
            for m in (match.group(0) for match in RE_EMAIL_ANY.finditer(msg.text)):
                if _insert_entity(session, "email", m, linked_message_id=msg.id):
                    counts["EMAIL"] += 1
        # Address field detections (sender/receiver may include UAE numbers)
        if msg.sender and RE_UAE_ANCHORED.match(msg.sender):
            if _insert_entity(session, "foreign_number", msg.sender, linked_message_id=msg.id):
                counts["UAE"] += 1
        if msg.receiver and RE_UAE_ANCHORED.match(msg.receiver):
            if _insert_entity(session, "foreign_number", msg.receiver, linked_message_id=msg.id):
                counts["UAE"] += 1
    session.commit()
    return counts


def detect_in_calls(session: Session) -> Dict[str, int]:
    counts = {"BTC": 0, "ETH": 0, "UAE": 0, "EMAIL": 0}
    for c in session.query(Call).all():
        if c.caller and RE_UAE_ANCHORED.match(c.caller):
            if _insert_entity(session, "foreign_number", c.caller, linked_call_id=c.id):
                counts["UAE"] += 1
        if c.callee and RE_UAE_ANCHORED.match(c.callee):
            if _insert_entity(session, "foreign_number", c.callee, linked_call_id=c.id):
                counts["UAE"] += 1
    session.commit()
    return counts


def detect_in_contacts(session: Session) -> Dict[str, int]:
    counts = {"BTC": 0, "ETH": 0, "UAE": 0, "EMAIL": 0}
    for ct in session.query(Contact).all():
        if ct.number and RE_UAE_ANCHORED.match(ct.number):
            # No direct FK to contacts in Entity; store unlinked
            if _insert_entity(session, "foreign_number", ct.number, linked_message_id=None, linked_call_id=None):
                counts["UAE"] += 1
        if ct.email and RE_EMAIL_ANCHORED.match(ct.email):
            if _insert_entity(session, "email", ct.email, linked_message_id=None, linked_call_id=None):
                counts["EMAIL"] += 1
    session.commit()
    return counts


def run_entity_detection(database_url: str = "sqlite:///forensic_data.db") -> None:
    engine, Session = init_db(database_url)
    session = Session()
    try:
        msg_counts = detect_in_messages(session)
        call_counts = detect_in_calls(session)
        contact_counts = detect_in_contacts(session)

        # Aggregate counts
        total_btc = msg_counts["BTC"] + call_counts["BTC"] + contact_counts["BTC"]
        total_eth = msg_counts["ETH"] + call_counts["ETH"] + contact_counts["ETH"]
        total_uae = msg_counts["UAE"] + call_counts["UAE"] + contact_counts["UAE"]
        total_email = msg_counts["EMAIL"] + call_counts["EMAIL"] + contact_counts["EMAIL"]

        print(f"BTC: {total_btc} found | ETH: {total_eth} found | UAE Numbers: {total_uae} found | Emails: {total_email} found")
    finally:
        session.close()


if __name__ == "__main__":
    run_entity_detection()
