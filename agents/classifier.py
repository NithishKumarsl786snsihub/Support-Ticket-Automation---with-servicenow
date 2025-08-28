"""
Classifier Agent
Determines if a message is a support request
"""

import json
import logging
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

from api.google_chat import SupportMessage
from utils.models import ClassifiedMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClassifierAgent:
    """Agent to classify if message is a support request"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = PromptTemplate(
            input_variables=["message_content", "user_name"],
            template="""
            Analyze the following message to determine if it's a legitimate support request:

            User: {user_name}
            Message: {message_content}

            IMPORTANT: This message mentions "@Support Ticket Automation" or "Support Ticket Automation", 
            so the user is specifically requesting help from the support system.

            Classification Criteria:
            - Contains technical issues, problems, or requests for help
            - Mentions system errors, access issues, or functionality problems
            - Asks for assistance with software, hardware, or services
            - Reports bugs or unexpected behavior
            - Contains words like: "test", "help", "issue", "problem", "error", "down", "broken", "not working"

            NOT support requests:
            - Casual conversations
            - Greetings or social messages
            - Meeting scheduling
            - General announcements

            Since the user mentioned the bot, treat this as a support request unless it's clearly just a greeting.

            Respond in JSON format:
            {{
                "is_support_request": boolean,
                "confidence": float (0.0-1.0),
                "reasoning": "Brief explanation of decision"
            }}
            """
        )
    
    async def classify_message(self, message: SupportMessage) -> ClassifiedMessage:
        """Classify a single message"""
        try:
            formatted_prompt = self.prompt.format(
                message_content=message.content,
                user_name=message.user_name
            )
            
            response = await self.llm.ainvoke([HumanMessage(content=formatted_prompt)])
            
            # Parse JSON response - handle potential formatting issues
            try:
                # Try to extract JSON from the response
                content = response.content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                logger.error(f"Raw response: {response.content}")
                # Fallback to default values
                result = {
                    "is_support_request": True,
                    "confidence": 0.8,
                    "reasoning": "Fallback classification due to parsing error"
                }
            
            return ClassifiedMessage(
                original_message=message,
                is_support_request=result['is_support_request'],
                confidence=result['confidence'],
                reasoning=result['reasoning']
            )
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            # Default to treating as support request to avoid missing tickets
            return ClassifiedMessage(
                original_message=message,
                is_support_request=True,
                confidence=0.5,
                reasoning=f"Classification failed: {str(e)}"
            )
