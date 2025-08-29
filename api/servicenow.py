"""
ServiceNow API Integration
Handles communication with ServiceNow for ticket management
"""

import logging
from typing import Dict, Optional, List
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
            'correlation_id': ticket_data.get('correlation_id', ''),
            'work_notes': f"Auto-created from Google Chat message by AI Agent"
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
    
    async def find_incident_by_correlation(self, correlation_id: str) -> Optional[ServiceNowTicket]:
        """Find incident by correlation ID (message_id)"""
        try:
            # Query ServiceNow for incidents with the correlation ID
            url = f"{self.base_url}/table/incident"
            params = {
                'sysparm_query': f'correlation_id={correlation_id}',
                'sysparm_limit': 1
            }
            
            response = await self.session.get(url, params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result') and len(result['result']) > 0:
                    incident_data = result['result'][0]
                    return ServiceNowTicket(
                        sys_id=incident_data['sys_id'],
                        number=incident_data['number'],
                        state=incident_data['state'],
                        short_description=incident_data['short_description'],
                        description=incident_data['description'],
                        priority=incident_data['priority'],
                        category=incident_data['category'],
                        assigned_to=incident_data.get('assigned_to', ''),
                        created_on=incident_data['sys_created_on'],
                        updated_on=incident_data['sys_updated_on']
                    )
            
            logger.info(f"No incident found with correlation_id: {correlation_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding incident by correlation: {str(e)}")
            return None

    async def get_recent_incidents(self, hours: int = 24) -> List[ServiceNowTicket]:
        """Get recent incidents for duplicate detection"""
        try:
            from datetime import datetime, timedelta
            
            # Calculate time threshold
            threshold_time = datetime.now() - timedelta(hours=hours)
            threshold_str = threshold_time.strftime('%Y-%m-%d %H:%M:%S')
            
            url = f"{self.base_url}/table/incident"
            params = {
                'sysparm_query': f'sys_created_on>={threshold_str}',
                'sysparm_limit': 50,  # Get last 50 incidents
                'sysparm_orderby': 'sys_created_on DESC'
            }
            
            response = await self.session.get(url, params=params)
            if response.status_code == 200:
                result = response.json()
                incidents = []
                
                for incident_data in result.get('result', []):
                    incident = ServiceNowTicket(
                        sys_id=incident_data['sys_id'],
                        number=incident_data['number'],
                        state=incident_data['state'],
                        short_description=incident_data['short_description'],
                        description=incident_data['description'],
                        priority=incident_data['priority'],
                        category=incident_data['category'],
                        assigned_to=incident_data.get('assigned_to', ''),
                        created_on=incident_data['sys_created_on'],
                        updated_on=incident_data['sys_updated_on']
                    )
                    incidents.append(incident)
                
                logger.info(f"Retrieved {len(incidents)} recent incidents for duplicate detection")
                return incidents
            else:
                logger.error(f"Failed to get recent incidents: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting recent incidents: {str(e)}")
            return []
