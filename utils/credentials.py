"""
Credentials Manager for Support Ticket Automation System
Handles loading and managing all required API credentials
"""

import os
from typing import Dict
from dotenv import load_dotenv

class CredentialsManager:
    """Manages all required credentials and configurations"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        self.google_credentials = self._load_google_credentials()
        self.servicenow_credentials = self._load_servicenow_credentials()
        self.gemini_api_key = self._load_gemini_credentials()
    
    def _load_google_credentials(self) -> Dict:
        """Load Google Chat API credentials"""
        return {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'refresh_token': os.getenv('GOOGLE_REFRESH_TOKEN'),
            'project_id': os.getenv('GOOGLE_PROJECT_ID'),
            'space_id': os.getenv('GOOGLE_CHAT_SPACE_ID'),
            'service_account_file': os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE'),
            # Optional API key for Google Chat API (used as query param 'key')
            'chat_api_key': os.getenv('GOOGLE_CHAT_API_KEY')
        }
    
    def _load_servicenow_credentials(self) -> Dict:
        """Load ServiceNow API credentials"""
        return {
            'instance_url': os.getenv('SERVICENOW_INSTANCE_URL'),
            'username': os.getenv('SERVICENOW_USERNAME'),
            'password': os.getenv('SERVICENOW_PASSWORD'),
            'client_id': os.getenv('SERVICENOW_CLIENT_ID'),
            'client_secret': os.getenv('SERVICENOW_CLIENT_SECRET')
        }
    
    def _load_gemini_credentials(self) -> str:
        """Load Google Gemini API key"""
        return os.getenv('GOOGLE_GEMINI_API_KEY')
    
    def validate_credentials(self) -> Dict:
        """Validate that all required credentials are present"""
        missing = []
        
        # Check Google credentials
        for key in ['client_id', 'client_secret', 'project_id']:
            if not self.google_credentials.get(key):
                missing.append(f'GOOGLE_{key.upper()}')
        
        # Check if either refresh_token or service_account_file is present
        if not (self.google_credentials.get('refresh_token') or 
                self.google_credentials.get('service_account_file')):
            missing.append('GOOGLE_REFRESH_TOKEN or GOOGLE_SERVICE_ACCOUNT_FILE')
        
        # Check ServiceNow credentials
        for key in ['instance_url', 'username', 'password']:
            if not self.servicenow_credentials.get(key):
                missing.append(f'SERVICENOW_{key.upper()}')
        
        # Check Gemini API key
        if not self.gemini_api_key:
            missing.append('GOOGLE_GEMINI_API_KEY')
        
        return {
            'valid': len(missing) == 0,
            'missing': missing
        }
