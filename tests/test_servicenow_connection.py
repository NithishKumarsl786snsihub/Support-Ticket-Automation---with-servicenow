"""
Test script to verify ServiceNow connection and create a real ticket
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path to import from project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.credentials import CredentialsManager
from api.servicenow import ServiceNowAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_servicenow_connection():
    """Test ServiceNow connection and create a real ticket"""
    
    print("\n🧪 Testing ServiceNow Connection")
    print("=" * 60)
    
    try:
        # Initialize credentials
        credentials_manager = CredentialsManager()
        servicenow_credentials = credentials_manager.servicenow_credentials
        
        # Print connection info
        print(f"ServiceNow Instance URL: {servicenow_credentials.get('instance_url')}")
        print(f"Username: {servicenow_credentials.get('username')}")
        
        # Initialize ServiceNow API
        servicenow_api = ServiceNowAPI(servicenow_credentials)
        
        # Create a test ticket
        ticket_data = {
            'title': "Test Ticket from Support Automation System",
            'description': "This is a test ticket created to verify the connection to ServiceNow.",
            'priority': "2 - High",
            'category': "Software",
            'subcategory': "System Access",
            'urgency': "2",
            'assignment_group': "IT Support"
        }
        
        print("\nCreating test ticket in ServiceNow...")
        ticket = await servicenow_api.create_incident(ticket_data)
        
        print("\n✅ ServiceNow ticket created successfully!")
        print(f"Ticket Number: {ticket.number}")
        print(f"Ticket ID: {ticket.sys_id}")
        print(f"Status: {ticket.state}")
        print(f"Created On: {ticket.created_on}")
        print(f"\nYou can view this ticket at: {servicenow_credentials.get('instance_url')}/nav_to.do?uri=incident.do?sys_id={ticket.sys_id}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ServiceNow connection failed: {str(e)}")
        print("\nPossible issues:")
        print("1. ServiceNow instance URL is incorrect")
        print("2. Username or password is incorrect")
        print("3. ServiceNow instance is not accessible from your network")
        print("4. ServiceNow API permissions are not configured correctly")
        
        return False

if __name__ == "__main__":
    asyncio.run(test_servicenow_connection())
