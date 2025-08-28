"""
Debug script to test ServiceNow connection with detailed error reporting
"""

import asyncio
import sys
import os
import logging
import traceback
from datetime import datetime
import httpx

# Add parent directory to path to import from project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.credentials import CredentialsManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_servicenow_connection_debug():
    """Test ServiceNow connection with detailed error reporting"""
    
    print("\n🧪 Testing ServiceNow Connection (Debug Mode)")
    print("=" * 60)
    
    try:
        # Initialize credentials
        credentials_manager = CredentialsManager()
        servicenow_credentials = credentials_manager.servicenow_credentials
        
        # Print connection info
        print(f"ServiceNow Instance URL: {servicenow_credentials.get('instance_url')}")
        print(f"Username: {servicenow_credentials.get('username')}")
        
        # Test basic connection to ServiceNow
        instance_url = servicenow_credentials.get('instance_url')
        username = servicenow_credentials.get('username')
        password = servicenow_credentials.get('password')
        
        if not instance_url or not username or not password:
            print("\n❌ Missing ServiceNow credentials in .env file")
            return False
        
        print("\nTesting basic connection to ServiceNow...")
        
        # Test endpoint
        test_url = f"{instance_url}/api/now/table/incident?sysparm_limit=1"
        
        async with httpx.AsyncClient(auth=(username, password), timeout=30.0) as client:
            try:
                print(f"Sending GET request to: {test_url}")
                response = await client.get(test_url)
                
                print(f"Response status code: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ Successfully connected to ServiceNow!")
                    print("\nResponse data:")
                    print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
                    
                    # Try creating a test incident
                    print("\nTrying to create a test incident...")
                    
                    create_url = f"{instance_url}/api/now/table/incident"
                    payload = {
                        'short_description': "Test Ticket from Support Automation System",
                        'description': "This is a test ticket created to verify the connection to ServiceNow.",
                        'priority': "2",
                        'category': "software",
                        'subcategory': "system access",
                        'urgency': "2"
                    }
                    
                    create_response = await client.post(create_url, json=payload)
                    print(f"Create response status code: {create_response.status_code}")
                    
                    if create_response.status_code in (200, 201):
                        result = create_response.json()
                        print("\n✅ ServiceNow ticket created successfully!")
                        print(f"Ticket Number: {result['result'].get('number')}")
                        print(f"Ticket ID: {result['result'].get('sys_id')}")
                        print(f"\nYou can view this ticket at: {instance_url}/nav_to.do?uri=incident.do?sys_id={result['result'].get('sys_id')}")
                    else:
                        print("\n❌ Failed to create ticket")
                        print(f"Response: {create_response.text}")
                else:
                    print("\n❌ Failed to connect to ServiceNow")
                    print(f"Response: {response.text}")
            
            except httpx.RequestError as e:
                print(f"\n❌ Request error: {str(e)}")
            except Exception as e:
                print(f"\n❌ Unexpected error: {str(e)}")
                traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_servicenow_connection_debug())
