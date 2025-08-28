"""
Server Runner for Support Ticket Automation System
"""

import asyncio
import os
from main import main

if __name__ == "__main__":
    # Set default port
    os.environ.setdefault('WEBHOOK_PORT', '8000')
    
    # Run the main application
    asyncio.run(main())
