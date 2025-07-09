#!/usr/bin/env python3
"""
Script de test pour vérifier que l'application fonctionne correctement
"""

import os
os.environ['GEMINI_API_KEY'] = 'test_key_for_development'
os.environ['LINKEDIN_EMAIL'] = 'test@example.com'
os.environ['LINKEDIN_PASSWORD'] = 'test_password'

from loguru import logger
from src.scraper import TechNewsScraper
from src.database import DatabaseManager
from src.web_interface import app

def test_scraper():
    logger.info("Testing scraper...")
    scraper = TechNewsScraper()
    # Test avec un seul article pour éviter de spammer
    articles = scraper.scrape_all_sources(max_articles=3)
    logger.info(f"Found {len(articles)} articles")
    for article in articles:
        logger.info(f"- {article['title']} ({article['source']})")
    return articles

def test_database():
    logger.info("Testing database...")
    db = DatabaseManager()
    
    # Test post creation
    test_post = {
        'content': 'Test post content for LinkedIn',
        'style': 'test',
        'hashtags': ['#test', '#linkedin'],
        'source_articles': []
    }
    
    post_id = db.save_post(test_post)
    logger.info(f"Created test post with ID: {post_id}")
    
    # Test retrieval
    pending_posts = db.get_pending_posts()
    logger.info(f"Found {len(pending_posts)} pending posts")
    
    return post_id

def test_web_interface():
    logger.info("Testing web interface...")
    logger.info("Starting Flask server on http://localhost:5000")
    logger.info("Press Ctrl+C to stop")
    app.run(debug=True, port=5000)

if __name__ == "__main__":
    logger.info("Starting application tests...")
    
    # Test components
    articles = test_scraper()
    post_id = test_database()
    
    # Start web interface
    test_web_interface()