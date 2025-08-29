"""
Test Thread Reply Functionality
Tests sending replies to existing Google Chat threads
"""

import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

from api.google_chat import GoogleChatAPI
from utils.credentials import CredentialsManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_thread_reply():
    """Test sending a reply to an existing thread"""
    
    print("=" * 60)
    print("TESTING THREAD REPLY FUNCTIONALITY")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize credentials and APIs
        credentials_manager = CredentialsManager()
        google_chat = GoogleChatAPI(credentials_manager.google_credentials)
        
        print("✅ Components initialized")
        
        # Test data from the logs
        test_space_id = "spaces/AAQAWaIEuf4"
        test_thread_id = "spaces/AAQAWaIEuf4/threads/2n6iu_9NxA0"
        
        print(f"🧪 Testing with:")
        print(f"   Space ID: {test_space_id}")
        print(f"   Thread ID: {test_thread_id}")
        
        # Test message
        test_message = """
🧪 **Test Reply Message**

This is a test reply to verify that thread notifications are working correctly.

**Test Details:**
- Space ID: {space_id}
- Thread ID: {thread_id}
- Timestamp: {timestamp}

If you see this message, the thread reply functionality is working! 🎉
""".format(
            space_id=test_space_id,
            thread_id=test_thread_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        print(f"📝 Test message prepared (length: {len(test_message)} characters)")
        
        # Test 1: Send to the exact thread ID from logs
        print(f"\n🔧 Test 1: Sending to exact thread ID from logs")
        print(f"   Thread ID: {test_thread_id}")
        
        success1 = await google_chat.send_message(
            space_id=test_space_id,
            thread_id=test_thread_id,
            message=test_message
        )
        
        if success1:
            print("   ✅ Test 1 SUCCESS: Message sent to exact thread ID")
        else:
            print("   ❌ Test 1 FAILED: Could not send to exact thread ID")
        
        # Test 2: Send to extracted thread ID (simulating the current logic)
        print(f"\n🔧 Test 2: Sending to extracted thread ID (current logic)")
        extracted_thread_id = test_thread_id.split('/')[-1]  # Extract just '2n6iu_9NxA0'
        print(f"   Extracted Thread ID: {extracted_thread_id}")
        
        success2 = await google_chat.send_message(
            space_id=test_space_id,
            thread_id=extracted_thread_id,
            message=test_message
        )
        
        if success2:
            print("   ✅ Test 2 SUCCESS: Message sent to extracted thread ID")
        else:
            print("   ❌ Test 2 FAILED: Could not send to extracted thread ID")
        
        # Test 3: Send to space (fallback)
        print(f"\n🔧 Test 3: Sending to space (fallback)")
        print(f"   Space ID: {test_space_id}")
        
        success3 = await google_chat.send_message(
            space_id=test_space_id,
            thread_id=None,  # Send to space
            message=test_message
        )
        
        if success3:
            print("   ✅ Test 3 SUCCESS: Message sent to space")
        else:
            print("   ❌ Test 3 FAILED: Could not send to space")
        
        # Summary
        print(f"\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Test 1 (Exact Thread ID): {'✅ PASS' if success1 else '❌ FAIL'}")
        print(f"Test 2 (Extracted Thread ID): {'✅ PASS' if success2 else '❌ PASS'}")
        print(f"Test 3 (Space Fallback): {'✅ PASS' if success3 else '❌ FAIL'}")
        
        if success1:
            print("\n🎉 SUCCESS: Thread replies are working!")
            print("The issue was likely in the thread ID processing logic.")
        elif success2:
            print("\n⚠️  PARTIAL SUCCESS: Extracted thread ID works")
            print("The issue is in how the full thread path is being handled.")
        elif success3:
            print("\n⚠️  FALLBACK SUCCESS: Space messages work")
            print("The issue is with thread ID handling.")
        else:
            print("\n❌ ALL TESTS FAILED")
            print("There's a fundamental issue with the Google Chat API integration.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_thread_reply())
