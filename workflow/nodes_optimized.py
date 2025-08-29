"""
Optimized LangGraph Workflow Nodes
Reduces LLM usage by implementing rule-based logic and batching operations
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI

from utils.credentials import CredentialsManager
from utils.models import WorkflowState, SupportMessage, ClassifiedMessage, TicketSummary, TicketCategory, Priority, Category
from api.google_chat import GoogleChatAPI
from api.servicenow import ServiceNowAPI
from agents.classifier import ClassifierAgent
from agents.summarizer import SummaryAgent
from agents.categorizer import CategoryExtractorAgent
from agents.duplicate_detector import DuplicateDetectionAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rule-based classification keywords
SUPPORT_KEYWORDS = [
    'help', 'support', 'issue', 'problem', 'broken', 'not working', 'error',
    'fix', 'assist', 'trouble', 'down', 'crash', 'fail', 'cannot', "can't",
    'password', 'login', 'access', 'email', 'printer', 'network', 'internet',
    'software', 'hardware', 'computer', 'laptop', 'desktop', 'server'
]

CATEGORY_KEYWORDS = {
    Category.HARDWARE: ['hardware', 'computer', 'laptop', 'desktop', 'printer', 'scanner', 'keyboard', 'mouse', 'monitor', 'screen'],
    Category.SOFTWARE: ['software', 'application', 'program', 'app', 'system', 'update', 'install', 'uninstall'],
    Category.NETWORK: ['network', 'internet', 'wifi', 'ethernet', 'connection', 'vpn', 'firewall'],
    Category.ACCESS: ['access', 'login', 'password', 'authentication', 'permission', 'account', 'user'],
    Category.EMAIL: ['email', 'outlook', 'gmail', 'mail', 'inbox', 'spam'],
    Category.PRINTING: ['printer', 'print', 'scan', 'copier', 'fax'],
    Category.SECURITY: ['security', 'virus', 'malware', 'firewall', 'encryption', 'breach']
}

PRIORITY_KEYWORDS = {
    Priority.CRITICAL: ['critical', 'urgent', 'emergency', 'down', 'broken', 'crash', 'fail', 'cannot work'],
    Priority.HIGH: ['important', 'blocking', 'cannot', "can't", 'not working', 'issue'],
    Priority.MODERATE: ['problem', 'issue', 'help', 'support', 'assist'],
    Priority.LOW: ['question', 'inquiry', 'information', 'how to', 'guide']
}

def rule_based_classification(message: SupportMessage) -> ClassifiedMessage:
    """Rule-based classification to reduce LLM calls"""
    content_lower = message.content.lower()
    
    # FIRST: Check if this is an admin notification message (should be excluded)
    admin_notification_patterns = [
        '🎫 **support ticket created**',
        'ticket number: inc',
        'your request has been processed',
        'ticket has been created',
        'view ticket: [open in servicenow]',
        'status:',
        'priority:',
        'you will receive updates as the issue progresses'
    ]
    
    # Check if message contains admin notification patterns
    is_admin_notification = any(pattern in content_lower for pattern in admin_notification_patterns)
    
    if is_admin_notification:
        return ClassifiedMessage(
            original_message=message,
            is_support_request=False,
            confidence=0.95,
            reasoning="Admin notification message - not a user support request"
        )
    
    # SECOND: Check if message mentions the bot
    bot_mentioned = '@Support Ticket Automation' in message.content or 'Support Ticket Automation' in message.content
    
    if not bot_mentioned:
        return ClassifiedMessage(
            original_message=message,
            is_support_request=False,
            confidence=0.0,
            reasoning="Message does not mention bot"
        )
    
    # THIRD: Check for support keywords (only if it's not admin notification and mentions bot)
    support_score = 0
    found_keywords = []
    
    for keyword in SUPPORT_KEYWORDS:
        if keyword in content_lower:
            support_score += 1
            found_keywords.append(keyword)
    
    # Determine if it's a support request based on keywords
    is_support_request = support_score >= 1
    confidence = min(support_score / 3.0, 1.0)  # Normalize confidence
    
    reasoning = f"Bot mentioned. Found support keywords: {found_keywords}" if found_keywords else "Bot mentioned but no clear support keywords"
    
    return ClassifiedMessage(
        original_message=message,
        is_support_request=is_support_request,
        confidence=confidence,
        reasoning=reasoning
    )

def rule_based_categorization(message: SupportMessage, summary: TicketSummary) -> TicketCategory:
    """Rule-based categorization to reduce LLM calls"""
    content_lower = message.content.lower()
    summary_lower = summary.description.lower()
    combined_text = f"{content_lower} {summary_lower}"
    
    # Determine category based on keywords
    category_scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in combined_text)
        if score > 0:
            category_scores[category] = score
    
    # Default to OTHER if no specific category found
    if not category_scores:
        category = Category.OTHER
    else:
        category = max(category_scores.items(), key=lambda x: x[1])[0]
    
    # Determine priority based on keywords
    priority_scores = {}
    for priority, keywords in PRIORITY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in combined_text)
        if score > 0:
            priority_scores[priority] = score
    
    # Default to MODERATE if no specific priority found
    if not priority_scores:
        priority = Priority.MODERATE
    else:
        priority = max(priority_scores.items(), key=lambda x: x[1])[0]
    
    # Determine urgency and assignment group based on category
    urgency_map = {
        Category.HARDWARE: "3",
        Category.SOFTWARE: "3", 
        Category.NETWORK: "2",
        Category.ACCESS: "2",
        Category.EMAIL: "3",
        Category.PRINTING: "4",
        Category.SECURITY: "1",
        Category.OTHER: "3"
    }
    
    assignment_group_map = {
        Category.HARDWARE: "IT Hardware Support",
        Category.SOFTWARE: "IT Software Support",
        Category.NETWORK: "IT Network Support", 
        Category.ACCESS: "IT Access Management",
        Category.EMAIL: "IT Email Support",
        Category.PRINTING: "IT Hardware Support",
        Category.SECURITY: "IT Security Team",
        Category.OTHER: "IT General Support"
    }
    
    return TicketCategory(
        category=category,
        priority=priority,
        subcategory="General",
        urgency=urgency_map[category],
        assignment_group=assignment_group_map[category]
    )

def create_simple_summary(message: SupportMessage) -> TicketSummary:
    """Create a simple summary without LLM calls"""
    content = message.content
    
    # Extract first sentence as title
    sentences = content.split('.')
    title = sentences[0].strip() if sentences else "Support Request"
    
    # Limit title length
    if len(title) > 100:
        title = title[:97] + "..."
    
    # Create description from content
    description = content
    if len(description) > 500:
        description = description[:497] + "..."
    
    return TicketSummary(
        title=title,
        description=description,
        problem_statement=content[:200] + "..." if len(content) > 200 else content,
        user_impact="User requires assistance",
        urgency_level="Medium"
    )

async def duplicate_detection_node(state: WorkflowState) -> WorkflowState:
    """Detect duplicate support requests to prevent duplicate ticket creation"""
    logger.info("🔍 Duplicate Detection: Analyzing messages for duplicates")
    state['current_step'] = 'duplicate_detection'
    
    try:
        duplicate_agent = DuplicateDetectionAgent()
        messages = state.get('messages', [])
        
        # Get recent tickets for comparison
        recent_tickets = await duplicate_agent.servicenow.get_recent_incidents(hours=24)
        logger.info(f"Retrieved {len(recent_tickets)} recent tickets for duplicate detection")
        
        unique_messages = []
        duplicate_messages = []
        
        for message in messages:
            logger.info(f"Analyzing message {message.message_id} for duplicates...")
            
            # Check if message already has a ticket created
            if message.message_id in state.get('ticket_links', {}):
                logger.info(f"Message {message.message_id} already has ticket, skipping duplicate detection")
                continue
            
            # Use duplicate detection agent
            duplicate_result = await duplicate_agent.detect_duplicates(message, recent_tickets)
            
            if duplicate_result.is_duplicate:
                logger.info(f"🚫 DUPLICATE DETECTED: {duplicate_result}")
                duplicate_messages.append({
                    'message': message,
                    'result': duplicate_result
                })
                
                # Mark as processed to prevent further processing
                if 'processed_messages' not in state:
                    state['processed_messages'] = set()
                message_key = f"{message.message_id}_{message.thread_id}"
                state['processed_messages'].add(message_key)
                
            else:
                logger.info(f"✅ UNIQUE REQUEST: {duplicate_result}")
                unique_messages.append(message)
        
        # Update state with duplicate detection results
        state['duplicate_messages'] = duplicate_messages
        state['unique_messages'] = unique_messages
        state['messages'] = unique_messages  # Only process unique messages
        
        logger.info(f"Duplicate detection complete:")
        logger.info(f"  - Total messages: {len(messages)}")
        logger.info(f"  - Duplicates found: {len(duplicate_messages)}")
        logger.info(f"  - Unique requests: {len(unique_messages)}")
        
        # Log duplicate details for debugging
        for dup in duplicate_messages:
            logger.info(f"  🚫 Duplicate: {dup['message'].message_id} - {dup['result'].reasoning}")
        
    except Exception as e:
        logger.error(f"Duplicate detection failed: {e}")
        state['errors'].append(f"Duplicate detection error: {str(e)}")
        # Continue with original messages if detection fails
        state['messages'] = state.get('messages', [])
    
    return state

async def optimized_classifier_node(state: WorkflowState) -> WorkflowState:
    """Optimized classifier using rule-based logic"""
    logger.info("🤖 Optimized Classifier: Analyzing messages with rule-based logic")
    state['current_step'] = 'classifier'
    
    try:
        classified_messages = []
        
        for message in state.get('messages', []):
            logger.info(f"Processing message: {message.content[:50]}...")
            
            # Check if message already has a ticket created
            if message.message_id in state.get('ticket_links', {}):
                logger.info(f"Message {message.message_id} already has ticket, skipping")
                continue
            
            # Check if we already processed this message
            message_key = f"{message.message_id}_{message.thread_id}"
            if message_key in state.get('processed_messages', set()):
                logger.info(f"Message already processed, skipping: {message_key}")
                continue
            
            # Use rule-based classification instead of LLM
            classified = rule_based_classification(message)
            
            if classified.is_support_request:
                logger.info(f"Message classified as support request (confidence: {classified.confidence})")
                classified_messages.append(classified)
                
                # Mark message as processed
                if 'processed_messages' not in state:
                    state['processed_messages'] = set()
                state['processed_messages'].add(message_key)
            else:
                logger.info(f"Message not classified as support request: {classified.reasoning}")
        
        state['classified_messages'] = classified_messages
        logger.info(f"Identified {len(classified_messages)} support requests using rule-based logic")
        
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        state['errors'].append(f"Classification error: {str(e)}")
    
    return state

async def optimized_summary_node(state: WorkflowState) -> WorkflowState:
    """Optimized summary using simple text processing"""
    logger.info("📝 Optimized Summary: Creating ticket summaries with simple processing")
    state['current_step'] = 'summary'
    
    try:
        summarized_tickets = []
        
        for classified_msg in state.get('classified_messages', []):
            # Use simple summary creation instead of LLM
            summary = create_simple_summary(classified_msg.original_message)
            summarized_tickets.append(summary)
        
        state['summarized_tickets'] = summarized_tickets
        logger.info(f"Generated {len(summarized_tickets)} ticket summaries using simple processing")
        
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        state['errors'].append(f"Summary error: {str(e)}")
    
    return state

async def optimized_category_extractor_node(state: WorkflowState) -> WorkflowState:
    """Optimized category extraction using rule-based logic"""
    logger.info("🏷️ Optimized Category Extractor: Categorizing tickets with rule-based logic")
    state['current_step'] = 'category_extractor'
    
    try:
        categorized_tickets = []
        
        for i, summary in enumerate(state.get('summarized_tickets', [])):
            # Get the original message for context
            original_message = state['classified_messages'][i].original_message
            
            # Use rule-based categorization instead of LLM
            categorized = rule_based_categorization(original_message, summary)
            categorized_tickets.append(categorized)
        
        state['categorized_tickets'] = categorized_tickets
        logger.info(f"Categorized {len(categorized_tickets)} tickets using rule-based logic")
        
    except Exception as e:
        logger.error(f"Categorization failed: {e}")
        state['errors'].append(f"Category error: {str(e)}")
    
    return state

async def servicenow_node(state: WorkflowState) -> WorkflowState:
    """Create tickets in ServiceNow (unchanged)"""
    logger.info("🎫 ServiceNow: Creating tickets")
    state['current_step'] = 'servicenow'
    
    try:
        from tools.servicenowTool import build_incident_assignment_fields
        
        credentials_manager = CredentialsManager()
        servicenow = ServiceNowAPI(credentials_manager.servicenow_credentials)
        
        created_tickets = []
        newly_created_tickets = []
        summaries = state.get('summarized_tickets', [])
        categories = state.get('categorized_tickets', [])
        classified_messages = state.get('classified_messages', [])
        
        for i, (summary, category, classified_msg) in enumerate(zip(summaries, categories, classified_messages)):
            original_msg = classified_msg.original_message
            correlation_id = original_msg.message_id
            
            logger.info(f"Processing ticket {i+1} for message {correlation_id}")
            logger.info(f"  Message content: {original_msg.content[:100]}...")
            
            # Check in-memory map first
            existing_number = state.get('ticket_links', {}).get(correlation_id)
            if existing_number:
                logger.info(f"Incident already created for message {correlation_id}: {existing_number}; skipping creation")
                continue
            
            # Check ServiceNow by correlation_id to avoid duplicates
            logger.info(f"Checking for existing incident with correlation_id: {correlation_id}")
            existing = await servicenow.find_incident_by_correlation(correlation_id)
            if existing:
                logger.info(f"Found existing incident {existing.number} for message {correlation_id}; linking and skipping creation")
                if 'ticket_links' not in state:
                    state['ticket_links'] = {}
                state['ticket_links'][correlation_id] = existing.number
                created_tickets.append(existing)
                continue
            else:
                logger.info(f"No existing incident found for correlation_id: {correlation_id}; will create new ticket")
            
            # Resolve caller and assignment
            caller_email = getattr(original_msg, 'user_email', None)
            caller_name = original_msg.user_name
            group_name = category.assignment_group
            
            logger.info(f"Resolving caller for message {correlation_id}")
            logger.info(f"  User ID: {original_msg.user_id}")
            logger.info(f"  User Name: {caller_name}")
            logger.info(f"  User Email: {caller_email}")
            logger.info(f"  Thread ID: {original_msg.thread_id}")
            logger.info(f"  Space ID: {original_msg.space_id}")
            
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
                'assignment_group_name': group_name,
                'correlation_id': correlation_id,
            }
            
            ticket_data.update(assignment_fields)
            
            ticket = await servicenow.create_incident(ticket_data)
            created_tickets.append(ticket)
            newly_created_tickets.append({
                'ticket': ticket,
                'correlation_id': correlation_id,
                'original_message': original_msg
            })
            
            if 'ticket_links' not in state:
                state['ticket_links'] = {}
            state['ticket_links'][correlation_id] = ticket.number
            
            logger.info(f"Created ticket {ticket.number} for message {correlation_id}")
        
        state['servicenow_tickets'] = created_tickets
        state['newly_created_tickets'] = newly_created_tickets
        logger.info(f"Created/linked {len(created_tickets)} ServiceNow tickets ({len(newly_created_tickets)} newly created)")
        
    except Exception as e:
        logger.error(f"ServiceNow creation failed: {e}")
        state['errors'].append(f"ServiceNow error: {str(e)}")
    
    return state

async def notification_node(state: WorkflowState) -> WorkflowState:
    """Send notifications back to Google Chat (unchanged)"""
    logger.info("📢 Notification: Sending updates to Google Chat")
    state['current_step'] = 'notification'
    
    try:
        credentials_manager = CredentialsManager()
        google_chat = GoogleChatAPI(credentials_manager.google_credentials)
        
        newly_created_tickets = state.get('newly_created_tickets', [])
        notifications_sent = []
        
        logger.info(f"Processing {len(newly_created_tickets)} newly created tickets for notifications")
        
        # Log details of each ticket to be notified
        for i, ticket_info in enumerate(newly_created_tickets):
            logger.info(f"  Ticket {i+1}: {ticket_info['ticket'].number} for message {ticket_info['correlation_id']}")
        
        for ticket_info in newly_created_tickets:
            ticket = ticket_info['ticket']
            original_msg = ticket_info['original_message']
            
            servicenow_url = credentials_manager.servicenow_credentials['instance_url']
            ticket_url = f"{servicenow_url}/nav_to.do?uri=incident.do?sys_id={ticket.sys_id}"
            
            notification_text = f"""
