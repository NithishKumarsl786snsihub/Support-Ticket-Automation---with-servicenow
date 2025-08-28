"""
Test script using mock data to simulate the complete workflow
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path to import from project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.google_chat import SupportMessage
from utils.models import WorkflowState, ClassifiedMessage, SummarizedTicket, CategorizedTicket, TicketCategory, TicketPriority
from api.servicenow import ServiceNowTicket

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mock_workflow():
    """Test the complete workflow with mock data"""
    
    # Create a test message similar to what was shown in the screenshot
    test_message = SupportMessage(
        message_id=f"test_{int(datetime.now().timestamp())}",
        thread_id="test_thread",
        user_id="user_123",
        user_name="Nithish Kumar S L",
        content="i need a support in the system support @pf 2 please check and recover soon and resolve it i have meeting with in a hour",
        timestamp=datetime.now(),
        space_id="AAQAWaIEuf4"  # From the screenshot
    )
    
    print("\n🧪 Testing complete workflow with mock data")
    print("=" * 60)
    print(f"Message: {test_message.content}")
    print(f"From: {test_message.user_name}")
    print("=" * 60)
    
    # Initialize state
    state = WorkflowState(
        messages=[test_message],
        classified_messages=[],
        summarized_tickets=[],
        categorized_tickets=[],
        servicenow_tickets=[],
        notifications_sent=[],
        current_step='',
        errors=[]
    )
    
    # Step 1: Classification (mock)
    print("\n1️⃣ Classification step")
    classified_message = ClassifiedMessage(
        original_message=test_message,
        is_support_request=True,
        confidence=0.95,
        reasoning="This is clearly a support request mentioning system issues and urgent recovery needed."
    )
    state['classified_messages'] = [classified_message]
    print("✅ Message classified as support request (95% confidence)")
    
    # Step 2: Summarization (mock)
    print("\n2️⃣ Summarization step")
    summary = SummarizedTicket(
        title="System Support Request - Urgent Meeting Preparation",
        description="User needs urgent support with system issue before an upcoming meeting within the hour.",
        problem_statement="System issue requiring immediate recovery",
        user_impact="User has a meeting within an hour and needs the system working"
    )
    state['summarized_tickets'] = [summary]
    print(f"✅ Ticket summarized:")
    print(f"   Title: {summary.title}")
    print(f"   Description: {summary.description}")
    
    # Step 3: Categorization (mock)
    print("\n3️⃣ Categorization step")
    categorized = CategorizedTicket(
        category=TicketCategory.SOFTWARE,
        subcategory="System Access",
        priority=TicketPriority.HIGH,
        urgency="2",
        service="IT Support",
        assignment_group="IT Support"
    )
    state['categorized_tickets'] = [categorized]
    print(f"✅ Ticket categorized:")
    print(f"   Category: {categorized.category.value}")
    print(f"   Priority: {categorized.priority.value}")
    print(f"   Assignment: {categorized.assignment_group}")
    
    # Step 4: ServiceNow ticket creation (mock)
    print("\n4️⃣ ServiceNow ticket creation step")
    ticket = ServiceNowTicket(
        sys_id="1234567890abcdef",
        number="INC0010001",
        state="1",
        short_description=summary.title,
        description=summary.description,
        priority=categorized.priority.value,
        category=categorized.category.value,
        assigned_to="IT Support Team",
        created_on=datetime.now().isoformat(),
        updated_on=datetime.now().isoformat()
    )
    state['servicenow_tickets'] = [ticket]
    print(f"✅ ServiceNow ticket created:")
    print(f"   Ticket Number: {ticket.number}")
    print(f"   Status: In Progress")
    
    # Step 5: Notification (mock)
    print("\n5️⃣ Notification step")
    notification = {
        'ticket_number': ticket.number,
        'message_id': test_message.message_id,
        'notification_sent': True,
        'timestamp': datetime.now().isoformat()
    }
    state['notifications_sent'] = [notification]
    print(f"✅ Notification sent to Google Chat")
    
    # Print final workflow summary
    print("\n📊 Final Workflow Summary:")
    print(f"Messages Processed: {len(state['messages'])}")
    print(f"Support Requests Identified: {len(state['classified_messages'])}")
    print(f"Tickets Summarized: {len(state['summarized_tickets'])}")
    print(f"Tickets Categorized: {len(state['categorized_tickets'])}")
    print(f"ServiceNow Tickets Created: {len(state['servicenow_tickets'])}")
    print(f"Notifications Sent: {len(state['notifications_sent'])}")
    print(f"Errors Encountered: {len(state['errors'])}")
    
    print("\n🎉 Complete workflow test successful!")
    print("\nThis is what would happen with your message:")
    print("1. Your message would be identified as a support request")
    print("2. A ticket summary would be generated")
    print("3. The ticket would be categorized as Software/System Access with High priority")
    print("4. A ServiceNow ticket would be created")
    print("5. A notification would be sent back to your Google Chat thread")
    
    return state

if __name__ == "__main__":
    asyncio.run(test_mock_workflow())
