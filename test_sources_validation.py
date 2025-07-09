#!/usr/bin/env python3
"""
Validation complète des sources du scraper
Vérifie chaque source individuellement
"""
import time
from datetime import datetime
from src.fullstack_scraper import FullStackDevScraper
from src.database import DatabaseManager
from loguru import logger

def validate_all_sources():
    """Valide toutes les sources du scraper"""
    logger.info("=== VALIDATION COMPLÈTE DES SOURCES ===")
    
    scraper = FullStackDevScraper()
    
    # Stats globales
    total_sources = 0
    working_sources = 0
    broken_sources = []
    empty_sources = []
    quality_sources = []
    
    # Test chaque domaine
    for domain, sources in scraper.sources.items():
        logger.info(f"\n{'='*50}")
        logger.info(f"🔍 TESTING DOMAIN: {domain.upper()}")
        logger.info(f"{'='*50}")
        
        domain_working = 0
        domain_broken = 0
        
        for source in sources:
            total_sources += 1
            source_name = source['name']
            source_url = source['url']
            source_weight = source['weight']
            
            logger.info(f"\n📡 Testing: {source_name}")
            logger.info(f"   URL: {source_url}")
            logger.info(f"   Weight: {source_weight}")
            
            try:
                # Test de la source
                start_time = time.time()
                articles = scraper._scrape_source(source)
                elapsed = time.time() - start_time
                
                if not articles:
                    logger.warning(f"   ❌ NO ARTICLES - Source returned empty")
                    empty_sources.append({
                        'domain': domain,
                        'name': source_name,
                        'url': source_url,
                        'error': 'No articles returned'
                    })
                    domain_broken += 1
                else:
                    working_sources += 1
                    domain_working += 1
                    
                    # Analyser la qualité
                    logger.info(f"   ✅ SUCCESS - {len(articles)} articles in {elapsed:.2f}s")
                    
                    # Analyser le premier article
                    first_article = articles[0]
                    title_len = len(first_article.get('title', ''))
                    summary_len = len(first_article.get('summary', ''))
                    content_len = len(first_article.get('content', ''))
                    
                    logger.info(f"   📄 Sample article:")
                    logger.info(f"      Title: {first_article.get('title', 'N/A')[:60]}...")
                    logger.info(f"      Title length: {title_len} chars")
                    logger.info(f"      Summary length: {summary_len} chars")
                    logger.info(f"      Content length: {content_len} chars")
                    logger.info(f"      Published: {first_article.get('published', 'N/A')}")
                    logger.info(f"      Tags: {first_article.get('tags', [])}")
                    
                    # Critères de qualité
                    quality_score = 0
                    issues = []
                    
                    if title_len > 20:
                        quality_score += 20
                    else:
                        issues.append("Title too short")
                    
                    if summary_len > 100:
                        quality_score += 20
                    else:
                        issues.append("Summary too short")
                    
                    if content_len > 500:
                        quality_score += 20
                    else:
                        issues.append("Content too short")
                    
                    if first_article.get('published'):
                        quality_score += 20
                    else:
                        issues.append("No publication date")
                    
                    if len(articles) >= 5:
                        quality_score += 20
                    else:
                        issues.append("Too few articles")
                    
                    # Évaluation finale
                    if quality_score >= 80:
                        logger.info(f"   🌟 HIGH QUALITY - Score: {quality_score}/100")
                        quality_sources.append({
                            'domain': domain,
                            'name': source_name,
                            'weight': source_weight,
                            'articles_count': len(articles),
                            'quality_score': quality_score,
                            'response_time': elapsed
                        })
                    elif quality_score >= 60:
                        logger.info(f"   ⚠️  MEDIUM QUALITY - Score: {quality_score}/100")
                        if issues:
                            logger.info(f"      Issues: {', '.join(issues)}")
                    else:
                        logger.warning(f"   ⚠️  LOW QUALITY - Score: {quality_score}/100")
                        logger.warning(f"      Issues: {', '.join(issues)}")
                
            except Exception as e:
                logger.error(f"   ❌ ERROR - {str(e)}")
                broken_sources.append({
                    'domain': domain,
                    'name': source_name,
                    'url': source_url,
                    'error': str(e)
                })
                domain_broken += 1
            
            # Petite pause entre les tests
            time.sleep(0.5)
        
        # Résumé du domaine
        logger.info(f"\n📊 DOMAIN {domain.upper()} SUMMARY:")
        logger.info(f"   Working: {domain_working}/{len(sources)} sources")
        logger.info(f"   Broken: {domain_broken}/{len(sources)} sources")
    
    # Résumé global
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 GLOBAL SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total sources tested: {total_sources}")
    logger.info(f"Working sources: {working_sources}")
    logger.info(f"Broken sources: {len(broken_sources)}")
    logger.info(f"Empty sources: {len(empty_sources)}")
    logger.info(f"High quality sources: {len(quality_sources)}")
    logger.info(f"Success rate: {(working_sources/total_sources)*100:.1f}%")
    
    # Détail des sources cassées
    if broken_sources:
        logger.info(f"\n❌ BROKEN SOURCES:")
        for source in broken_sources:
            logger.info(f"   {source['domain']}: {source['name']} - {source['error']}")
    
    # Détail des sources vides
    if empty_sources:
        logger.info(f"\n⚠️  EMPTY SOURCES:")
        for source in empty_sources:
            logger.info(f"   {source['domain']}: {source['name']} - {source['error']}")
    
    # Top sources par qualité
    if quality_sources:
        logger.info(f"\n🌟 HIGH QUALITY SOURCES:")
        quality_sources.sort(key=lambda x: x['quality_score'], reverse=True)
        for source in quality_sources[:10]:  # Top 10
            logger.info(f"   {source['domain']}: {source['name']} - Score: {source['quality_score']}/100 ({source['articles_count']} articles)")
    
    # Recommandations
    logger.info(f"\n💡 RECOMMENDATIONS:")
    if len(broken_sources) > 0:
        logger.info(f"   - Fix or remove {len(broken_sources)} broken sources")
    if len(empty_sources) > 0:
        logger.info(f"   - Investigate {len(empty_sources)} empty sources")
    if len(quality_sources) < total_sources * 0.7:
        logger.info(f"   - Consider adding more high-quality sources")
    
    success_rate = (working_sources/total_sources)*100
    if success_rate >= 85:
        logger.info(f"   ✅ Overall source quality is EXCELLENT ({success_rate:.1f}%)")
    elif success_rate >= 70:
        logger.info(f"   ✅ Overall source quality is GOOD ({success_rate:.1f}%)")
    else:
        logger.info(f"   ⚠️  Overall source quality needs IMPROVEMENT ({success_rate:.1f}%)")

if __name__ == "__main__":
    validate_all_sources()