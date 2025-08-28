"""
Test script to simulate a Google Chat message and create a ServiceNow ticket
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path to import from project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.google_chat import SupportMessage
from main import SupportTicketAutomation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_specific_message():
    """Test with a specific message from the screenshot"""
    
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
    
    print("\n🧪 Testing with specific message from screenshot")
    print("=" * 60)
    print(f"Message: {test_message.content}")
    print(f"From: {test_message.user_name}")
    print(f"Space ID: {test_message.space_id}")
    print("=" * 60)
    
    # Initialize automation system
    automation = SupportTicketAutomation()
    
    # Run workflow with test message
    result = await automation.run_workflow([test_message])
    
    print("\n✅ Test completed!")
    return result

if __name__ == "__main__":
    asyncio.run(test_specific_message())
