"""
Process a real message and create an actual ServiceNow ticket
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path to import from project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.google_chat import SupportMessage
from utils.credentials import CredentialsManager
from api.servicenow import ServiceNowAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_real_message():
    """Process the user's message and create a real ServiceNow ticket"""
    
    # Create a message object from the screenshot
    message = SupportMessage(
        message_id=f"real_{int(datetime.now().timestamp())}",
        thread_id="real_thread",
        user_id="user_123",
        user_name="Nithish Kumar S L",
        content="i need a support in the system support @pf 2 please check and recover soon and resolve it i have meeting with in a hour",
        timestamp=datetime.now(),
        space_id="AAQAWaIEuf4"
    )
    
    print("\n🔄 Processing Real Message")
    print("=" * 60)
    print(f"Message: {message.content}")
    print(f"From: {message.user_name}")
    print("=" * 60)
    
    # Initialize credentials and ServiceNow API
    credentials_manager = CredentialsManager()
    servicenow_api = ServiceNowAPI(credentials_manager.servicenow_credentials)
    
    # Manually process the message (since we don't have a valid Gemini API key)
    print("\n1️⃣ Manual Classification")
    print("✅ Message classified as support request")
    
    # Create ticket data
    ticket_data = {
        'title': "System Support Request - Urgent Meeting Preparation",
        'description': f"User needs urgent support with system issue before an upcoming meeting within the hour.\n\nOriginal message: {message.content}",
        'priority': "2",  # High
        'category': "software",
        'subcategory': "system access",
        'urgency': "2",
        'assignment_group': "IT Support"
    }
    
    print("\n2️⃣ Creating Real ServiceNow Ticket")
    try:
        ticket = await servicenow_api.create_incident(ticket_data)
        
        print("\n✅ ServiceNow ticket created successfully!")
        print(f"Ticket Number: {ticket.number}")
        print(f"Ticket ID: {ticket.sys_id}")
        print(f"Status: {ticket.state}")
        
        # Provide link to view the ticket
        instance_url = credentials_manager.servicenow_credentials.get('instance_url')
        print(f"\nYou can view this ticket at: {instance_url}/nav_to.do?uri=incident.do?sys_id={ticket.sys_id}")
        
        print("\n3️⃣ What would happen next:")
        print("- A notification would be sent back to your Google Chat")
        print("- The ticket would be tracked for status changes")
        print("- Updates would be sent to your Google Chat thread")
        
    except Exception as e:
        print(f"\n❌ Failed to create ServiceNow ticket: {str(e)}")
    
    return True

if __name__ == "__main__":
    asyncio.run(process_real_message())
