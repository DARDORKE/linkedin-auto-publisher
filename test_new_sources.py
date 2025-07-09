#!/usr/bin/env python3
"""
Test rapide des nouvelles sources AI
"""
import time
from src.fullstack_scraper import FullStackDevScraper
from loguru import logger

def test_ai_sources():
    """Test spécifiquement les nouvelles sources AI"""
    logger.info("=== TEST DES NOUVELLES SOURCES AI ===")
    
    scraper = FullStackDevScraper()
    
    # Test des nouvelles sources AI
    ai_sources = scraper.sources['ai']
    
    for source in ai_sources:
        logger.info(f"\n🔍 Testing: {source['name']}")
        logger.info(f"   URL: {source['url']}")
        
        try:
            start_time = time.time()
            articles = scraper._scrape_source(source)
            elapsed = time.time() - start_time
            
            if articles:
                logger.info(f"   ✅ SUCCESS - {len(articles)} articles in {elapsed:.2f}s")
                
                # Analyser le premier article
                first_article = articles[0]
                logger.info(f"   📄 Sample: {first_article.get('title', 'N/A')[:50]}...")
                logger.info(f"   📏 Content: {len(first_article.get('content', ''))} chars")
                logger.info(f"   📝 Summary: {len(first_article.get('summary', ''))} chars")
                logger.info(f"   🔄 Needs extraction: {first_article.get('needs_extraction', False)}")
            else:
                logger.warning(f"   ❌ NO ARTICLES")
                
        except Exception as e:
            logger.error(f"   ❌ ERROR: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    test_ai_sources()