#!/usr/bin/env python3
"""
Test de sources potentielles pour remplacer les sources cassées
"""
import requests
import feedparser
import time
from loguru import logger

def test_source(name, url):
    """Test une source RSS"""
    logger.info(f"\n🔍 Testing: {name}")
    logger.info(f"   URL: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        elapsed = time.time() - start_time
        
        if not hasattr(feed, 'entries') or not feed.entries:
            logger.warning(f"   ❌ NO ENTRIES - Feed has no entries")
            return False
        
        articles_count = len(feed.entries)
        logger.info(f"   ✅ SUCCESS - {articles_count} articles in {elapsed:.2f}s")
        
        # Analyser le premier article
        first_entry = feed.entries[0]
        title = first_entry.get('title', '').strip()
        summary = first_entry.get('summary', '').strip()
        
        logger.info(f"   📄 Sample: {title[:60]}...")
        logger.info(f"   📝 Title length: {len(title)} chars")
        logger.info(f"   📝 Summary length: {len(summary)} chars")
        logger.info(f"   📅 Published: {first_entry.get('published', 'N/A')}")
        
        # Score de qualité
        quality_score = 0
        if len(title) > 20:
            quality_score += 25
        if len(summary) > 100:
            quality_score += 25
        if articles_count >= 5:
            quality_score += 25
        if first_entry.get('published'):
            quality_score += 25
        
        logger.info(f"   🌟 Quality score: {quality_score}/100")
        
        return quality_score >= 75
        
    except Exception as e:
        logger.error(f"   ❌ ERROR: {e}")
        return False

def test_potential_sources():
    """Test des sources potentielles"""
    logger.info("=== TEST DES SOURCES POTENTIELLES ===")
    
    # Sources potentielles pour remplacer OpenAI
    openai_alternatives = [
        ("OpenAI News", "https://openai.com/news/rss.xml"),
        ("OpenAI Blog Alt", "https://openai.com/blog/rss/"),
        ("OpenAI Research", "https://openai.com/research/rss.xml"),
        ("AI News", "https://artificialintelligence-news.com/feed/"),
        ("VentureBeat AI", "https://venturebeat.com/ai/feed/"),
        ("MIT Technology Review AI", "https://www.technologyreview.com/topic/artificial-intelligence/feed/"),
    ]
    
    # Sources potentielles pour améliorer AI
    ai_improvements = [
        ("Papers with Code", "https://paperswithcode.com/feed.xml"),
        ("Distill", "https://distill.pub/rss.xml"),
        ("AI Research", "https://ai-research.org/feed/"),
        ("The Gradient", "https://thegradient.pub/rss/"),
        ("Berkeley AI Research", "https://bair.berkeley.edu/blog/feed.xml"),
    ]
    
    # Sources potentielles pour améliorer Node.js
    nodejs_alternatives = [
        ("Node.js Medium", "https://medium.com/feed/the-node-js-collection"),
        ("Node.js Best Practices", "https://github.com/goldbergyoni/nodebestpractices/releases.atom"),
        ("Rising Stack", "https://blog.risingstack.com/rss/"),
        ("Node.js Weekly Archive", "https://nodeweekly.com/rss/"),
    ]
    
    logger.info("\n" + "="*60)
    logger.info("🔍 TESTING OPENAI ALTERNATIVES")
    logger.info("="*60)
    
    good_openai_alternatives = []
    for name, url in openai_alternatives:
        if test_source(name, url):
            good_openai_alternatives.append((name, url))
        time.sleep(1)
    
    logger.info("\n" + "="*60)
    logger.info("🔍 TESTING AI IMPROVEMENTS")
    logger.info("="*60)
    
    good_ai_improvements = []
    for name, url in ai_improvements:
        if test_source(name, url):
            good_ai_improvements.append((name, url))
        time.sleep(1)
    
    logger.info("\n" + "="*60)
    logger.info("🔍 TESTING NODE.JS ALTERNATIVES")
    logger.info("="*60)
    
    good_nodejs_alternatives = []
    for name, url in nodejs_alternatives:
        if test_source(name, url):
            good_nodejs_alternatives.append((name, url))
        time.sleep(1)
    
    # Résumé des recommandations
    logger.info("\n" + "="*60)
    logger.info("📊 RECOMMANDATIONS")
    logger.info("="*60)
    
    logger.info("\n🔄 Pour remplacer OpenAI Blog (cassé):")
    for name, url in good_openai_alternatives:
        logger.info(f"   ✅ {name}: {url}")
    
    logger.info("\n📈 Pour améliorer le domaine AI:")
    for name, url in good_ai_improvements:
        logger.info(f"   ✅ {name}: {url}")
    
    logger.info("\n🔧 Pour améliorer Node.js:")
    for name, url in good_nodejs_alternatives:
        logger.info(f"   ✅ {name}: {url}")

if __name__ == "__main__":
    test_potential_sources()