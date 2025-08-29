"""
Test Fixed Thread Reply Functionality
Tests the new thread reply and quote reply methods
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

async def test_fixed_thread_reply():
    """Test the new thread reply and quote reply methods"""
    
    print("=" * 60)
    print("TESTING FIXED THREAD REPLY FUNCTIONALITY")
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
        test_thread_id = "2n6iu_9NxA0"  # Just the thread ID part
        test_message_id = "spaces/AAQAWaIEuf4/threads/2n6iu_9NxA0/messages/abc123"
        
        print(f"🧪 Testing with:")
        print(f"   Space ID: {test_space_id}")
        print(f"   Thread ID: {test_thread_id}")
        print(f"   Message ID: {test_message_id}")
        
        # Test message
        test_message = f"""
🧪 **Fixed Thread Reply Test**

This is a test of the new thread reply functionality.

**Test Details:**
- Space ID: {test_space_id}
- Thread ID: {test_thread_id}
- Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Purpose: Testing fixed thread reply methods

If you see this message in the correct thread, the fix is working! 🎉
"""
        
        print(f"📝 Test message prepared (length: {len(test_message)} characters)")
        
        # Test 1: New thread reply method
        print(f"\n🔧 Test 1: New Thread Reply Method")
        print(f"   Thread ID: {test_thread_id}")
        
        success1 = await google_chat.send_thread_reply(
            space_id=test_space_id,
            thread_id=test_thread_id,
            message=test_message
        )
        
        if success1:
            print("   ✅ Test 1 SUCCESS: Thread reply sent successfully")
        else:
            print("   ❌ Test 1 FAILED: Thread reply failed")
        
        # Test 2: New quote reply method
        print(f"\n🔧 Test 2: New Quote Reply Method")
        print(f"   Message ID: {test_message_id}")
        
        success2 = await google_chat.send_quote_reply(
            space_id=test_space_id,
            quoted_message_id=test_message_id,
            message=f"Quote reply test: {test_message}"
        )
        
        if success2:
            print("   ✅ Test 2 SUCCESS: Quote reply sent successfully")
        else:
            print("   ❌ Test 2 FAILED: Quote reply failed")
        
        # Test 3: Fallback method with new methods
        print(f"\n🔧 Test 3: Fallback Method with New Methods")
        print(f"   Testing complete fallback chain")
        
        success3 = await google_chat.send_message_with_fallback(
            space_id=test_space_id,
            thread_id=test_thread_id,
            message=f"Fallback test: {test_message}",
            original_message_id=test_message_id
        )
        
        if success3:
            print("   ✅ Test 3 SUCCESS: Fallback method worked")
        else:
            print("   ❌ Test 3 FAILED: All fallback attempts failed")
        
        # Test 4: Space message (should always work)
        print(f"\n🔧 Test 4: Space Message (Control Test)")
        print(f"   Space ID: {test_space_id}")
        
        success4 = await google_chat.send_message(
            space_id=test_space_id,
            thread_id=None,
            message=f"Space message test: {test_message}"
        )
        
        if success4:
            print("   ✅ Test 4 SUCCESS: Space message sent")
        else:
            print("   ❌ Test 4 FAILED: Space message failed")
        
        # Summary
        print(f"\n" + "=" * 60)
        print("FIXED THREAD REPLY TEST RESULTS")
        print("=" * 60)
        print(f"Test 1 (Thread Reply): {'✅ PASS' if success1 else '❌ FAIL'}")
        print(f"Test 2 (Quote Reply): {'✅ PASS' if success2 else '❌ FAIL'}")
        print(f"Test 3 (Fallback Chain): {'✅ PASS' if success3 else '❌ FAIL'}")
        print(f"Test 4 (Space Message): {'✅ PASS' if success4 else '❌ FAIL'}")
        
        # Analysis
        if success1 and success2:
            print("\n🎉 EXCELLENT: Both thread reply and quote reply are working!")
            print("The Google Chat API permissions and methods are properly configured.")
        elif success1:
            print("\n⚠️  PARTIAL SUCCESS: Thread reply works, quote reply needs attention")
            print("The basic thread functionality is working, but quote replies may need additional configuration.")
        elif success2:
            print("\n⚠️  PARTIAL SUCCESS: Quote reply works, thread reply needs attention")
            print("Quote replies are working, but direct thread replies may need additional configuration.")
        elif success3:
            print("\n⚠️  FALLBACK SUCCESS: At least one method in the fallback chain works")
            print("The system can send notifications, but not through the preferred thread/quote methods.")
        elif success4:
            print("\n⚠️  BASIC SUCCESS: Only space messages work")
            print("The bot can send messages to the space, but thread/quote functionality needs configuration.")
        else:
            print("\n❌ ALL TESTS FAILED")
            print("There are fundamental issues with the Google Chat API configuration.")
        
        # Recommendations
        print(f"\n📋 RECOMMENDATIONS:")
        if not success1:
            print("   - Check Google Cloud Console for Chat API permissions")
            print("   - Verify service account has 'Chat Bot' and 'Chat API User' roles")
            print("   - Ensure Google Chat API is enabled in the project")
        if not success2:
            print("   - Check quote reply payload format")
            print("   - Verify message ID format and thread extraction logic")
        if not success3:
            print("   - Review fallback chain implementation")
            print("   - Check error handling and logging")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_fixed_thread_reply())
