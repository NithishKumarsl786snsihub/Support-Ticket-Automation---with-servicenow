"""
Google Chat API Integration
Handles authentication and communication with Google Chat API
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import httpx
from dataclasses import dataclass
import google.auth
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SupportMessage:
    """Represents an incoming support message"""
    message_id: str
    thread_id: str
    user_id: str
    user_name: str
    content: str
    timestamp: datetime
    space_id: str
    user_email: Optional[str] = None  # User's email address if available

class GoogleChatAPI:
    """Google Chat API integration"""
    
    def __init__(self, credentials: Dict):
        self.credentials = credentials
        self.base_url = "https://chat.googleapis.com/v1"
        self._access_token = None
        self.scopes = [
            'https://www.googleapis.com/auth/chat.bot',
            'https://www.googleapis.com/auth/chat.spaces.bot',
            'https://www.googleapis.com/auth/chat.messages',
            'https://www.googleapis.com/auth/chat.threads'
        ]
    
    async def authenticate(self):
        """Authenticate with Google Chat API using either OAuth2 or Service Account"""
        # First try service account if available
        if self.credentials.get('service_account_file'):
            try:
                service_account_file = self.credentials['service_account_file']
                logger.info(f"Authenticating with service account: {service_account_file}")
                
                # Check if file exists
                if not os.path.exists(service_account_file):
                    logger.error(f"Service account file not found: {service_account_file}")
                    return False
                
                # Load the service account credentials
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_file, 
                    scopes=self.scopes
                )
                
                # Get token
                request = Request()
                credentials.refresh(request)
                self._access_token = credentials.token
                if not self._access_token:
                    raise Exception("No access token received from credentials refresh")
                logger.info("Service account authentication successful")
                return True
                
            except Exception as e:
                logger.error(f"Service account authentication failed: {str(e)}")
                # Fall back to OAuth2 if service account fails
        
        # Try OAuth2 refresh token if available
        if self.credentials.get('refresh_token'):
            try:
                # Implementation for OAuth2 token refresh
                auth_url = "https://oauth2.googleapis.com/token"
                payload = {
                    'client_id': self.credentials['client_id'],
                    'client_secret': self.credentials['client_secret'],
                    'refresh_token': self.credentials['refresh_token'],
                    'grant_type': 'refresh_token'
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(auth_url, data=payload)
                    if response.status_code == 200:
                        token_data = response.json()
                        self._access_token = token_data['access_token']
                        logger.info("OAuth2 authentication successful")
                        return True
                    else:
                        logger.error(f"OAuth2 authentication failed: {response.text}")
                        return False
            except Exception as e:
                logger.error(f"OAuth2 authentication failed: {str(e)}")
                return False
        
        logger.error("No valid authentication method available")
        return False
    
    async def get_space_messages(self, space_id: str, since: Optional[datetime] = None) -> List[SupportMessage]:
        """Fetch new messages from Google Chat space"""
        if not self._access_token:
            success = await self.authenticate()
            if not success:
                logger.error("Authentication failed, cannot fetch messages")
                return []
        
        headers = {'Authorization': f'Bearer {self._access_token}'}
        
        # Ensure space_id has 'spaces/' prefix
        if not space_id.startswith('spaces/'):
            space_id = f"spaces/{space_id}"
        url = f"{self.base_url}/{space_id}/messages"
        
        params = {}
        # If an API key is provided, include it as a query parameter per Google API conventions
        chat_api_key = self.credentials.get('chat_api_key') if hasattr(self, 'credentials') else None
        if chat_api_key:
            params['key'] = chat_api_key
        if since:
            # Format timestamp for Google Chat API
            timestamp = since.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            params['filter'] = f'createTime > "{timestamp}"'
            logger.info(f"Using filter: {params['filter']}")
        
        messages = []
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Fetching messages from URL: {url}")
                logger.info(f"With params: {params}")
                response = await client.get(url, headers=headers, params=params)
                logger.info(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Response data: {json.dumps(data, indent=2)}")
                    for msg_data in data.get('messages', []):
                        # Extract thread ID properly
                        thread_info = msg_data.get('thread', {})
                        thread_id = None
                        if thread_info:
                            thread_name = thread_info.get('name', '')
                            if thread_name:
                                # Store the full thread path for notifications
                                thread_id = thread_name
                        
                        # Extract user information
                        sender_info = msg_data['sender']
                        user_id = sender_info['name'].split('/')[-1]
                        user_name = sender_info.get('displayName', 'Unknown')
                        user_email = sender_info.get('email', None)
                        
                        # If email is not available, try to get user details
                        if not user_email and user_id:
                            try:
                                user_details = await self.get_user_details(user_id)
                                if user_details:
                                    user_email = user_details.get('email')
                                    if not user_name or user_name == 'Unknown':
                                        user_name = user_details.get('name', user_name)
                            except Exception as e:
                                logger.warning(f"Failed to get user details for {user_id}: {e}")
                        
                        message = SupportMessage(
                            message_id=msg_data['name'].split('/')[-1],
                            thread_id=thread_id or '',  # Use empty string if no thread
                            user_id=user_id,
                            user_name=user_name,
                            content=msg_data.get('text', ''),
                            timestamp=datetime.fromisoformat(msg_data['createTime'].rstrip('Z')),
                            space_id=space_id,
                            user_email=user_email
                        )
                        messages.append(message)
                else:
                    logger.error(f"Failed to fetch messages: {response.text}")
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}")
        
        return messages
    
    async def get_user_details(self, user_id: str) -> Optional[Dict[str, str]]:
        """Get user details from Google Chat API"""
        try:
            if not await self.authenticate():
                logger.error("Failed to authenticate with Google Chat API")
                return None
            
            # Get user details
            endpoint = f"{self.base_url}/users/{user_id}"
            headers = {
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Getting user details from URL: {endpoint}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, headers=headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    logger.info(f"User details retrieved: {json.dumps(user_data, indent=2)}")
                    return {
                        'name': user_data.get('displayName', ''),
                        'email': user_data.get('email', ''),
                        'user_id': user_id
                    }
                else:
                    logger.warning(f"Failed to get user details: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting user details: {e}")
            return None

    async def send_message(self, space_id: str, thread_id: str, message: str) -> bool:
        """Send message back to Google Chat thread"""
        if not self._access_token:
            success = await self.authenticate()
            if not success:
                logger.error("Authentication failed, cannot send message")
                return False
        
        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json'
        }
        
        # Ensure space_id has 'spaces/' prefix
        if not space_id.startswith('spaces/'):
            space_id = f"spaces/{space_id}"
        
        # Determine the correct URL based on whether we're sending to a thread or space
        if thread_id:
            # Send to specific thread
            # Handle different thread_id formats
            if thread_id.startswith('spaces/') and '/threads/' in thread_id:
                # Full thread path provided (e.g., spaces/XXX/threads/YYY)
                # Extract just the space and thread parts
                parts = thread_id.split('/')
                if len(parts) >= 4 and parts[0] == 'spaces' and parts[2] == 'threads':
                    space_part = parts[1]
                    thread_part = parts[3]
                    url = f"https://chat.googleapis.com/v1/spaces/{space_part}/threads/{thread_part}/messages"
                else:
                    # Fallback to original logic
                    url = f"https://chat.googleapis.com/v1/{thread_id}/messages"
            elif thread_id.startswith('threads/'):
                # Thread path without spaces prefix
                space_id_clean = space_id.replace('spaces/', '')
                url = f"https://chat.googleapis.com/v1/spaces/{space_id_clean}/{thread_id}/messages"
            else:
                # Just the thread ID, construct the full path
                space_id_clean = space_id.replace('spaces/', '')
                url = f"https://chat.googleapis.com/v1/spaces/{space_id_clean}/threads/{thread_id}/messages"
                
            logger.info(f"Constructed thread URL: {url}")
        else:
            # Send to space (not thread)
            url = f"https://chat.googleapis.com/v1/{space_id}/messages"
            logger.info(f"Constructed space URL: {url}")
        
        payload = {
            'text': message
        }
        
        try:
            logger.info(f"Sending message to URL: {url}")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                logger.info("Message sent successfully")
                return True
            else:
                logger.error(f"Failed to send message: HTTP {response.status_code}")
                logger.error(f"Response text: {response.text}")
                logger.error(f"Request URL: {url}")
                logger.error(f"Request payload: {json.dumps(payload, indent=2)}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def send_message_with_fallback(self, space_id: str, thread_id: str, message: str, original_message_id: str = None) -> bool:
        """Send message with fallback: try thread reply first, then quote reply, then space"""
        if not self._access_token:
            success = await self.authenticate()
            if not success:
                logger.error("Authentication failed, cannot send message")
                return False
        
        # First attempt: Try to send thread reply (new method)
        if thread_id:
            logger.info(f"🔄 Attempt 1: Sending thread reply to {thread_id}")
            success = await self.send_thread_reply(space_id, thread_id, message)
            if success:
                logger.info("✅ Thread reply sent successfully")
                return True
            else:
                logger.warning("⚠️ Thread reply failed, trying quote reply")
        
        # Second attempt: Try quote reply
        if original_message_id:
            logger.info(f"🔄 Attempt 2: Sending quote reply to message {original_message_id}")
            success = await self.send_quote_reply(space_id, original_message_id, message)
            if success:
                logger.info("✅ Quote reply sent successfully")
                return True
            else:
                logger.warning("⚠️ Quote reply failed, trying simple space message")
        
        # Final fallback: Send to space as simple message
        logger.info(f"🔄 Attempt 3: Sending to space as simple message")
        success = await self.send_message(space_id, None, message)
        if success:
            logger.info("✅ Fallback simple space message sent successfully")
            return True
        else:
            logger.error("❌ All notification attempts failed")
            return False

    async def send_thread_reply(self, space_id: str, thread_id: str, message: str) -> bool:
        """Send a proper thread reply using Google Chat API v1 with thread object"""
        if not self._access_token:
            success = await self.authenticate()
            if not success:
                logger.error("Authentication failed, cannot send thread reply")
                return False
        
        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json'
        }
        
        # Ensure space_id has proper format
        if not space_id.startswith('spaces/'):
            space_id = f"spaces/{space_id}"
        
        # Extract thread ID from full path if needed
        if thread_id.startswith('spaces/'):
            # Extract just the thread ID part
            parts = thread_id.split('/')
            if len(parts) >= 4 and parts[2] == 'threads':
                thread_id = parts[3]
        
        # Construct the URL for sending to space
        url = f"https://chat.googleapis.com/v1/{space_id}/messages"
        
        # Create payload with thread object (this is the correct way!)
        payload = {
            'text': message,
            'thread': {
                'name': f"{space_id}/threads/{thread_id}"
            }
        }
        
        try:
            logger.info(f"Sending thread reply to space: {url}")
            logger.info(f"Thread ID: {thread_id}")
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

    async def send_quote_reply(self, space_id: str, quoted_message_id: str, message: str) -> bool:
        """Send a proper quote reply using Google Chat API v1 with thread object"""
        if not self._access_token:
            success = await self.authenticate()
            if not success:
                logger.error("Authentication failed, cannot send quote reply")
                return False
        
        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json'
        }
        
        # Ensure space_id has proper format
        if not space_id.startswith('spaces/'):
            space_id = f"spaces/{space_id}"
        
        # Extract thread ID from message ID
        # Message format: spaces/XXX/threads/YYY/messages/ZZZ
        parts = quoted_message_id.split('/')
        if len(parts) >= 4 and parts[2] == 'threads':
            thread_id = parts[3]  # Extract just the thread ID part
        else:
            # Fallback: try to extract from message ID
            thread_id = quoted_message_id.split('.')[0] if '.' in quoted_message_id else quoted_message_id
        
        # Construct the URL for sending to space
        url = f"https://chat.googleapis.com/v1/{space_id}/messages"
        
        # Create proper quote reply payload with thread object (without cards for bot)
        payload = {
            'text': message,
            'thread': {
                'name': f"{space_id}/threads/{thread_id}"
            }
        }
        
        try:
            logger.info(f"Sending quote reply to space: {url}")
            logger.info(f"Thread ID: {thread_id}")
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