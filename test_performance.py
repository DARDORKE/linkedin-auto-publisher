#!/usr/bin/env python3
"""
Script pour tester les performances du scraping
Compare avant/après les optimisations
"""

import time
from datetime import datetime
from src.enhanced_scraper import EnhancedFullstackScraper
from src.database import DatabaseManager
from loguru import logger

def measure_scraping_performance():
    """Mesure les performances du scraping"""
    logger.info("Starting performance test...")
    
    # Initialiser le scraper
    db = DatabaseManager()
    scraper = EnhancedFullstackScraper(db)
    
    # Mesurer le temps de scraping
    start_time = time.time()
    start_datetime = datetime.now()
    
    try:
        # Scraper 20 articles (comme d'habitude)
        articles = scraper.scrape_all_sources(max_articles=20)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Statistiques
        logger.info(f"\n{'='*50}")
        logger.info("PERFORMANCE REPORT")
        logger.info(f"{'='*50}")
        logger.info(f"Start time: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        logger.info(f"Articles collected: {len(articles)}")
        
        if articles:
            # Compter les articles depuis le cache
            cached_articles = sum(1 for a in articles if a.get('from_cache', False))
            enriched_articles = sum(1 for a in articles if a.get('extraction_quality') == 'full')
            
            logger.info(f"Articles from cache: {cached_articles}/{len(articles)} ({cached_articles/len(articles)*100:.1f}%)")
            logger.info(f"Articles enriched: {enriched_articles}/{len(articles)} ({enriched_articles/len(articles)*100:.1f}%)")
            
            # Temps moyen par article
            avg_time_per_article = duration / len(articles)
            logger.info(f"Average time per article: {avg_time_per_article:.2f} seconds")
        
        logger.info(f"{'='*50}\n")
        
        # Afficher les statistiques du cache
        cache_stats = db.get_cache_stats()
        logger.info("Cache Statistics:")
        logger.info(f"Total cached articles: {cache_stats['total_articles']}")
        logger.info(f"Fresh articles: {cache_stats['fresh_articles']}")
        logger.info(f"Expired articles: {cache_stats['expired_articles']}")
        
        return {
            'duration': duration,
            'articles_count': len(articles),
            'cached_articles': cached_articles if articles else 0,
            'enriched_articles': enriched_articles if articles else 0,
            'cache_stats': cache_stats
        }
        
    except Exception as e:
        logger.error(f"Error during performance test: {e}")
        return None

if __name__ == "__main__":
    # Configuration des logs pour le test
    logger.remove()
    logger.add("logs/performance_test_{time}.log", rotation="10 MB")
    logger.add(lambda msg: print(msg), colorize=True)
    
    # Lancer le test
    results = measure_scraping_performance()
    
    if results:
        logger.success("\nPerformance test completed successfully!")
        logger.info("\nOptimizations applied:")
        logger.info("✓ RSS collection workers: 5 → 15")
        logger.info("✓ Content enrichment workers: 3 → 10")
        logger.info("✓ Content caching implemented")
        logger.info("✓ Reduced articles for low-priority sources")
        logger.info("✓ Date filtering before enrichment (30 days)")
    else:
        logger.error("\nPerformance test failed!")