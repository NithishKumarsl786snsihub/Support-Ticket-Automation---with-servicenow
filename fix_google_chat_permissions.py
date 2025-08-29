"""
Google Chat API Permission Fix
Helps configure proper permissions for thread replies and quote replies
"""

import os
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def check_google_chat_permissions():
    """Check current Google Chat API permissions and configuration"""
    
    print("=" * 60)
    print("GOOGLE CHAT API PERMISSION CHECK")
    print("=" * 60)
    
    # Load service account credentials
    service_account_file = "enduring-palace-469405-h2-ac55ef517000.json"
    
    if not os.path.exists(service_account_file):
        print(f"❌ Service account file not found: {service_account_file}")
        return False
    
    try:
        # Load credentials
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=[
                'https://www.googleapis.com/auth/chat.bot',
                'https://www.googleapis.com/auth/chat.spaces.bot',
                'https://www.googleapis.com/auth/chat.messages',
                'https://www.googleapis.com/auth/chat.threads'
            ]
        )
        
        print("✅ Service account credentials loaded")
        
        # Build Google Chat API service
        service = build('chat', 'v1', credentials=credentials)
        
        print("✅ Google Chat API service built")
        
        # Test basic API access
        try:
            # Try to get spaces (this tests basic permissions)
            spaces_response = service.spaces().list().execute()
            print(f"✅ Basic API access working - Found {len(spaces_response.get('spaces', []))} spaces")
            
            # Check if we can send messages
            print("\n🔍 Testing message sending permissions...")
            
            # Test space message (this should work)
            test_space_id = "spaces/AAQAWaIEuf4"  # Replace with your space ID
            
            test_message = {
                'text': '🧪 Testing Google Chat API permissions...'
            }
            
            try:
                # Test sending to space
                space_response = service.spaces().messages().create(
                    parent=test_space_id,
                    body=test_message
                ).execute()
                
                print("✅ Space message sending: WORKING")
                print(f"   Message ID: {space_response.get('name', 'Unknown')}")
                
            except HttpError as e:
                print(f"❌ Space message sending: FAILED")
                print(f"   Error: {e}")
            
            # Test thread message (this is what we need to fix)
            test_thread_id = "spaces/AAQAWaIEuf4/threads/2n6iu_9NxA0"  # Replace with actual thread
            
            try:
                # Test sending to thread
                thread_response = service.spaces().messages().create(
                    parent=test_thread_id,
                    body=test_message
                ).execute()
                
                print("✅ Thread message sending: WORKING")
                print(f"   Message ID: {thread_response.get('name', 'Unknown')}")
                
            except HttpError as e:
                print(f"❌ Thread message sending: FAILED")
                print(f"   Error: {e}")
                print(f"   Error Details: {e.error_details}")
            
            return True
            
        except HttpError as e:
            print(f"❌ API access failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up Google Chat API: {e}")
        return False

def fix_google_chat_configuration():
    """Provide instructions to fix Google Chat configuration"""
    
    print("\n" + "=" * 60)
    print("GOOGLE CHAT CONFIGURATION FIX INSTRUCTIONS")
    print("=" * 60)
    
    print("""
🔧 TO ENABLE THREAD REPLIES AND QUOTE REPLIES:

1. GOOGLE CLOUD CONSOLE SETUP:
   - Go to: https://console.cloud.google.com/
   - Select your project: enduring-palace-469405-h2
   - Enable Google Chat API if not already enabled

2. SERVICE ACCOUNT PERMISSIONS:
   - Go to: IAM & Admin > Service Accounts
   - Find: chat-bot-sa@enduring-palace-469405-h2.iam.gserviceaccount.com
   - Add these roles:
     * Chat Bot
     * Chat API User
     * Service Account Token Creator

3. GOOGLE CHAT API CONFIGURATION:
   - Go to: APIs & Services > Google Chat API
   - Click on "Configuration" tab
   - Enable these features:
     * Thread replies
     * Quote replies
     * Message threading
     * Context preservation

4. BOT PERMISSIONS IN GOOGLE CHAT:
   - In your Google Chat space
   - Go to space settings
   - Add the bot with these permissions:
     * Send messages
     * Reply to threads
     * Quote messages
     * Access to all threads

5. UPDATE SCOPES IN CODE:
   Add these scopes to your credentials:
   - https://www.googleapis.com/auth/chat.messages
   - https://www.googleapis.com/auth/chat.threads
   - https://www.googleapis.com/auth/chat.spaces.bot

6. TEST THE CONFIGURATION:
   Run this script again to verify permissions are working.
""")

