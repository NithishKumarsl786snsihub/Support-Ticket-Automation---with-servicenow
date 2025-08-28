"""
Test script to directly process a message without fetching from Google Chat API
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path to import from project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.google_chat import SupportMessage
from utils.models import WorkflowState
from agents.classifier import ClassifierAgent
from agents.summarizer import SummaryAgent
from agents.categorizer import CategoryExtractorAgent
from utils.credentials import CredentialsManager
from langchain_google_genai import ChatGoogleGenerativeAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_direct_message_processing():
    """Test direct message processing without API calls"""
    
    # Create a test message similar to what was shown in the screenshot
    test_message = SupportMessage(
        message_id=f"test_{int(datetime.now().timestamp())}",
        thread_id="test_thread",
        user_id="user_123",
        user_name="Nithish Kumar S L",
        content="i need a support in the system support @pf 2 please check and recover soon and resolve it i have meeting with in a hour",
        timestamp=datetime.now(),
        space_id="AAQAWaIEuf4"  # From the screenshot
    )
    
    print("\n🧪 Testing direct message processing")
    print("=" * 60)
    print(f"Message: {test_message.content}")
    print(f"From: {test_message.user_name}")
    print("=" * 60)
    
    # Initialize state
    state = WorkflowState(
        messages=[test_message],
        classified_messages=[],
        summarized_tickets=[],
        categorized_tickets=[],
        servicenow_tickets=[],
        notifications_sent=[],
        current_step='',
        errors=[]
    )
    
    # Check if we have GEMINI API key
    credentials_manager = CredentialsManager()
    gemini_api_key = credentials_manager.gemini_api_key
    
    if not gemini_api_key or gemini_api_key == "your_gemini_api_key_here":
        print("\n⚠️ No valid Gemini API key found in .env file")
        print("Using mock processing instead of actual AI processing")
        
        # Mock classification
        from utils.models import ClassifiedMessage
        classified_message = ClassifiedMessage(
            original_message=test_message,
            is_support_request=True,
            confidence=0.95,
            reasoning="This is clearly a support request mentioning system issues and urgent recovery needed."
        )
        state['classified_messages'] = [classified_message]
        
        # Mock summary
        from utils.models import SummarizedTicket
        summary = SummarizedTicket(
            title="System Support Request - Urgent Meeting Preparation",
            description="User needs urgent support with system issue before an upcoming meeting within the hour.",
            problem_statement="System issue requiring immediate recovery",
            user_impact="User has a meeting within an hour and needs the system working"
        )
        state['summarized_tickets'] = [summary]
        
        # Mock categorization
        from utils.models import CategorizedTicket, TicketCategory, TicketPriority
        categorized = CategorizedTicket(
            category=TicketCategory.SOFTWARE,
            subcategory="System Access",
            priority=TicketPriority.HIGH,
            urgency="2",
            service="IT Support",
            assignment_group="IT Support"
        )
        state['categorized_tickets'] = [categorized]
        
        print("\n✅ Mock processing complete!")
        print("\n📋 Results:")
        print(f"Classification: Support Request (95% confidence)")
        print(f"Title: {summary.title}")
        print(f"Description: {summary.description}")
        print(f"Category: {categorized.category.value}")
        print(f"Priority: {categorized.priority.value}")
        
    else:
        print("\n✅ Valid Gemini API key found, processing with AI...")
        
        try:
            # Create LLM
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=gemini_api_key,
                temperature=0.1
            )
            
            # Process with classifier
            print("\nClassifying message...")
            classifier = ClassifierAgent(llm)
            classified = await classifier.classify_message(test_message)
            state['classified_messages'] = [classified]
            print(f"Classification: {'Support Request' if classified.is_support_request else 'Not a Support Request'} ({classified.confidence:.0%} confidence)")
            print(f"Reasoning: {classified.reasoning}")
            
            if classified.is_support_request:
                # Process with summarizer
                print("\nGenerating ticket summary...")
                summary_agent = SummaryAgent(llm)
                summary = await summary_agent.summarize_message(classified)
                state['summarized_tickets'] = [summary]
                print(f"Title: {summary.title}")
                print(f"Description: {summary.description}")
                
                # Process with categorizer
                print("\nCategorizing ticket...")
                category_agent = CategoryExtractorAgent(llm)
                categorized = await category_agent.categorize_ticket(summary)
                state['categorized_tickets'] = [categorized]
                print(f"Category: {categorized.category.value}")
                print(f"Priority: {categorized.priority.value}")
                print(f"Assignment Group: {categorized.assignment_group}")
            
        except Exception as e:
            print(f"\n❌ Error during processing: {str(e)}")
            state['errors'].append(str(e))
    
    # Print final state summary
    print("\n📊 Final State Summary:")
    print(f"Messages: {len(state['messages'])}")
    print(f"Support Requests: {len(state['classified_messages'])}")
    print(f"Tickets Summarized: {len(state['summarized_tickets'])}")
    print(f"Tickets Categorized: {len(state['categorized_tickets'])}")
    print(f"Errors: {len(state['errors'])}")
    
    if state['errors']:
        print("\n⚠️ Errors encountered:")
        for error in state['errors']:
            print(f"  - {error}")
    
    return state

if __name__ == "__main__":
    asyncio.run(test_direct_message_processing())
