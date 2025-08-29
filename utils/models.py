"""
Data models for the Support Ticket Automation system
"""

from typing import List, Dict, Any, Optional, Set, TypedDict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class Priority(Enum):
    """Ticket priority levels"""
    CRITICAL = "1"
    HIGH = "2"
    MODERATE = "3"
    LOW = "4"
    PLANNING = "5"

class Category(Enum):
    """Ticket categories"""
    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    ACCESS = "access"
    EMAIL = "email"
    PRINTING = "printing"
    SECURITY = "security"
    OTHER = "other"

@dataclass
class SupportMessage:
    """Represents a support message from Google Chat"""
    message_id: str
    thread_id: str
    user_id: str
    user_name: str
    content: str
    timestamp: datetime
    space_id: str
    user_email: Optional[str] = None  # User's email address if available

@dataclass
class ClassifiedMessage:
    """Message that has been classified as a support request"""
    original_message: SupportMessage
    is_support_request: bool
    confidence: float
    reasoning: str

@dataclass
class TicketSummary:
    """Summary of a support ticket"""
    title: str
    description: str
    problem_statement: str
    user_impact: str
    urgency_level: str

@dataclass
class TicketCategory:
    """Categorized ticket information"""
    category: Category
    priority: Priority
    subcategory: str
    urgency: str
    assignment_group: str

@dataclass
class ServiceNowTicket:
    """Represents a ServiceNow incident ticket"""
    sys_id: str
    number: str
    state: str
    short_description: str
    description: str
    priority: str
    category: str
    assigned_to: str
    created_on: str
    updated_on: str

class WorkflowState(TypedDict, total=False):
    """State object for the LangGraph workflow (dict-like for item assignment)"""
    messages: List[SupportMessage]
    duplicate_messages: List[Dict[str, Any]]  # Messages identified as duplicates
    unique_messages: List[SupportMessage]  # Messages that are unique requests
    classified_messages: List[ClassifiedMessage]
    summarized_tickets: List[TicketSummary]
    categorized_tickets: List[TicketCategory]
    servicenow_tickets: List[Any]
    newly_created_tickets: List[Dict[str, Any]]  # Track newly created tickets for notifications
    notifications_sent: List[Dict[str, Any]]
    current_step: str
    errors: List[str]
    processed_messages: Set[str]
    ticket_links: Dict[str, str]
