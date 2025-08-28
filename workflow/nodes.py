"""
LangGraph Workflow Nodes
Defines the individual processing steps in the workflow
"""

import logging
from datetime import datetime, timedelta

from langchain_google_genai import ChatGoogleGenerativeAI

from utils.credentials import CredentialsManager
from utils.models import WorkflowState
from api.google_chat import GoogleChatAPI, SupportMessage
from api.servicenow import ServiceNowAPI
from agents.classifier import ClassifierAgent
from agents.summarizer import SummaryAgent
from agents.categorizer import CategoryExtractorAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scheduler_node(state: WorkflowState) -> WorkflowState:
    """Entry point - determines if workflow should run"""
    logger.info("🔄 Scheduler: Starting workflow execution")
    state['current_step'] = 'scheduler'
    
    # Check if we have messages to process
    if not state.get('messages'):
        # Fetch new messages (this would be triggered by webhook or schedule)
        state['messages'] = []  # Placeholder - will be populated by message fetcher
    
    return state

async def message_fetcher_node(state: WorkflowState) -> WorkflowState:
    """Fetch new messages from Google Chat"""
    logger.info("📨 Message Fetcher: Retrieving new messages")
    state['current_step'] = 'message_fetcher'
    
    try:
        credentials_manager = CredentialsManager()
        google_chat = GoogleChatAPI(credentials_manager.google_credentials)
        
        # Look for messages from the last 24 hours to catch any unprocessed messages
        since = datetime.now() - timedelta(hours=24)  # Get messages from last 24 hours
        space_id = credentials_manager.google_credentials['space_id']
        logger.info(f"Fetching messages since: {since.isoformat()}")
        
        messages = await google_chat.get_space_messages(space_id, since)
        state['messages'] = messages
        
        logger.info(f"Fetched {len(messages)} messages")
        
    except Exception as e:
        logger.error(f"Message fetching failed: {e}")
        state['errors'].append(f"Message fetch error: {str(e)}")
    
    return state

async def classifier_node(state: WorkflowState) -> WorkflowState:
    """Classify messages as support requests"""
    logger.info("🤖 Classifier: Analyzing messages")
    state['current_step'] = 'classifier'
    
    try:
        credentials_manager = CredentialsManager()
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=credentials_manager.gemini_api_key,
            temperature=0.1
        )
        
        classifier = ClassifierAgent(llm)
        classified_messages = []
        
        for message in state.get('messages', []):
            logger.info(f"Processing message: {message.content}")
            
            # Check if message already has a ticket created
            if message.message_id in state.get('ticket_links', {}):
                logger.info(f"Message {message.message_id} already has ticket {state['ticket_links'][message.message_id]}, skipping")
                continue
            
            # Only process messages that mention the bot
            if '@Support Ticket Automation' in message.content or 'Support Ticket Automation' in message.content:
                logger.info(f"Message mentions bot, processing: {message.content}")
                
                # Check if we already processed this message (avoid duplicates)
                message_key = f"{message.message_id}_{message.thread_id}"
                if message_key in state.get('processed_messages', set()):
                    logger.info(f"Message already processed, skipping: {message_key}")
                    continue
                
                classified = await classifier.classify_message(message)
                if classified:
                    logger.info(f"Message classified as support request: {classified.is_support_request}")
                    classified_messages.append(classified)
                    
                    # Mark message as processed
                    if 'processed_messages' not in state:
                        state['processed_messages'] = set()
                    state['processed_messages'].add(message_key)
            else:
                logger.info(f"Message does not mention bot, skipping: {message.content[:50]}...")
        
        # Filter only support requests
        support_requests = [msg for msg in classified_messages if msg.is_support_request]
        
        state['classified_messages'] = support_requests
        logger.info(f"Identified {len(support_requests)} support requests")
        
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        state['errors'].append(f"Classification error: {str(e)}")
    
    return state

async def summary_node(state: WorkflowState) -> WorkflowState:
    """Generate ticket summaries"""
    logger.info("📝 Summary: Creating ticket summaries")
    state['current_step'] = 'summary'
    
    try:
        credentials_manager = CredentialsManager()
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=credentials_manager.gemini_api_key,
            temperature=0.3
        )
        
        summary_agent = SummaryAgent(llm)
        summarized_tickets = []
        
        for classified_msg in state.get('classified_messages', []):
            summary = await summary_agent.summarize_message(classified_msg)
            summarized_tickets.append(summary)
        
        state['summarized_tickets'] = summarized_tickets
        logger.info(f"Generated {len(summarized_tickets)} ticket summaries")
        
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        state['errors'].append(f"Summary error: {str(e)}")
    
    return state

