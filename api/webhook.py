"""
Webhook Handler
Handles incoming webhooks from Google Chat and ServiceNow
"""

import logging
import asyncio
import json
from datetime import datetime
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from api.google_chat import SupportMessage, GoogleChatAPI
from api.servicenow import ServiceNowAPI
from utils.credentials import CredentialsManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handles incoming webhooks from Google Chat"""
    
    def __init__(self, automation_system):
        self.app = FastAPI(title="Support Ticket Automation Webhook")
        self.automation = automation_system
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.post("/webhook/google-chat")
        async def handle_google_chat_webhook(request: Request):
            """Handle incoming Google Chat messages"""
            try:
                logger.info("🔔 Webhook received - processing Google Chat message")
                payload = await request.json()
                logger.info(f"📦 Payload received: {json.dumps(payload, indent=2)}")
                
                # Verify webhook authenticity (implement proper verification)
                if not self._verify_webhook(payload):
                    raise HTTPException(status_code=401, detail="Unauthorized")
                
                # Extract message data
                message_data = payload.get('message', {})
                logger.info(f"📝 Message data: {json.dumps(message_data, indent=2)}")
                if not message_data:
                    logger.warning("⚠️ No message data found in payload")
                    return JSONResponse({"status": "no_message"})
                
                # Extract user information
                sender_info = message_data['sender']
                user_id = sender_info['name'].split('/')[-1]
                user_name = sender_info.get('displayName', 'Unknown')
                
                # Try to get user email from sender info
                user_email = None
                if 'email' in sender_info:
                    user_email = sender_info['email']
                
                # Convert to SupportMessage
                message = SupportMessage(
                    message_id=message_data['name'].split('/')[-1],
                    thread_id=message_data.get('thread', {}).get('name', '').split('/')[-1],
                    user_id=user_id,
                    user_name=user_name,
                    content=message_data.get('text', ''),
                    timestamp=datetime.fromisoformat(message_data['createTime'].rstrip('Z')),
                    space_id=payload.get('space', {}).get('name', '').split('/')[-1]
                )
                
                # Add user email to message if available
                if user_email:
                    message.user_email = user_email
                logger.info(f"📨 Converted message: {message.content}")
                logger.info(f"👤 User: {message.user_name}")
                logger.info(f"🏠 Space ID: {message.space_id}")
                logger.info(f"🧵 Thread ID: {message.thread_id}")
                
                # Check if message mentions the bot
                if '@Support Ticket Automation' in message.content or 'Support Ticket Automation' in message.content:
                    logger.info(f"Bot mentioned in message: {message.content}")
                    
                    # Check if a ticket already exists for this message
                    credentials_manager = CredentialsManager()
                    servicenow = ServiceNowAPI(credentials_manager.servicenow_credentials)
                    existing_ticket = await servicenow.find_incident_by_correlation(message.message_id)
                    
                    if existing_ticket:
                        logger.info(f"Ticket already exists for message {message.message_id}: {existing_ticket.number}")
                        # Don't send immediate acknowledgment or trigger workflow for existing tickets
                        return JSONResponse({"status": "ticket_exists", "ticket_number": existing_ticket.number})
                    
                    # Send immediate acknowledgment only for new requests
                    google_chat = GoogleChatAPI(credentials_manager.google_credentials)
                    
                    # Add "spaces/" prefix if not present
                    space_id = message.space_id
                    if not space_id.startswith('spaces/'):
                        space_id = f"spaces/{space_id}"
                    
                    # Send immediate response
                    await google_chat.send_message(
                        space_id=space_id,
                        thread_id=message.thread_id,
                        message="🤖 **Support Ticket Automation** is processing your request...\n\nI'm analyzing your message and will create a ticket shortly."
                    )
                    
                    # Trigger workflow asynchronously
                    asyncio.create_task(self.automation.run_workflow([message]))
                else:
                    logger.info(f"Message does not mention bot, skipping: {message.content[:50]}...")
                
                return JSONResponse({"status": "processing"})
                
            except Exception as e:
                logger.error(f"Webhook handling error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @self.app.post("/webhook/servicenow")
        async def handle_servicenow_webhook(request: Request):
            """Handle ServiceNow ticket status updates"""
            try:
                payload = await request.json()
                
                # Extract ticket update information
                ticket_data = payload.get('data', {})
                sys_id = ticket_data.get('sys_id')
                new_state = ticket_data.get('state')
                
                if sys_id and new_state:
                    # Send update notification to Google Chat
                    await self._send_status_update(sys_id, new_state)
                
                return JSONResponse({"status": "processed"})
                
            except Exception as e:
                logger.error(f"ServiceNow webhook error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    def _verify_webhook(self, payload: Dict) -> bool:
        """Verify webhook authenticity"""
        # Implement proper webhook verification
        # For Google Chat, verify the token or signature
        return True  # Placeholder
    
    async def _send_status_update(self, sys_id: str, new_state: str):
        """Send status update notification"""
        try:
            credentials_manager = CredentialsManager()
            servicenow = ServiceNowAPI(credentials_manager.servicenow_credentials)
            google_chat = GoogleChatAPI(credentials_manager.google_credentials)
            
            # Get ticket details
            ticket = await servicenow.get_incident(sys_id)
            if not ticket:
                return
            
            # Create status update message
            status_map = {
                '1': 'New',
                '2': 'In Progress',
                '6': 'Resolved',
                '7': 'Closed'
            }
            
            status_text = status_map.get(new_state, 'Updated')
            
            update_message = f"""
            🔄 **Ticket Status Update**
            
            **Ticket:** {ticket.number}
            **New Status:** {status_text}
            **Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            {ticket.short_description}
            """
            
            # Note: In production, you'd need to store the mapping of tickets to chat threads
            # For now, this is a placeholder for the notification logic
            
        except Exception as e:
            logger.error(f"Status update failed: {e}")
