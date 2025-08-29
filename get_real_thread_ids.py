"""
Get Real Thread IDs from Google Chat Space
Fetches actual thread IDs from your space for testing thread replies
"""

import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

from api.google_chat import GoogleChatAPI
from utils.credentials import CredentialsManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_real_thread_ids():
    """Get real thread IDs from the Google Chat space"""
    
    print("=" * 60)
    print("GETTING REAL THREAD IDs FROM GOOGLE CHAT SPACE")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize credentials and APIs
        credentials_manager = CredentialsManager()
        google_chat = GoogleChatAPI(credentials_manager.google_credentials)
        
        print("✅ Components initialized")
        
        # Get space ID from credentials
        space_id = credentials_manager.google_credentials['space_id']
        print(f"📋 Space ID: {space_id}")
        
        # Get messages from the last 24 hours
        since = datetime.now() - timedelta(hours=24)
        print(f"📅 Fetching messages since: {since.isoformat()}")
        
        # Fetch messages
        messages = await google_chat.get_space_messages(space_id, since)
        print(f"📨 Found {len(messages)} messages")
        
        # Analyze messages for thread information
        thread_messages = []
        space_messages = []
        
        for msg in messages:
            if msg.thread_id and msg.thread_id != space_id:
                thread_messages.append(msg)
            else:
                space_messages.append(msg)
        
        print(f"\n📊 Message Analysis:")
        print(f"   Thread messages: {len(thread_messages)}")
        print(f"   Space messages: {len(space_messages)}")
        
        # Display thread messages with their IDs
        if thread_messages:
            print(f"\n🧵 THREAD MESSAGES (for testing thread replies):")
            print("=" * 60)
            
            for i, msg in enumerate(thread_messages[:10], 1):  # Show first 10
                print(f"\n{i}. Thread Message:")
                print(f"   Message ID: {msg.message_id}")
                print(f"   Thread ID: {msg.thread_id}")
                print(f"   Sender: {msg.user_name}")
                print(f"   Time: {msg.timestamp}")
                print(f"   Content: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
                print(f"   User Email: {msg.user_email or 'Not available'}")
                print("-" * 40)
        else:
            print("\n⚠️  No thread messages found in the last 24 hours")
            print("   This means all messages are in the main space")
            print("   Thread replies will only work when there are actual threads")
        
        # Display space messages
        if space_messages:
            print(f"\n💬 SPACE MESSAGES (for testing space replies):")
            print("=" * 60)
            
            for i, msg in enumerate(space_messages[:5], 1):  # Show first 5
                print(f"\n{i}. Space Message:")
                print(f"   Message ID: {msg.message_id}")
                print(f"   Thread ID: {msg.thread_id}")
                print(f"   Sender: {msg.user_name}")
                print(f"   Time: {msg.timestamp}")
                print(f"   Content: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
                print(f"   User Email: {msg.user_email or 'Not available'}")
                print("-" * 40)
        
        # Create test data for thread reply testing
        if thread_messages:
            test_thread = thread_messages[0]  # Use first thread message
            print(f"\n🧪 TEST DATA FOR THREAD REPLY TESTING:")
            print("=" * 60)
            print(f"Test Space ID: {space_id}")
            print(f"Test Thread ID: {test_thread.thread_id}")
            print(f"Test Message ID: {test_thread.message_id}")
            print(f"Test Message Content: {test_thread.content[:50]}...")
            
            # Create test script content
            test_script_content = f'''
# Test with real thread data
test_space_id = "{space_id}"
test_thread_id = "{test_thread.thread_id}"
test_message_id = "{test_thread.message_id}"

# Use these in your thread reply tests
'''
            print(f"\n📝 Test script variables:")
            print(test_script_content)
            
            # Save test data to file
            with open("real_thread_test_data.py", "w") as f:
                f.write(f'''"""
Real Thread Test Data
Generated from actual Google Chat space
"""

# Real thread data for testing
REAL_SPACE_ID = "{space_id}"
REAL_THREAD_ID = "{test_thread.thread_id}"
REAL_MESSAGE_ID = "{test_thread.message_id}"
REAL_MESSAGE_CONTENT = """{test_thread.content}"""

# Test message for thread replies
TEST_REPLY_MESSAGE = f"""
🧪 **Real Thread Reply Test**

This is a test reply to a real thread in your Google Chat space.

**Thread Details:**
- Original Message: {test_thread.content[:50]}...
- Thread ID: {test_thread.thread_id}
- Message ID: {test_thread.message_id}
- Sender: {test_thread.user_name}

If you see this message in the correct thread, thread replies are working! 🎉
"""
''')
            
            print(f"✅ Test data saved to: real_thread_test_data.py")
        
        # Recommendations
        print(f"\n📋 RECOMMENDATIONS:")
        if thread_messages:
            print("   ✅ You have thread messages - thread replies should work")
            print("   📝 Use the test data above for thread reply testing")
            print("   🔧 Update your test scripts with real thread IDs")
        else:
            print("   ⚠️  No thread messages found - create some threads first")
            print("   💡 Reply to existing messages to create threads")
            print("   🔧 Test with space messages until threads are available")
        
        print(f"\n🔧 NEXT STEPS:")
        print("   1. Use the real thread IDs for testing")
        print("   2. Run thread reply tests with actual data")
        print("   3. Monitor logs for successful thread replies")
        print("   4. Configure Google Cloud Console if needed")
        
    except Exception as e:
        print(f"❌ Error getting thread IDs: {e}")
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_real_thread_ids())