async def category_extractor_node(state: WorkflowState) -> WorkflowState:
    """Extract categories and priorities"""
    logger.info("🏷️ Category Extractor: Categorizing tickets")
    state['current_step'] = 'category_extractor'
    
    try:
        credentials_manager = CredentialsManager()
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=credentials_manager.gemini_api_key,
            temperature=0.2
        )
        
        category_agent = CategoryExtractorAgent(llm)
        categorized_tickets = []
        
        for summary in state.get('summarized_tickets', []):
            categorized = await category_agent.categorize_ticket(summary)
            categorized_tickets.append(categorized)
        
        state['categorized_tickets'] = categorized_tickets
        logger.info(f"Categorized {len(categorized_tickets)} tickets")
        
    except Exception as e:
        logger.error(f"Categorization failed: {e}")
        state['errors'].append(f"Category error: {str(e)}")
    
    return state

async def servicenow_node(state: WorkflowState) -> WorkflowState:
    """Create tickets in ServiceNow"""
    logger.info("🎫 ServiceNow: Creating tickets")
    state['current_step'] = 'servicenow'
    
    try:
        from tools.servicenowTool import build_incident_assignment_fields  # lazy import to avoid cycles
        
        credentials_manager = CredentialsManager()
        servicenow = ServiceNowAPI(credentials_manager.servicenow_credentials)
        
        created_tickets = []
        newly_created_tickets = []  # Track which tickets were newly created
        summaries = state.get('summarized_tickets', [])
        categories = state.get('categorized_tickets', [])
        classified_messages = state.get('classified_messages', [])
        
        for i, (summary, category, classified_msg) in enumerate(zip(summaries, categories, classified_messages)):
            original_msg = classified_msg.original_message
            correlation_id = original_msg.message_id
            
            # Check in-memory map first
            existing_number = state.get('ticket_links', {}).get(correlation_id)
            if existing_number:
                logger.info(f"Incident already created for message {correlation_id}: {existing_number}; skipping creation")
                continue
            
            # Check ServiceNow by correlation_id to avoid duplicates across runs
            existing = await servicenow.find_incident_by_correlation(correlation_id)
            if existing:
                logger.info(f"Found existing incident {existing.number} for message {correlation_id}; linking and skipping creation")
                if 'ticket_links' not in state:
                    state['ticket_links'] = {}
                state['ticket_links'][correlation_id] = existing.number
                created_tickets.append(existing)
                # Don't add to newly_created_tickets since this is an existing ticket
                continue
            
            # Resolve caller and assignment using tools
            caller_email = getattr(original_msg, 'user_email', None)  # optional, may not exist
            caller_name = original_msg.user_name
            group_name = category.assignment_group
            assignment_fields = build_incident_assignment_fields(
                caller_email=caller_email,
                caller_name=caller_name,
                group_name=group_name,
            )
            
            ticket_data = {
                'title': summary.title,
                'description': summary.description,
                'priority': category.priority.value,
                'category': category.category.value,
                'subcategory': category.subcategory,
                'urgency': category.urgency,
                'assignment_group_name': group_name,  # keep name for traceability
                'correlation_id': correlation_id,
            }
            
            # Merge resolved fields (caller_id, assignment_group, assigned_to)
            ticket_data.update(assignment_fields)
            
            ticket = await servicenow.create_incident(ticket_data)
            created_tickets.append(ticket)
            # Store ticket with its correlation_id for notification tracking
            newly_created_tickets.append({
                'ticket': ticket,
                'correlation_id': correlation_id,
                'original_message': original_msg
            })
            
            # Track the ticket creation for this message
            if 'ticket_links' not in state:
                state['ticket_links'] = {}
            state['ticket_links'][correlation_id] = ticket.number
            
            logger.info(f"Created ticket {ticket.number} for message {correlation_id}")
        
        state['servicenow_tickets'] = created_tickets
        state['newly_created_tickets'] = newly_created_tickets  # Store for notification node
        logger.info(f"Created/linked {len(created_tickets)} ServiceNow tickets ({len(newly_created_tickets)} newly created)")
        
        # Log the newly created tickets for debugging
        for i, ticket_info in enumerate(newly_created_tickets):
            logger.info(f"  Newly created ticket {i+1}: {ticket_info['ticket'].number} for message {ticket_info['correlation_id']}")
        
    except Exception as e:
        logger.error(f"ServiceNow creation failed: {e}")
        state['errors'].append(f"ServiceNow error: {str(e)}")
    
    return state

