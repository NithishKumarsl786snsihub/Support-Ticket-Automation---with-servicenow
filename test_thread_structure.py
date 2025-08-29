"""
Test Google Chat Thread Structure
Understanding how to properly send replies to threads
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

async def test_thread_structure():
    """Test different approaches to understand thread structure"""
    
    print("=" * 60)
    print("TESTING GOOGLE CHAT THREAD STRUCTURE")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize credentials and APIs
        credentials_manager = CredentialsManager()
        google_chat = GoogleChatAPI(credentials_manager.google_credentials)
        
        print("✅ Components initialized")
        
        # Test data
        test_space_id = "spaces/AAQAWaIEuf4"
        
        print(f"🧪 Testing with Space ID: {test_space_id}")
        
        # Test message
        test_message = f"""
🧪 **Thread Structure Test**

This is a test message to understand how Google Chat threads work.

**Test Details:**
- Space ID: {test_space_id}
- Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Purpose: Understanding thread structure

This message should appear in the space and help us understand the threading mechanism.
"""
        
        print(f"📝 Test message prepared (length: {len(test_message)} characters)")
        
        # Test 1: Send to space (this should work)
        print(f"\n🔧 Test 1: Sending to space")
        print(f"   Space ID: {test_space_id}")
        
        success1 = await google_chat.send_message(
            space_id=test_space_id,
            thread_id=None,  # Send to space
            message=test_message
        )
        
        if success1:
            print("   ✅ Test 1 SUCCESS: Message sent to space")
            print("   💡 This confirms the bot can post to the space")
        else:
            print("   ❌ Test 1 FAILED: Could not send to space")
            return
        
        # Test 2: Try to get space information
        print(f"\n🔧 Test 2: Getting space information")
        try:
            # This would help us understand the space structure
            print("   📋 Note: Google Chat API doesn't provide direct space info endpoint")
            print("   💡 We need to work with the thread information from messages")
        except Exception as e:
            print(f"   ❌ Error getting space info: {e}")
        
        # Test 3: Try different thread ID formats
        print(f"\n🔧 Test 3: Testing different thread ID formats")
        
        # Format 1: Just the thread ID part
        thread_id_1 = "2n6iu_9NxA0"
        print(f"   Format 1: {thread_id_1}")
        
        success3a = await google_chat.send_message(
            space_id=test_space_id,
            thread_id=thread_id_1,
            message=f"Test reply to thread {thread_id_1}"
        )
        
        if success3a:
            print("   ✅ Format 1 SUCCESS")
        else:
            print("   ❌ Format 1 FAILED")
        
        # Format 2: With threads/ prefix
        thread_id_2 = f"threads/{thread_id_1}"
        print(f"   Format 2: {thread_id_2}")
        
        success3b = await google_chat.send_message(
            space_id=test_space_id,
            thread_id=thread_id_2,
            message=f"Test reply to thread {thread_id_2}"
        )
        
        if success3b:
            print("   ✅ Format 2 SUCCESS")
        else:
            print("   ❌ Format 2 FAILED")
        
        # Format 3: Full path but simplified
        thread_id_3 = f"spaces/AAQAWaIEuf4/threads/{thread_id_1}"
        print(f"   Format 3: {thread_id_3}")
        
        success3c = await google_chat.send_message(
            space_id=test_space_id,
            thread_id=thread_id_3,
            message=f"Test reply to thread {thread_id_3}"
        )
        
        if success3c:
            print("   ✅ Format 3 SUCCESS")
        else:
            print("   ❌ Format 3 FAILED")
        
        # Summary
        print(f"\n" + "=" * 60)
        print("THREAD STRUCTURE TEST RESULTS")
        print("=" * 60)
        print(f"Space Messages: {'✅ WORKING' if success1 else '❌ FAILED'}")
        print(f"Thread Format 1: {'✅ WORKING' if success3a else '❌ FAILED'}")
        print(f"Thread Format 2: {'✅ WORKING' if success3b else '❌ FAILED'}")
        print(f"Thread Format 3: {'✅ WORKING' if success3c else '❌ FAILED'}")
        
        if success3a or success3b or success3c:
            print("\n🎉 SUCCESS: Found working thread format!")
            if success3a:
                print("   Working format: Just thread ID (e.g., '2n6iu_9NxA0')")
            elif success3b:
                print("   Working format: With threads/ prefix (e.g., 'threads/2n6iu_9NxA0')")
            elif success3c:
                print("   Working format: Full path (e.g., 'spaces/XXX/threads/YYY')")
        else:
            print("\n❌ ALL THREAD FORMATS FAILED")
            print("   The issue might be:")
            print("   - Bot permissions for threads")
            print("   - Thread ID format from Google Chat")
            print("   - API endpoint restrictions")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_thread_structure())