🎫 **Support Ticket Created**

**Ticket Number:** {ticket.number}
**Title:** {ticket.short_description}
**Status:** {ticket.state}
**Priority:** {ticket.priority}

**View Ticket:** [Open in ServiceNow]({ticket_url})

Your request has been processed and a ticket has been created. You will receive updates as the issue progresses.
"""
            
            space_id = original_msg.space_id
            if not space_id.startswith('spaces/'):
                space_id = f"spaces/{space_id}"
            
            # Handle thread ID - it could be full path or just ID
            thread_id = original_msg.thread_id
            if thread_id.startswith('spaces/'):
                # Full thread path provided, use as is
                # The Google Chat API will handle this correctly now
                pass
            elif '.' in thread_id:
                # Thread ID with message suffix, extract just the thread part
                thread_id = thread_id.split('.')[0]
                # Convert to full path if we have space_id
                if not thread_id.startswith('spaces/'):
                    space_id_clean = space_id.replace('spaces/', '')
                    thread_id = f"spaces/{space_id_clean}/threads/{thread_id}"
            
            logger.info(f"Attempting to send notification for ticket {ticket.number}")
            logger.info(f"  Space ID: {space_id}")
            logger.info(f"  Original Thread ID: {original_msg.thread_id}")
            logger.info(f"  Processed Thread ID: {thread_id}")
            
            # Log the final URL that will be used
            if thread_id.startswith('spaces/') and '/threads/' in thread_id:
                final_url = f"https://chat.googleapis.com/v1/{thread_id}/messages"
            else:
                space_id_clean = space_id.replace('spaces/', '')
                final_url = f"https://chat.googleapis.com/v1/spaces/{space_id_clean}/threads/{thread_id}/messages"
            logger.info(f"  Final URL: {final_url}")
            
            try:
                # Use fallback method: try thread first, then space as reply
                success = await google_chat.send_message_with_fallback(
                    space_id=space_id,
                    thread_id=thread_id,
                    message=notification_text,
                    original_message_id=original_msg.message_id
                )
                
                if success:
                    notifications_sent.append({
                        'ticket_number': ticket.number,
                        'message_id': original_msg.message_id,
                        'sent_at': datetime.now().isoformat(),
                        'sent_via': 'thread' if thread_id else 'space_fallback'
                    })
                    logger.info(f"✅ Notification sent successfully for ticket {ticket.number}")
                else:
                    logger.error(f"❌ Failed to send notification for ticket {ticket.number} (both thread and fallback failed)")
            except Exception as e:
                logger.error(f"❌ Exception while sending notification for ticket {ticket.number}: {str(e)}")
        
        state['notifications_sent'] = notifications_sent
        logger.info(f"Sent {len(notifications_sent)} notifications")
        
    except Exception as e:
        logger.error(f"Notification failed: {e}")
        state['errors'].append(f"Notification error: {str(e)}")
    
    return state

async def tracker_node(state: WorkflowState) -> WorkflowState:
    """Monitor ticket status (unchanged)"""
    logger.info("👁️ Tracker: Monitoring ticket status")
    state['current_step'] = 'tracker'
    
    # Placeholder for ticket monitoring logic
    logger.info("Tracking system active")
    
    return state

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
        
        # PRE-FILTER: Remove admin notification messages before processing
        filtered_messages = []
        admin_notifications_filtered = 0
        
        for message in messages:
            # Check if this is an admin notification message
            content_lower = message.content.lower()
            admin_patterns = [
                '🎫 **support ticket created**',
                'ticket number: inc',
                'your request has been processed',
                'ticket has been created',
                'view ticket: [open in servicenow]',
                'status:',
                'priority:',
                'you will receive updates as the issue progresses'
            ]
            
            is_admin_notification = any(pattern in content_lower for pattern in admin_patterns)
            
            # Check if this is from the bot itself (should be excluded)
            is_bot_message = (
                message.user_name.lower() in ['support ticket automation', 'bot', 'admin'] or
                'chat-bot' in message.user_id.lower() or
                'bot' in message.user_id.lower()
            )
            
            if is_admin_notification or is_bot_message:
                logger.info(f"🚫 Pre-filtered admin/bot message: {message.message_id} (User: {message.user_name})")
                admin_notifications_filtered += 1
                continue
            else:
                # Only include messages from actual users
                filtered_messages.append(message)
                logger.info(f"✅ User message included: {message.message_id} (User: {message.user_name})")
        
        state['messages'] = filtered_messages
        
        logger.info(f"Message filtering complete:")
        logger.info(f"  - Total messages fetched: {len(messages)}")
        logger.info(f"  - Admin notifications filtered: {admin_notifications_filtered}")
        logger.info(f"  - User messages for processing: {len(filtered_messages)}")
        
    except Exception as e:
        logger.error(f"Message fetching failed: {e}")
        state['errors'].append(f"Message fetch error: {str(e)}")
    
    return state