async def notification_node(state: WorkflowState) -> WorkflowState:
    """Send notifications back to Google Chat"""
    logger.info("📢 Notification: Sending updates to Google Chat")
    state['current_step'] = 'notification'
    
    try:
        credentials_manager = CredentialsManager()
        google_chat = GoogleChatAPI(credentials_manager.google_credentials)
        
        newly_created_tickets = state.get('newly_created_tickets', [])
        notifications_sent = []
        
        logger.info(f"Processing {len(newly_created_tickets)} newly created tickets for notifications")
        
        # Log the tickets that will be processed
        for i, ticket_info in enumerate(newly_created_tickets):
            logger.info(f"  Ticket {i+1}: {ticket_info['ticket'].number} for message {ticket_info['correlation_id']}")
        
        # Only send notifications for newly created tickets
        for ticket_info in newly_created_tickets:
            ticket = ticket_info['ticket']
            original_msg = ticket_info['original_message']
            
            # Create ServiceNow ticket link
            servicenow_url = credentials_manager.servicenow_credentials['instance_url']
            ticket_link = f"{servicenow_url}/nav_to.do?uri=incident.do?sys_id={ticket.sys_id}"
            
            # Send notification to the space (since thread permissions are restricted)
            try:
                # Include user context in the notification
                user_context = f"**From:** {original_msg.user_name}"
                notification_text = f"""
                ✅ **Ticket Created Successfully**
                
                {user_context}
                **Ticket Number:** [{ticket.number}]({ticket_link})
                **Title:** {ticket.short_description}
                **Priority:** {ticket.priority}
                **Status:** In Progress
                
                **Original Message:** "{original_msg.content[:100]}..."
                
                Your request has been automatically processed and assigned to the appropriate team. 
                You'll receive updates as the ticket progresses.
                
                [View Ticket in ServiceNow]({ticket_link})
                """
                
                # Send to space instead of thread
                # Ensure space_id has the correct format
                space_id = original_msg.space_id
                if not space_id.startswith('spaces/'):
                    space_id = f"spaces/{space_id}"
                
                success = await google_chat.send_message(
                    space_id=space_id,
                    thread_id=None,  # Send to space instead of thread
                    message=notification_text
                )
                
                if success:
                    notifications_sent.append({
                        'ticket_number': ticket.number,
                        'message_id': original_msg.message_id,
                        'user_name': original_msg.user_name,
                        'notification_sent': True,
                        'timestamp': datetime.now().isoformat(),
                        'ticket_link': ticket_link
                    })
                    logger.info(f"Notification sent for newly created ticket {ticket.number} for message {original_msg.message_id} from {original_msg.user_name}")
                else:
                    logger.error(f"Failed to send notification for message {original_msg.message_id}")
                    
            except Exception as e:
                logger.error(f"Error sending notification for message {original_msg.message_id}: {e}")
        
        state['notifications_sent'] = notifications_sent
        logger.info(f"Sent {len(notifications_sent)} notifications for newly created tickets")
        
    except Exception as e:
        logger.error(f"Notification failed: {e}")
        state['errors'].append(f"Notification error: {str(e)}")
    
    return state

async def tracker_node(state: WorkflowState) -> WorkflowState:
    """Track ticket status and send updates"""
    logger.info("👁️ Tracker: Monitoring ticket status")
    state['current_step'] = 'tracker'
    
    try:
        credentials_manager = CredentialsManager()
        servicenow = ServiceNowAPI(credentials_manager.servicenow_credentials)
        
        # This would typically be a separate scheduled process
        # For now, just log that tracking is active
        
        for ticket in state.get('servicenow_tickets', []):
            current_ticket = await servicenow.get_incident(ticket.sys_id)
            if current_ticket and current_ticket.state != ticket.state:
                # Status changed - send update
                logger.info(f"Ticket {ticket.number} status changed to {current_ticket.state}")
                
                # Send status update to Google Chat
                # (Implementation would fetch original thread info)
        
        logger.info("Tracking system active")
        
    except Exception as e:
        logger.error(f"Tracking failed: {e}")
        state['errors'].append(f"Tracking error: {str(e)}")
    
    return state
