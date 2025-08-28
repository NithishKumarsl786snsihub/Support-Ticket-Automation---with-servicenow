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

class GoogleChatAPI:
    """Google Chat API integration"""
    
    def __init__(self, credentials: Dict):
        self.credentials = credentials
        self.base_url = "https://chat.googleapis.com/v1"
        self._access_token = None
        self.scopes = [
            'https://www.googleapis.com/auth/chat.bot',
            'https://www.googleapis.com/auth/chat.spaces.bot'
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
                                # Extract just the thread ID part
                                thread_id = thread_name.split('/')[-1]
                        
                        message = SupportMessage(
                            message_id=msg_data['name'].split('/')[-1],
                            thread_id=thread_id or '',  # Use empty string if no thread
                            user_id=msg_data['sender']['name'].split('/')[-1],
                            user_name=msg_data['sender'].get('displayName', 'Unknown'),
                            content=msg_data.get('text', ''),
                            timestamp=datetime.fromisoformat(msg_data['createTime'].rstrip('Z')),
                            space_id=space_id
                        )
                        messages.append(message)
                else:
                    logger.error(f"Failed to fetch messages: {response.text}")
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}")
        
        return messages
    
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
            if thread_id.startswith('spaces/'):
                # Full thread path provided
                url = f"https://chat.googleapis.com/v1/{thread_id}/messages"
            elif thread_id.startswith('threads/'):
                # Thread path without spaces prefix
                space_id_clean = space_id.replace('spaces/', '')
                url = f"https://chat.googleapis.com/v1/spaces/{space_id_clean}/{thread_id}/messages"
            else:
                # Just the thread ID, construct the full path
                space_id_clean = space_id.replace('spaces/', '')
                url = f"https://chat.googleapis.com/v1/spaces/{space_id_clean}/threads/{thread_id}/messages"
        else:
            # Send to space (not thread)
            url = f"https://chat.googleapis.com/v1/{space_id}/messages"
        
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
                logger.error(f"Failed to send message: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False