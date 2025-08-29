"""
Duplicate Detection Agent using LangChain
Intelligently detects duplicate support requests to prevent duplicate ticket creation
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import re

from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from utils.models import SupportMessage, ServiceNowTicket
from api.servicenow import ServiceNowAPI
from utils.credentials import CredentialsManager

logger = logging.getLogger(__name__)

class DuplicateDetectionResult:
    """Result of duplicate detection analysis"""
    
    def __init__(self, is_duplicate: bool, confidence: float, reasoning: str, 
                 similar_tickets: List[ServiceNowTicket] = None):
        self.is_duplicate = is_duplicate
        self.confidence = confidence
        self.reasoning = reasoning
        self.similar_tickets = similar_tickets or []
    
    def __str__(self):
        return f"Duplicate: {self.is_duplicate} (Confidence: {self.confidence:.2f}) - {self.reasoning}"

class DuplicateDetectionParser(BaseOutputParser):
    """Parse the output of duplicate detection LLM"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse LLM output to extract duplicate detection results"""
        try:
            # Extract JSON-like structure from LLM response
            import json
            
            # Clean up the response text
            cleaned_text = text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            # Parse JSON
            result = json.loads(cleaned_text.strip())
            
            return {
                "is_duplicate": result.get("is_duplicate", False),
                "confidence": result.get("confidence", 0.0),
                "reasoning": result.get("reasoning", ""),
                "similarity_score": result.get("similarity_score", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Failed to parse duplicate detection result: {e}")
            # Fallback to rule-based detection
            return {
                "is_duplicate": False,
                "confidence": 0.0,
                "reasoning": f"Parse error, using fallback: {str(e)}",
                "similarity_score": 0.0
            }

class DuplicateDetectionAgent:
    """Agent for detecting duplicate support requests"""
    
    def __init__(self):
        self.credentials_manager = CredentialsManager()
        self.servicenow = ServiceNowAPI(self.credentials_manager.servicenow_credentials)
        
        # Initialize LLM for intelligent duplicate detection
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.1,
                max_tokens=1000
            )
        except Exception as e:
            logger.warning(f"Failed to initialize LLM for duplicate detection: {e}")
            self.llm = None
        
        # Duplicate detection prompt
        self.duplicate_prompt = PromptTemplate(
            input_variables=["message_content", "existing_tickets"],
            template="""
You are an expert support ticket duplicate detection agent. Your job is to analyze if a new support request is a duplicate of existing tickets.

NEW REQUEST:
{message_content}

EXISTING TICKETS:
{existing_tickets}

ANALYSIS INSTRUCTIONS:
1. Check if the new request is similar to any existing tickets
2. Look for:
   - Same issue/problem description
   - Same user/requester
   - Same time period (within 24 hours)
   - Similar technical details
   - Notification messages that are not actual requests

3. Determine if this is a duplicate request

RESPONSE FORMAT (JSON):
{{
    "is_duplicate": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation of why this is/isn't a duplicate",
    "similarity_score": 0.0-1.0
}}

IMPORTANT: If the message contains ticket creation confirmations, ticket numbers, or is clearly a notification, mark it as a duplicate.
"""
        )
        
        # Rule-based duplicate detection patterns
        self.duplicate_patterns = [
            r"🎫 \*\*Support Ticket Created\*\*",
            r"Ticket Number: INC\d+",
            r"Your request has been processed",
            r"ticket has been created",
            r"View Ticket: \[Open in ServiceNow\]",
            r"Status: \d+",
            r"Priority: \d+"
        ]
        
        self.parser = DuplicateDetectionParser()
    
    async def detect_duplicates(self, message: SupportMessage, 
                              recent_tickets: List[ServiceNowTicket] = None) -> DuplicateDetectionResult:
        """
        Detect if a message is a duplicate request
        
        Args:
            message: The message to analyze
            recent_tickets: List of recent tickets to compare against
            
        Returns:
            DuplicateDetectionResult with analysis
        """
        try:
            # Step 1: Quick rule-based check for obvious duplicates
            if self._is_obvious_duplicate(message.content):
                logger.info(f"Message {message.message_id} identified as obvious duplicate via rules")
                return DuplicateDetectionResult(
                    is_duplicate=True,
                    confidence=0.95,
                    reasoning="Message contains ticket creation confirmation or notification content"
                )
            
            # Step 2: Get recent tickets if not provided
            if recent_tickets is None:
                recent_tickets = await self._get_recent_tickets()
            
            # Step 3: Check for exact correlation ID match
            existing_ticket = await self._check_correlation_id(message.message_id)
            if existing_ticket:
                logger.info(f"Message {message.message_id} has existing ticket: {existing_ticket.number}")
                return DuplicateDetectionResult(
                    is_duplicate=True,
                    confidence=1.0,
                    reasoning=f"Message already has ticket {existing_ticket.number}",
                    similar_tickets=[existing_ticket]
                )
            
            # Step 4: Use LLM for intelligent duplicate detection
            if self.llm and recent_tickets:
                return await self._llm_duplicate_detection(message, recent_tickets)
            
            # Step 5: Fallback to rule-based similarity check
            return await self._rule_based_duplicate_detection(message, recent_tickets)
            
        except Exception as e:
            logger.error(f"Error in duplicate detection: {e}")
            # Default to not duplicate if detection fails
            return DuplicateDetectionResult(
                is_duplicate=False,
                confidence=0.0,
                reasoning=f"Detection failed: {str(e)}"
            )
    
    def _is_obvious_duplicate(self, content: str) -> bool:
        """Check if content is obviously a duplicate using pattern matching"""
        content_lower = content.lower()
        
        # Check for notification patterns
        for pattern in self.duplicate_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        # Check for ticket creation confirmations
        if any(phrase in content_lower for phrase in [
            "support ticket created",
            "ticket number:",
            "your request has been processed",
            "ticket has been created",
            "view ticket:",
            "open in servicenow"
        ]):
            return True
        
        return False
    
    async def _check_correlation_id(self, message_id: str) -> Optional[ServiceNowTicket]:
        """Check if a message already has a ticket via correlation ID"""
        try:
            return await self.servicenow.find_incident_by_correlation(message_id)
        except Exception as e:
            logger.error(f"Error checking correlation ID: {e}")
            return None
    
    async def _get_recent_tickets(self, hours: int = 24) -> List[ServiceNowTicket]:
        """Get recent tickets for comparison"""
        try:
            return await self.servicenow.get_recent_incidents(hours)
        except Exception as e:
            logger.error(f"Error getting recent tickets: {e}")
            return []
    
    async def _llm_duplicate_detection(self, message: SupportMessage, 
                                     recent_tickets: List[ServiceNowTicket]) -> DuplicateDetectionResult:
        """Use LLM for intelligent duplicate detection"""
        try:
            # Format existing tickets for LLM
            tickets_text = self._format_tickets_for_llm(recent_tickets)
            
            # Create prompt
            prompt = self.duplicate_prompt.format(
                message_content=message.content,
                existing_tickets=tickets_text
            )
            
            # Get LLM response
            response = await self.llm.ainvoke(prompt)
            
            # Parse response
            result = self.parser.parse(response.content)
            
            logger.info(f"LLM duplicate detection result: {result}")
            
            return DuplicateDetectionResult(
                is_duplicate=result["is_duplicate"],
                confidence=result["confidence"],
                reasoning=result["reasoning"]
            )
            
        except Exception as e:
            logger.error(f"LLM duplicate detection failed: {e}")
            # Fallback to rule-based
            return await self._rule_based_duplicate_detection(message, recent_tickets)
    
    async def _rule_based_duplicate_detection(self, message: SupportMessage, 
                                            recent_tickets: List[ServiceNowTicket]) -> DuplicateDetectionResult:
        """Fallback rule-based duplicate detection"""
        try:
            content_lower = message.content.lower()
            
            # Check for similar content in recent tickets
            for ticket in recent_tickets:
                if ticket.description:
                    ticket_lower = ticket.description.lower()
                    
                    # Simple similarity check
                    common_words = set(content_lower.split()) & set(ticket_lower.split())
                    if len(common_words) >= 3:  # At least 3 common words
                        similarity = len(common_words) / max(len(content_lower.split()), len(ticket_lower.split()))
                        
                        if similarity > 0.3:  # 30% similarity threshold
                            return DuplicateDetectionResult(
                                is_duplicate=True,
                                confidence=similarity,
                                reasoning=f"Similar to ticket {ticket.number} (similarity: {similarity:.2f})",
                                similar_tickets=[ticket]
                            )
            
            # No duplicates found
            return DuplicateDetectionResult(
                is_duplicate=False,
                confidence=0.8,
                reasoning="No similar tickets found in recent history"
            )
            
        except Exception as e:
            logger.error(f"Rule-based duplicate detection failed: {e}")
            return DuplicateDetectionResult(
                is_duplicate=False,
                confidence=0.0,
                reasoning=f"Detection failed: {str(e)}"
            )
    
    def _format_tickets_for_llm(self, tickets: List[ServiceNowTicket]) -> str:
        """Format tickets for LLM consumption"""
        if not tickets:
            return "No recent tickets found"
        
        formatted = []
        for ticket in tickets[:5]:  # Limit to 5 most recent
            formatted.append(f"""
Ticket: {ticket.number}
Title: {ticket.short_description}
Description: {ticket.description[:200]}...
Created: {ticket.created_on}
Status: {ticket.state}
""")
        
        return "\n".join(formatted)
    
    async def get_duplicate_summary(self, messages: List[SupportMessage]) -> Dict[str, Any]:
        """Get summary of duplicate detection for multiple messages"""
        results = []
        duplicates_found = 0
        
        for message in messages:
            result = await self.detect_duplicates(message)
            results.append({
                'message_id': message.message_id,
                'content_preview': message.content[:100] + "...",
                'result': result
            })
            
            if result.is_duplicate:
                duplicates_found += 1
        
        return {
            'total_messages': len(messages),
            'duplicates_found': duplicates_found,
            'unique_requests': len(messages) - duplicates_found,
            'results': results
        }