def update_google_chat_scopes():
    """Update the Google Chat API scopes in the code"""
    
    print("\n" + "=" * 60)
    print("UPDATING GOOGLE CHAT SCOPES IN CODE")
    print("=" * 60)
    
    # File to update
    file_path = "api/google_chat.py"
    
    # New scopes to add
    new_scopes = [
        'https://www.googleapis.com/auth/chat.bot',
        'https://www.googleapis.com/auth/chat.spaces.bot',
        'https://www.googleapis.com/auth/chat.messages',
        'https://www.googleapis.com/auth/chat.threads'
    ]
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find the scopes section
        if 'self.scopes = [' in content:
            # Replace existing scopes
            import re
            pattern = r'self\.scopes = \[[^\]]*\]'
            replacement = f'self.scopes = {new_scopes}'
            updated_content = re.sub(pattern, replacement, content)
            
            with open(file_path, 'w') as f:
                f.write(updated_content)
            
            print(f"✅ Updated scopes in {file_path}")
            print(f"   New scopes: {new_scopes}")
        else:
            print(f"❌ Could not find scopes section in {file_path}")
            
    except Exception as e:
        print(f"❌ Error updating file: {e}")

def create_proper_thread_reply_method():
    """Create a proper thread reply method"""
    
    print("\n" + "=" * 60)
    print("CREATING PROPER THREAD REPLY METHOD")
    print("=" * 60)
    
    proper_method = '''
async def send_thread_reply(self, space_id: str, thread_id: str, message: str) -> bool:
    """Send a proper thread reply using Google Chat API v1"""
    if not self._access_token:
        success = await self.authenticate()
        if not success:
            logger.error("Authentication failed, cannot send thread reply")
            return False
    
    headers = {
        'Authorization': f'Bearer {self._access_token}',
        'Content-Type': 'application/json'
    }
    
    # Ensure proper thread ID format
    if not thread_id.startswith('spaces/'):
        # Extract space ID and construct full thread path
        space_id_clean = space_id.replace('spaces/', '')
        thread_id = f"spaces/{space_id_clean}/threads/{thread_id}"
    
    # Use the thread ID directly as the parent
    url = f"https://chat.googleapis.com/v1/{thread_id}/messages"
    
    payload = {
        'text': message
    }
    
    try:
        logger.info(f"Sending thread reply to: {url}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            logger.info("Thread reply sent successfully")
            return True
        else:
            logger.error(f"Failed to send thread reply: HTTP {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending thread reply: {e}")
        return False

async def send_quote_reply_proper(self, space_id: str, quoted_message_id: str, message: str) -> bool:
    """Send a proper quote reply using Google Chat API v1"""
    if not self._access_token:
        success = await self.authenticate()
        if not success:
            logger.error("Authentication failed, cannot send quote reply")
            return False
    
    headers = {
        'Authorization': f'Bearer {self._access_token}',
        'Content-Type': 'application/json'
    }
    
    # Extract thread ID from message ID
    # Message format: spaces/XXX/threads/YYY/messages/ZZZ
    parts = quoted_message_id.split('/')
    if len(parts) >= 4 and parts[2] == 'threads':
        thread_id = f"{parts[0]}/{parts[1]}/{parts[2]}/{parts[3]}"
    else:
        # Fallback: try to extract from message ID
        thread_id = quoted_message_id.split('.')[0] if '.' in quoted_message_id else quoted_message_id
        if not thread_id.startswith('spaces/'):
            space_id_clean = space_id.replace('spaces/', '')
            thread_id = f"spaces/{space_id_clean}/threads/{thread_id}"
    
    # Use the thread as parent for quote reply
    url = f"https://chat.googleapis.com/v1/{thread_id}/messages"
    
    # Create proper quote reply payload
    payload = {
        'text': message,
        'cards': [{
            'header': {
                'title': 'Reply to support request',
                'subtitle': 'Support Ticket Automation'
            },
            'sections': [{
                'widgets': [{
                    'textParagraph': {
                        'text': f'Replying to: {quoted_message_id}'
                    }
                }]
            }]
        }]
    }
    
    try:
        logger.info(f"Sending quote reply to: {url}")
        logger.info(f"Quoting message: {quoted_message_id}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            logger.info("Quote reply sent successfully")
            return True
        else:
            logger.error(f"Failed to send quote reply: HTTP {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending quote reply: {e}")
        return False
'''
    
    print("📝 Add these methods to your GoogleChatAPI class:")
    print(proper_method)
    
    print("\n🔧 Key improvements:")
    print("   - Proper thread ID handling")
    print("   - Correct API endpoint construction")
    print("   - Better error handling and logging")
    print("   - Proper quote reply payload structure")

if __name__ == "__main__":
    print("🔍 Checking current Google Chat API permissions...")
    
    if check_google_chat_permissions():
        print("\n✅ Basic permissions are working")
    else:
        print("\n❌ Permission issues detected")
    
    fix_google_chat_configuration()
    update_google_chat_scopes()
    create_proper_thread_reply_method()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Follow the configuration instructions above")
    print("2. Update your Google Cloud project settings")
    print("3. Add the new methods to your GoogleChatAPI class")
    print("4. Test with the updated permissions")
    print("5. Monitor logs for successful thread replies")
