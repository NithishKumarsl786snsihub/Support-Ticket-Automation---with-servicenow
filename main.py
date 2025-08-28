"""
Support Ticket Automation System - Main Application
LangGraph + LangChain + Google Gemini 1.5 + Google Chat + ServiceNow
"""

import os
import logging
import asyncio
import argparse
import signal
from typing import List, Dict

import uvicorn
from dotenv import load_dotenv

from api.google_chat import SupportMessage
from api.webhook import WebhookHandler
from utils.credentials import CredentialsManager
from utils.scheduler import SchedulerService
from workflow.graph import create_workflow
from utils.models import WorkflowState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupportTicketAutomation:
    """Main automation system orchestrator"""
    
    def __init__(self):
        self.workflow = create_workflow()
        self.credentials_manager = CredentialsManager()
        
    async def run_workflow(self, initial_messages: List[SupportMessage] = None) -> WorkflowState:
        """Execute the complete workflow"""
        
        initial_state = WorkflowState(
            messages=initial_messages or [],
            classified_messages=[],
            summarized_tickets=[],
            categorized_tickets=[],
            servicenow_tickets=[],
            notifications_sent=[],
            current_step='',
            errors=[]
        )
        
        logger.info("🚀 Starting Support Ticket Automation Workflow")
        
        try:
            # Execute the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Log results
            self._log_workflow_results(final_state)
            
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise
    
    def _log_workflow_results(self, state: WorkflowState):
        """Log workflow execution results"""
        
        logger.info("=" * 50)
        logger.info("WORKFLOW EXECUTION SUMMARY")
        logger.info("=" * 50)
        
        logger.info(f"Messages Processed: {len(state.get('messages', []))}")
        logger.info(f"Support Requests Identified: {len(state.get('classified_messages', []))}")
        logger.info(f"Tickets Summarized: {len(state.get('summarized_tickets', []))}")
        logger.info(f"Tickets Categorized: {len(state.get('categorized_tickets', []))}")
        logger.info(f"ServiceNow Tickets Created: {len(state.get('servicenow_tickets', []))}")
        logger.info(f"Notifications Sent: {len(state.get('notifications_sent', []))}")
        logger.info(f"Errors Encountered: {len(state.get('errors', []))}")
        
        if state.get('errors'):
            logger.warning("Errors during execution:")
            for error in state['errors']:
                logger.warning(f"  - {error}")
        
        if state.get('servicenow_tickets'):
            logger.info("Created Tickets:")
            for ticket in state['servicenow_tickets']:
                logger.info(f"  - {ticket.number}: {ticket.short_description}")
        
        logger.info("=" * 50)

def generate_env_template():
    """Generate .env template with required credentials"""
    
    env_template = """
# ==============================================
# SUPPORT TICKET AUTOMATION - ENVIRONMENT VARIABLES
# ==============================================

# Google Gemini API
GOOGLE_GEMINI_API_KEY=your_gemini_api_key_here

# Google Cloud / Chat API Credentials
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_CLIENT_ID=your_oauth_client_id
GOOGLE_CLIENT_SECRET=your_oauth_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token
GOOGLE_SERVICE_ACCOUNT_FILE=path/to/service_account.json
GOOGLE_CHAT_SPACE_ID=your_chat_space_id

# ServiceNow Credentials
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password
SERVICENOW_CLIENT_ID=your_oauth_client_id
SERVICENOW_CLIENT_SECRET=your_oauth_client_secret

# Application Settings
WEBHOOK_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=production
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_template)
    
    print("Generated .env.template - Copy to .env and fill in your credentials")

# Global variables for graceful shutdown
scheduler = None
server = None

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    logger.info("Received shutdown signal, stopping services...")
    if scheduler:
        scheduler.running = False  # Signal the scheduler to stop
    # The rest will be handled in the finally block of main()
    raise KeyboardInterrupt

async def main():
    """Main application entry point"""
    global scheduler, server
    
    # Generate environment template if it doesn't exist
    if not os.path.exists('.env.template'):
        generate_env_template()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize the automation system
    automation = SupportTicketAutomation()
    
    # Setup webhook handler
    webhook_handler = WebhookHandler(automation)
    
    # Setup scheduler
    scheduler = SchedulerService(automation)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start scheduler
        scheduler.start()
        
        # Start webhook server
        port = int(os.getenv('WEBHOOK_PORT', 8000))
        config = uvicorn.Config(
            webhook_handler.app, 
            host="0.0.0.0", 
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        logger.info(f"Starting webhook server on port {port}")
        logger.info("Support Ticket Automation System is now running!")
        logger.info("Webhook endpoints:")
        logger.info(f"  - Google Chat: http://localhost:{port}/webhook/google-chat")
        logger.info(f"  - ServiceNow: http://localhost:{port}/webhook/servicenow")
        logger.info(f"  - Health Check: http://localhost:{port}/health")
        
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Error in main application: {e}")
    finally:
        # Stop the scheduler first
        if scheduler:
            logger.info("Stopping scheduler...")
            scheduler.stop()
            scheduler = None
        
        logger.info("Shutdown complete")

def setup_cli():
    """Setup command-line interface"""
    
    parser = argparse.ArgumentParser(description="Support Ticket Automation System")
    
    parser.add_argument('--mode', choices=['server', 'test', 'setup'], 
                       default='server', help='Run mode')
    parser.add_argument('--port', type=int, default=8000, 
                       help='Webhook server port')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = setup_cli()
    
    # Configure logging
    logging.basicConfig(level=getattr(logging, args.log_level))
    
    if args.mode == 'setup':
        generate_env_template()
        print("Environment template generated. Please configure .env file.")
    else:
        # Set webhook port from command line
        os.environ['WEBHOOK_PORT'] = str(args.port)
        asyncio.run(main())