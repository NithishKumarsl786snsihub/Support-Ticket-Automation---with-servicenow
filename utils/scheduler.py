"""
Scheduler Service
Background scheduler for periodic workflow execution
"""

import logging
import threading
import time
import asyncio
import schedule

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulerService:
    """Background scheduler for periodic workflow execution"""
    
    def __init__(self, automation_system):
        self.automation = automation_system
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the scheduler service"""
        if self.running:
            return
        
        # Schedule periodic checks
        schedule.every(1).minutes.do(self._run_scheduled_workflow)
        schedule.every().hour.do(self._cleanup_old_data)
        schedule.every().day.at("09:00").do(self._daily_summary)
        
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop)
        self.thread.daemon = True  # Set as daemon so it doesn't block program exit
        self.thread.start()
        
        logger.info("Scheduler service started")
    
    def stop(self):
        """Stop the scheduler service"""
        if not self.running:
            return
            
        logger.info("Stopping scheduler service...")
        self.running = False
        
        # Don't wait for thread to join if we're handling a KeyboardInterrupt
        # This prevents the server from hanging on shutdown
        try:
            if self.thread and self.thread.is_alive():
                # Set a short timeout to avoid blocking shutdown
                self.thread.join(timeout=1.0)
                if self.thread.is_alive():
                    logger.warning("Scheduler thread did not terminate gracefully")
        except Exception as e:
            logger.warning(f"Error while stopping scheduler: {e}")
            
        logger.info("Scheduler service stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                # Use a shorter sleep time to respond to stop requests faster
                for _ in range(6):  # 6 * 10 seconds = 1 minute
                    if not self.running:
                        break
                    time.sleep(10)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                # Brief pause before continuing
                time.sleep(5)
    
    def _run_scheduled_workflow(self):
        """Run workflow on schedule"""
        try:
            logger.info("Running scheduled workflow check")
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.automation.run_workflow())
            loop.close()
        except Exception as e:
            logger.error(f"Scheduled workflow failed: {e}")
    
    def _cleanup_old_data(self):
        """Cleanup old data and logs"""
        logger.info("Running data cleanup")
        # Implement cleanup logic
    
    def _daily_summary(self):
        """Generate daily summary report"""
        logger.info("Generating daily summary")
        # Implement summary report logic