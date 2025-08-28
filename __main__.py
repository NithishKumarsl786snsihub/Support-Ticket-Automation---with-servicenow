"""
Entry point for Support Ticket Automation System
"""

import sys
import os
import argparse
import logging
import asyncio

from main import main, generate_env_template
from tests.test_utils import run_test_workflow

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
    elif args.mode == 'test':
        asyncio.run(run_test_workflow())
    else:
        # Set webhook port from command line
        os.environ['WEBHOOK_PORT'] = str(args.port)
        asyncio.run(main())
