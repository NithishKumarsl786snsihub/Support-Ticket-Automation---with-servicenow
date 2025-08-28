"""
ServiceNow API Integration
Handles communication with ServiceNow for ticket management
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ServiceNowTicket:
    """ServiceNow ticket representation"""
    sys_id: str
    number: str
    state: str
    short_description: str
    description: str
    priority: str
    category: str
    assigned_to: str
    created_on: str
    updated_on: str

class ServiceNowAPI:
    """ServiceNow API integration"""
    
    def __init__(self, credentials: Dict):
        self.credentials = credentials
        self.base_url = f"{credentials['instance_url']}/api/now"
        self.session = httpx.AsyncClient(
            auth=(credentials['username'], credentials['password']),
            headers={'Content-Type': 'application/json'}
        )
    
    async def find_incident_by_correlation(self, correlation_id: str) -> Optional[ServiceNowTicket]:
        """Find existing incident by correlation_id to prevent duplicates"""
        try:
            url = f"{self.base_url}/table/incident"
            params = {
                'sysparm_limit': '1',
                'sysparm_query': f'correlation_id={correlation_id}',
                'sysparm_fields': 'sys_id,number,state,short_description,description,priority,category,assigned_to,sys_created_on,sys_updated_on'
            }
            response = await self.session.get(url, params=params)
            if response.status_code == 200:
                results = response.json().get('result', [])
                if results:
                    r = results[0]
                    return ServiceNowTicket(
                        sys_id=r['sys_id'],
                        number=r['number'],
                        state=r['state'],
                        short_description=r.get('short_description', ''),
                        description=r.get('description', ''),
                        priority=r.get('priority', ''),
                        category=r.get('category', ''),
                        assigned_to=(r.get('assigned_to') or ''),
                        created_on=r.get('sys_created_on', ''),
                        updated_on=r.get('sys_updated_on', '')
                    )
            else:
                logger.error(f"Failed to search incident by correlation_id: {response.text}")
        except Exception as e:
            logger.error(f"Error searching incident by correlation_id: {e}")
        return None
    
    async def create_incident(self, ticket_data: Dict) -> ServiceNowTicket:
        """Create new incident in ServiceNow"""
        url = f"{self.base_url}/table/incident"
        
        payload = {
            'short_description': ticket_data['title'],
            'description': ticket_data['description'],
            'priority': ticket_data['priority'],
            'category': ticket_data['category'],
            'subcategory': ticket_data.get('subcategory', ''),
            'caller_id': ticket_data.get('caller_id', ''),
            'urgency': ticket_data.get('urgency', '3'),
            'impact': ticket_data.get('impact', '3'),
            'assignment_group': ticket_data.get('assignment_group', ''),
            'work_notes': f"Auto-created from Google Chat message by AI Agent",
            'correlation_id': ticket_data.get('correlation_id', '')
        }
        
        response = await self.session.post(url, json=payload)
        if response.status_code == 201:
            result = response.json()['result']
            return ServiceNowTicket(
                sys_id=result['sys_id'],
                number=result['number'],
                state=result['state'],
                short_description=result['short_description'],
                description=result['description'],
                priority=result['priority'],
                category=result['category'],
                assigned_to=result.get('assigned_to', ''),
                created_on=result['sys_created_on'],
                updated_on=result['sys_updated_on']
            )
        else:
            logger.error(f"Failed to create incident: {response.text}")
            raise Exception(f"ServiceNow API error: {response.status_code}")
    
    async def update_incident(self, sys_id: str, updates: Dict) -> bool:
        """Update existing incident"""
        url = f"{self.base_url}/table/incident/{sys_id}"
        
        response = await self.session.patch(url, json=updates)
        return response.status_code == 200
    
    async def get_incident(self, sys_id: str) -> Optional[ServiceNowTicket]:
        """Fetch incident details"""
        url = f"{self.base_url}/table/incident/{sys_id}"
        
        response = await self.session.get(url)
        if response.status_code == 200:
            result = response.json()['result']
            return ServiceNowTicket(
                sys_id=result['sys_id'],
                number=result['number'],
                state=result['state'],
                short_description=result['short_description'],
                description=result['description'],
                priority=result['priority'],
                category=result['category'],
                assigned_to=result.get('assigned_to', ''),
                created_on=result['sys_created_on'],
                updated_on=result['sys_updated_on']
            )
        return None
