#!/usr/bin/env python3
"""
Test du scraper amélioré avec les nouvelles sources
"""
import time
from src.fullstack_scraper import FullStackDevScraper
from src.database import DatabaseManager
from loguru import logger

def test_improved_scraper():
    """Test du scraper amélioré"""
    logger.info("=== TEST DU SCRAPER AMÉLIORÉ ===")
    
    scraper = FullStackDevScraper()
    
    # Test rapide de chaque domaine
    domains = ['ai', 'backend', 'frontend']
    
    for domain in domains:
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 TESTING DOMAIN: {domain.upper()}")
        logger.info(f"{'='*60}")
        
        start_time = time.time()
        articles = scraper.scrape_domain_sources(domain, max_articles=10, use_cache=False)
        elapsed = time.time() - start_time
        
        logger.info(f"📊 RESULTS for {domain}:")
        logger.info(f"   Articles found: {len(articles)}")
        logger.info(f"   Time taken: {elapsed:.2f}s")
        
        if articles:
            # Analyser les scores de qualité
            scores = [a.get('relevance_score', 0) for a in articles]
            avg_score = sum(scores) / len(scores)
            
            logger.info(f"   Average relevance score: {avg_score:.1f}")
            logger.info(f"   Score range: {min(scores):.1f} - {max(scores):.1f}")
            
            # Analyser les extractions
            with_extraction = [a for a in articles if a.get('content', {}).get('extraction_quality') == 'full']
            needs_extraction = [a for a in articles if a.get('needs_extraction', False)]
            
            logger.info(f"   Articles with full extraction: {len(with_extraction)}")
            logger.info(f"   Articles needing extraction: {len(needs_extraction)}")
            
            # Échantillon des meilleurs articles
            logger.info(f"\n   📄 TOP 3 ARTICLES:")
            for i, article in enumerate(articles[:3]):
                logger.info(f"   {i+1}. {article['title'][:50]}...")
                logger.info(f"      Source: {article['source']}")
                logger.info(f"      Score: {article.get('relevance_score', 0):.1f}")
                logger.info(f"      Content quality: {article.get('content', {}).get('extraction_quality', 'unknown')}")
                logger.info(f"      Technologies: {article.get('metadata', {}).get('technologies', [])[:3]}")
                logger.info("")
        else:
            logger.warning(f"   ❌ No articles found for {domain}")
    
    # Test complet avec tous les domaines
    logger.info(f"\n{'='*60}")
    logger.info("🚀 TESTING COMPLETE SCRAPING")
    logger.info(f"{'='*60}")
    
    start_time = time.time()
    all_articles = scraper.scrape_all_sources(max_articles=30, use_cache=False)
    elapsed = time.time() - start_time
    
    logger.info(f"📊 COMPLETE RESULTS:")
    logger.info(f"   Total articles: {len(all_articles)}")
    logger.info(f"   Total time: {elapsed:.2f}s")
    
    if all_articles:
        # Analyser par domaine
        by_domain = scraper.get_articles_by_domain(all_articles)
        for domain, articles in by_domain.items():
            logger.info(f"   {domain}: {len(articles)} articles")
        
        # Analyser les technologies tendances
        trending_tech = scraper.get_trending_technologies(all_articles)
        logger.info(f"\n   🔥 TRENDING TECHNOLOGIES:")
        for domain, techs in trending_tech.items():
            if techs:
                logger.info(f"   {domain}: {', '.join(techs[:3])}")
    
    logger.info(f"\n✅ SCRAPER AMÉLIORATION TERMINÉE")

if __name__ == "__main__":
    test_improved_scraper()