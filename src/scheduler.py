import schedule
import time
from datetime import datetime
from loguru import logger
import os
from src.webdev_scraper import WebDevNewsScraper
from src.webdev_generator import WebDevPostGenerator
from src.database import DatabaseManager
from src.web_interface import run_web_interface
import threading

class PostScheduler:
    def __init__(self):
        self.scraper = WebDevNewsScraper()
        self.generator = WebDevPostGenerator()
        self.db = DatabaseManager()
        self.interval_hours = int(os.getenv('SCRAPING_INTERVAL_HOURS', 6))
        self.max_articles = int(os.getenv('MAX_ARTICLES_PER_SCRAPE', 30))
        self.running = False
        
    def generate_posts(self):
        logger.info("Starting post generation process")
        
        try:
            # Scrape articles
            articles = self.scraper.scrape_all_sources(self.max_articles)
            logger.info(f"Scraped {len(articles)} articles")
            
            if not articles:
                logger.warning("No articles found during scraping")
                return
            
            # Generate webdev synthesis
            variations = self.generator.generate_article_variations(articles, count=1)
            logger.info(f"Generated {len(variations)} webdev article(s)")
            
            # Save to database
            for post in variations:
                post_id = self.db.save_post(post)
                logger.info(f"Saved post {post_id} to database")
                
        except Exception as e:
            logger.error(f"Error in post generation: {e}")
    
    def start_web_interface(self):
        logger.info("Starting web interface")
        # Run Flask in a separate thread without debug mode in production
        web_thread = threading.Thread(target=lambda: run_web_interface(), daemon=True)
        web_thread.start()
    
    def start(self):
        self.running = True
        
        # Start web interface
        self.start_web_interface()
        
        # Initial generation
        self.generate_posts()
        
        # Schedule periodic generation
        schedule.every(self.interval_hours).hours.do(self.generate_posts)
        
        logger.info(f"Scheduler started - generating posts every {self.interval_hours} hours")
        logger.info(f"Web interface available at http://localhost:{os.getenv('FLASK_PORT', 5000)}")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        self.running = False
        logger.info("Scheduler stopped")