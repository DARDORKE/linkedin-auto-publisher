#!/usr/bin/env python3
"""
Test rapide du scraper optimisé
"""
import time
from datetime import datetime
from src.fullstack_scraper import FullStackDevScraper
from src.database import DatabaseManager
from loguru import logger

def quick_test():
    """Test rapide de performance"""
    logger.info("Quick test of optimized scraper...")
    
    # Initialiser
    db = DatabaseManager()
    scraper = FullStackDevScraper(db)
    
    # Test 1: Un domaine spécifique
    logger.info("\n=== Test Frontend Domain ===")
    start = time.time()
    
    frontend_articles = scraper.scrape_domain_sources('frontend', max_articles=5, use_cache=False)
    
    elapsed = time.time() - start
    logger.info(f"Time: {elapsed:.2f}s")
    logger.info(f"Articles: {len(frontend_articles)}")
    
    if frontend_articles:
        article = frontend_articles[0]
        logger.info(f"\nTop article:")
        logger.info(f"  Title: {article['title'][:80]}...")
        logger.info(f"  Source: {article['source']}")
        logger.info(f"  Score: {article['relevance_score']}")
        logger.info(f"  Domain: {article['domain']}")
        logger.info(f"  Content length: {len(article['content']['full_text'])}")
        logger.info(f"  Technologies: {article['metadata']['technologies'][:5]}")
    
    # Test 2: Scraping global rapide
    logger.info(f"\n=== Test Global Scraping ===")
    start = time.time()
    
    all_articles = scraper.scrape_all_sources(max_articles=10, use_cache=False)
    
    elapsed = time.time() - start
    logger.info(f"Time: {elapsed:.2f}s")
    logger.info(f"Articles: {len(all_articles)}")
    
    # Statistiques
    domains = {}
    for article in all_articles:
        domain = article.get('domain', 'unknown')
        domains[domain] = domains.get(domain, 0) + 1
    
    logger.info(f"Domain distribution: {domains}")
    
    # Afficher les top 3
    logger.info(f"\nTop 3 articles:")
    for i, article in enumerate(all_articles[:3]):
        logger.info(f"{i+1}. {article['title'][:60]}... (Score: {article['relevance_score']})")

if __name__ == "__main__":
    quick_test()