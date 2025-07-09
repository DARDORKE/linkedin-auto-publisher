from linkedin_api import Linkedin
import os
from loguru import logger
from datetime import datetime
import time

class LinkedInPublisher:
    def __init__(self):
        email = os.getenv('LINKEDIN_EMAIL')
        password = os.getenv('LINKEDIN_PASSWORD')
        
        if not email or not password:
            raise ValueError("LinkedIn credentials not found in environment variables")
        
        try:
            self.api = Linkedin(email, password)
            logger.info("Successfully connected to LinkedIn")
        except Exception as e:
            logger.error(f"Failed to connect to LinkedIn: {e}")
            raise
    
    def publish_post(self, content: str) -> bool:
        try:
            self.api.post(content)
            logger.info(f"Successfully published post at {datetime.now()}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish post: {e}")
            return False
    
    def publish_with_retry(self, content: str, max_retries: int = 3) -> bool:
        for attempt in range(max_retries):
            if self.publish_post(content):
                return True
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 30  # 30s, 60s, 90s
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        return False
    
    def validate_post_length(self, content: str) -> bool:
        max_length = 3000
        if len(content) > max_length:
            logger.warning(f"Post exceeds maximum length ({len(content)}/{max_length})")
            return False
        return True
    
    def format_post(self, content: str) -> str:
        formatted_content = content.strip()
        
        if not formatted_content.endswith(('.', '!', '?', '#')):
            formatted_content += '.'
        
        return formatted_content