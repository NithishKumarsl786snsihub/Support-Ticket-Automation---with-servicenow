"""
Category Extractor Agent
Categorizes and prioritizes support tickets
"""

import json
import logging
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

from utils.models import TicketSummary, TicketCategory, Category, Priority

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CategoryExtractorAgent:
    """Agent to categorize and prioritize tickets"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = PromptTemplate(
            input_variables=["title", "description", "problem_statement"],
            template="""
            Analyze this support ticket and determine appropriate categorization:

            Title: {title}
            Description: {description}
            Problem: {problem_statement}

            Categorize based on:
            
            Categories: hardware, software, network, access, email, printing, security, other
            
            Priority Levels:
            - "1": Critical - System down, security breach, critical business impact
            - "2": High - Major functionality affected, multiple users impacted
            - "3": Moderate - Minor issues, single user affected, workarounds available
            - "4": Low - Minor issues, no immediate impact
            - "5": Planning - Future planning, no immediate action needed

            Assignment Groups:
            - IT Support (general issues)
            - Network Team (connectivity, VPN, infrastructure)
            - Security Team (access, permissions, security)
            - Application Support (software-specific issues)

            Respond in JSON format:
            {{
                "category": "category_name",
                "subcategory": "specific_subcategory",
                "priority": "priority_number",
                "urgency": "1-4 scale",
                "assignment_group": "team_to_assign"
            }}
            """
        )
    
    async def categorize_ticket(self, summary: TicketSummary) -> TicketCategory:
        """Categorize and prioritize ticket"""
        try:
            formatted_prompt = self.prompt.format(
                title=summary.title,
                description=summary.description,
                problem_statement=summary.problem_statement
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
                    "category": "other",
                    "subcategory": "General",
                    "priority": "3",
                    "urgency": "3",
                    "assignment_group": "IT Support"
                }
            
            return TicketCategory(
                category=Category(result['category']),
                priority=Priority(result['priority']),
                subcategory=result['subcategory'],
                urgency=result['urgency'],
                assignment_group=result['assignment_group']
            )
            
        except Exception as e:
            logger.error(f"Error categorizing ticket: {e}")
            # Return default categorization
            return TicketCategory(
                category=Category.OTHER,
                priority=Priority.MODERATE,
                subcategory="General",
                urgency="3",
                assignment_group="IT Support"
            )
