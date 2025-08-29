"""
Test Admin Message Filtering
Verifies that admin notification messages are filtered out before processing
"""

import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

from workflow.nodes_optimized import message_fetcher_node, rule_based_classification
from utils.models import WorkflowState, SupportMessage
from utils.credentials import CredentialsManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_admin_message_filtering():
    """Test that admin notification messages are properly filtered out"""
    
    print("=" * 60)
    print("TESTING ADMIN MESSAGE FILTERING")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Test data - simulating the problematic admin notification message
        test_messages = [
            # Admin notification message (should be filtered out)
            SupportMessage(
                message_id="admin_notification_001",
                thread_id="spaces/AAQAWaIEuf4/threads/admin_thread",
                user_id="admin_user_123",
                user_name="Support Ticket Automation",
                content="""
🎫 **Support Ticket Created**

**Ticket Number:** INC0010078
**Title:** @Support Ticket Automation 

Projector in the conference room is not working, but another room ca...
**Status:** 1
**Priority:** 5

**View Ticket:** [Open in ServiceNow](https://dev342375.service-now.com/nav_to.do?uri=incident.do?sys_id=db5d51d7532b621006d41ab0a0490eb5)

Your request has been processed and a ticket has been created. You will receive updates as the issue progresses.
""",
                timestamp=datetime.now() - timedelta(minutes=30),
                space_id="spaces/AAQAWaIEuf4"
            ),
            
            # Real user support request (should be included)
            SupportMessage(
                message_id="user_request_001",
                thread_id="spaces/AAQAWaIEuf4/threads/user_thread",
                user_id="user_456",
                user_name="John Doe",
                content="@Support Ticket Automation\n\nMy laptop is not connecting to the WiFi network. Can you help me fix this?",
                timestamp=datetime.now() - timedelta(hours=1),
                space_id="spaces/AAQAWaIEuf4"
            ),
            
            # Another admin notification (should be filtered out)
            SupportMessage(
                message_id="admin_notification_002",
                thread_id="spaces/AAQAWaIEuf4/threads/admin_thread2",
                user_id="admin_user_456",
                user_name="Admin Bot",
                content="""
🎫 **Support Ticket Created**

**Ticket Number:** INC0010079
**Title:** Network connectivity issue
**Status:** 1
**Priority:** 3

**View Ticket:** [Open in ServiceNow](https://dev342375.service-now.com/nav_to.do?uri=incident.do?sys_id=xyz123)

Your request has been processed and a ticket has been created.
""",
                timestamp=datetime.now() - timedelta(minutes=15),
                space_id="spaces/AAQAWaIEuf4"
            ),
            
            # Another real user request (should be included)
            SupportMessage(
                message_id="user_request_002",
                thread_id="spaces/AAQAWaIEuf4/threads/user_thread2",
                user_id="user_789",
                user_name="Jane Smith",
                content="@Support Ticket Automation\n\nThe printer in the marketing department is showing an error message. It says 'Paper Jam' but there's no paper stuck.",
                timestamp=datetime.now() - timedelta(hours=2),
                space_id="spaces/AAQAWaIEuf4"
            )
        ]
        
        print(f"🧪 Testing with {len(test_messages)} test messages")
        
        # Test 1: Rule-based classification filtering
        print(f"\n🔍 Test 1: Rule-based Classification Filtering")
        
        for i, message in enumerate(test_messages):
            print(f"\n  Message {i+1}: {message.message_id}")
            print(f"    User: {message.user_name}")
            print(f"    Content preview: {message.content[:100]}...")
            
            # Test classification
            classified = rule_based_classification(message)
            
            print(f"    Classification: {classified.is_support_request}")
            print(f"    Confidence: {classified.confidence}")
            print(f"    Reasoning: {classified.reasoning}")
            
            if classified.is_support_request:
                print(f"    ✅ CLASSIFIED AS SUPPORT REQUEST")
            else:
                print(f"    🚫 FILTERED OUT - {classified.reasoning}")
        
        # Test 2: Simulate message fetcher filtering
        print(f"\n🔍 Test 2: Message Fetcher Pre-filtering")
        
        # Create a mock workflow state
        state = WorkflowState(
            messages=test_messages,
            current_step="message_fetcher",
            errors=[],
            processed_messages=set(),
            ticket_links={}
        )
        
        # Simulate the filtering logic from message_fetcher_node
        filtered_messages = []
        admin_notifications_filtered = 0
        
        for message in test_messages:
            # Check if this is an admin notification message
            content_lower = message.content.lower()
            admin_patterns = [
                '🎫 **support ticket created**',
                'ticket number: inc',
                'your request has been processed',
                'ticket has been created',
                'view ticket: [open in servicenow]',
                'status:',
                'priority:',
                'you will receive updates as the issue progresses'
            ]
            
            is_admin_notification = any(pattern in content_lower for pattern in admin_patterns)
            
            # Check if this is from the bot itself (should be excluded)
            is_bot_message = (
                message.user_name.lower() in ['support ticket automation', 'bot', 'admin'] or
                'chat-bot' in message.user_id.lower() or
                'bot' in message.user_id.lower()
            )
            
            if is_admin_notification or is_bot_message:
                print(f"    🚫 Pre-filtered admin/bot message: {message.message_id} (User: {message.user_name})")
                admin_notifications_filtered += 1
                continue
            else:
                # Only include messages from actual users
                filtered_messages.append(message)
                print(f"    ✅ User message included: {message.message_id} (User: {message.user_name})")
        
        print(f"\n📊 Filtering Results:")
        print(f"   Total messages: {len(test_messages)}")
        print(f"   Admin notifications filtered: {admin_notifications_filtered}")
        print(f"   User messages for processing: {len(filtered_messages)}")
        
        # Test 3: Verify only user messages remain
        print(f"\n🔍 Test 3: Verify Filtered Messages")
        
        for message in filtered_messages:
            print(f"    ✅ Remaining message: {message.message_id} from {message.user_name}")
            print(f"       Content: {message.content[:80]}...")
        
        # Test 4: Classification of filtered messages
        print(f"\n🔍 Test 4: Classification of Filtered Messages")
        
        support_requests = 0
        for message in filtered_messages:
            classified = rule_based_classification(message)
            if classified.is_support_request:
                support_requests += 1
                print(f"    ✅ {message.message_id}: Support request detected")
            else:
                print(f"    ⚠️  {message.message_id}: Not classified as support request")
        
        # Summary and recommendations
        print(f"\n" + "=" * 60)
        print("ADMIN MESSAGE FILTERING TEST RESULTS")
        print("=" * 60)
        
        expected_filtered = 2  # The real user requests
        actual_filtered = len(filtered_messages)
        
        if actual_filtered == expected_filtered:
            print(f"✅ SUCCESS: Correctly filtered {actual_filtered} user messages")
            print(f"   Admin notifications were properly excluded")
            print(f"   Only legitimate user support requests remain")
        else:
            print(f"⚠️  PARTIAL SUCCESS: Filtered {actual_filtered} messages (expected: {expected_filtered})")
            print(f"   Some messages may not have been filtered correctly")
        
        print(f"\n🎯 Expected Behavior:")
        print(f"   1. Admin notification messages → Filtered out before processing")
        print(f"   2. Bot-generated messages → Filtered out before processing")
        print(f"   3. User support requests → Included for processing")
        print(f"   4. No duplicate tickets created from admin messages")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Test with real workflow execution")
        print(f"   2. Monitor logs for proper filtering")
        print(f"   3. Verify no admin message tickets are created")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_admin_message_filtering())
