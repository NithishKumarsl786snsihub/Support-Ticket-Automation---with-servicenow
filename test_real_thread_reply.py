"""
Test Real Thread Reply with Actual Thread IDs
Tests the fixed thread reply functionality with real data from Google Chat
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

async def test_real_thread_reply():
    """Test thread reply with real thread IDs from Google Chat space"""
    
    print("=" * 60)
    print("TESTING REAL THREAD REPLY WITH ACTUAL THREAD IDs")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize credentials and APIs
        credentials_manager = CredentialsManager()
        google_chat = GoogleChatAPI(credentials_manager.google_credentials)
        
        print("✅ Components initialized")
        
        # Real thread data from Google Chat space
        real_space_id = "AAQAWaIEuf4"
        real_thread_id = "kLQ-IX3e9cs"  # Just the thread ID part
        real_message_id = "kLQ-IX3e9cs.kLQ-IX3e9cs"
        
        print(f"🧪 Testing with REAL data:")
        print(f"   Space ID: {real_space_id}")
        print(f"   Thread ID: {real_thread_id}")
        print(f"   Message ID: {real_message_id}")
        
        # Test message
        test_message = f"""
🧪 **Real Thread Reply Test - FIXED VERSION**

This is a test of the **FIXED** thread reply functionality using the correct Google Chat API approach.

**Test Details:**
- Space ID: {real_space_id}
- Thread ID: {real_thread_id}
- Message ID: {real_message_id}
- Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Method: Using 'thread' object in payload

**What Changed:**
✅ Using `thread: {{ "name": "spaces/{real_space_id}/threads/{real_thread_id}" }}` in payload
✅ Sending to space URL, not thread URL
✅ Proper thread ID extraction and formatting

If you see this message in the correct thread, the fix is working! 🎉
"""
        
        print(f"📝 Test message prepared (length: {len(test_message)} characters)")
        
        # Test 1: New thread reply method with real thread ID
        print(f"\n🔧 Test 1: Thread Reply with Real Thread ID")
        print(f"   Thread ID: {real_thread_id}")
        
        success1 = await google_chat.send_thread_reply(
            space_id=real_space_id,
            thread_id=real_thread_id,
            message=test_message
        )
        
        if success1:
            print("   ✅ Test 1 SUCCESS: Thread reply sent successfully")
        else:
            print("   ❌ Test 1 FAILED: Thread reply failed")
        
        # Test 2: Quote reply with real message ID
        print(f"\n🔧 Test 2: Quote Reply with Real Message ID")
        print(f"   Message ID: {real_message_id}")
        
        success2 = await google_chat.send_quote_reply(
            space_id=real_space_id,
            quoted_message_id=real_message_id,
            message=f"Quote reply test: {test_message}"
        )
        
        if success2:
            print("   ✅ Test 2 SUCCESS: Quote reply sent successfully")
        else:
            print("   ❌ Test 2 FAILED: Quote reply failed")
        
        # Test 3: Fallback method with real data
        print(f"\n🔧 Test 3: Fallback Method with Real Data")
        print(f"   Testing complete fallback chain")
        
        success3 = await google_chat.send_message_with_fallback(
            space_id=real_space_id,
            thread_id=real_thread_id,
            message=f"Fallback test: {test_message}",
            original_message_id=real_message_id
        )
        
        if success3:
            print("   ✅ Test 3 SUCCESS: Fallback method worked")
        else:
            print("   ❌ Test 3 FAILED: All fallback attempts failed")
        
        # Test 4: Space message (control test)
        print(f"\n🔧 Test 4: Space Message (Control Test)")
        print(f"   Space ID: {real_space_id}")
        
        success4 = await google_chat.send_message(
            space_id=real_space_id,
            thread_id=None,
            message=f"Space message test: {test_message}"
        )
        
        if success4:
            print("   ✅ Test 4 SUCCESS: Space message sent")
        else:
            print("   ❌ Test 4 FAILED: Space message failed")
        
        # Summary
        print(f"\n" + "=" * 60)
        print("REAL THREAD REPLY TEST RESULTS")
        print("=" * 60)
        print(f"Test 1 (Thread Reply): {'✅ PASS' if success1 else '❌ FAIL'}")
        print(f"Test 2 (Quote Reply): {'✅ PASS' if success2 else '❌ FAIL'}")
        print(f"Test 3 (Fallback Chain): {'✅ PASS' if success3 else '❌ FAIL'}")
        print(f"Test 4 (Space Message): {'✅ PASS' if success4 else '❌ FAIL'}")
        
        # Analysis
        if success1 and success2:
            print("\n🎉 EXCELLENT: Both thread reply and quote reply are working!")
            print("The Google Chat API thread object approach is working correctly.")
            print("Thread replies should now work in the production system.")
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
        
        print(f"\n🔧 NEXT STEPS:")
        if success1 and success2:
            print("   1. ✅ Thread replies are working - deploy to production")
            print("   2. ✅ Monitor logs for successful thread replies")
            print("   3. ✅ Test with actual support requests")
        else:
            print("   1. 🔧 Fix remaining issues based on test results")
            print("   2. 🔧 Update Google Cloud Console settings if needed")
            print("   3. 🔧 Test again until all methods work")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_thread_reply())
