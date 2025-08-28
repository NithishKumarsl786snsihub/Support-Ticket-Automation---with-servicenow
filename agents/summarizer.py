"""
Summary Agent
Creates structured ticket summaries from classified messages
"""

import logging
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from utils.models import ClassifiedMessage, TicketSummary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SummaryAgent:
    """Agent to create ticket summaries from classified messages"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a support ticket summarizer. Convert this unstructured support message into a clear, professional ticket."),
            ("human", "User: {user_name}\nOriginal Message: {message_content}\n\nCreate a structured summary with:\n1. Professional title (max 80 characters)\n2. Clear description of the issue\n3. Concise problem statement\n4. User impact assessment\n5. Urgency level\n\nRespond in JSON format:\n{{\n  \"title\": \"Brief, professional title\",\n  \"description\": \"Detailed description of the issue\",\n  \"problem_statement\": \"Clear problem statement\",\n  \"user_impact\": \"Impact on user/workflow\",\n  \"urgency_level\": \"High/Medium/Low\"\n}}")
        ])
        
        self.output_parser = JsonOutputParser()
    
    async def summarize_message(self, classified_message: ClassifiedMessage) -> TicketSummary:
        """Create a structured summary from a classified message"""
        
        try:
            # Format the prompt
            formatted_prompt = self.prompt.format_messages(
                user_name=classified_message.original_message.user_name,
                message_content=classified_message.original_message.content
            )
            
            # Generate summary
            response = await self.llm.ainvoke(formatted_prompt)
            
            # Parse the response
            summary_data = self.output_parser.parse(response.content)
            
            # Create TicketSummary object
            summary = TicketSummary(
                title=summary_data.get('title', 'Support Request'),
                description=summary_data.get('description', 'No description provided'),
                problem_statement=summary_data.get('problem_statement', 'Problem not specified'),
                user_impact=summary_data.get('user_impact', 'Impact not specified'),
                urgency_level=summary_data.get('urgency_level', 'Medium')
            )
            
            logger.info(f"Created summary: {summary.title}")
            return summary
            
        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            # Return a default summary
            return TicketSummary(
                title="Support Request",
                description=classified_message.original_message.content,
                problem_statement="Issue requires attention",
                user_impact="User workflow affected",
                urgency_level="Medium"
            )
