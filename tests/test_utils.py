"""
Test Utilities for Support Ticket Automation System
"""

import time
import asyncio
from datetime import datetime
from typing import List

from api.google_chat import SupportMessage
from main import SupportTicketAutomation

class TestDataGenerator:
    """Generate test data for system validation"""
    
    @staticmethod
    def create_test_message(content: str, user_name: str = "Test User") -> SupportMessage:
        """Create a test support message"""
        return SupportMessage(
            message_id=f"test_{int(time.time())}",
            thread_id="test_thread",
            user_id="test_user_123",
            user_name=user_name,
            content=content,
            timestamp=datetime.now(),
            space_id="test_space"
        )
    
    @staticmethod
    def get_test_scenarios() -> List[SupportMessage]:
        """Get various test scenarios"""
        scenarios = [
            "My computer won't start and I have an important presentation in 1 hour!",
            "I can't access the VPN and need to work from home",
            "The email server seems to be down - not receiving emails",
            "Password reset request for my account",
            "Software installation help needed for Adobe Creative Suite",
            "Printer in conference room B is not working",
            "Need help setting up dual monitors on my workstation",
            "WiFi keeps disconnecting every few minutes",
            "Can't login to Salesforce - getting error message",
            "Request for new user account for John Doe starting Monday"
        ]
        
        return [TestDataGenerator.create_test_message(content) for content in scenarios]

async def run_test_workflow():
    """Run test workflow with sample data"""
    
    print("🧪 Running Test Workflow")
    print("=" * 50)
    
    # Create test messages
    test_messages = TestDataGenerator.get_test_scenarios()
    
    # Initialize automation system
    automation = SupportTicketAutomation()
    
    # Run workflow with test data
    result = await automation.run_workflow(test_messages)
    
    print("\n✅ Test completed successfully!")
    return result
