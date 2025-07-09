import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from loguru import logger
import time
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin, urlparse
import feedparser

class WebDevNewsScraper:
    def __init__(self):
        self.sources = [
            # Sources développement web françaises
            {
                "name": "Journal du Hacker",
                "type": "rss",
                "url": "https://www.journalduhacker.net/rss",
                "category": "webdev_fr",
                "reliability": 8,
                "topics": ["javascript", "react", "vue", "angular", "node", "css", "html", "frontend", "backend"]
            },
            {
                "name": "Grafikart",
                "type": "rss",
                "url": "https://grafikart.fr/tutoriels.rss",
                "category": "webdev_fr",
                "reliability": 9,
                "topics": ["javascript", "php", "css", "html", "symfony", "react", "vue"]
            },
            
            # Sources développement web internationales
            {
                "name": "CSS-Tricks",
                "type": "rss",
                "url": "https://css-tricks.com/feed/",
                "category": "frontend",
                "reliability": 9,
                "topics": ["css", "html", "javascript", "frontend", "responsive", "animations"]
            },
            {
                "name": "A List Apart",
                "type": "rss",
                "url": "https://alistapart.com/main/feed/",
                "category": "frontend",
                "reliability": 10,
                "topics": ["design", "frontend", "ux", "accessibility", "web standards"]
            },
            {
                "name": "Smashing Magazine",
                "type": "rss",
                "url": "https://www.smashingmagazine.com/feed/",
                "category": "frontend",
                "reliability": 9,
                "topics": ["design", "frontend", "javascript", "css", "ux", "performance"]
            },
            
            # Sources JavaScript/Framework
            {
                "name": "JavaScript Weekly",
                "type": "rss",
                "url": "https://javascriptweekly.com/rss/",
                "category": "javascript",
                "reliability": 9,
                "topics": ["javascript", "es6", "typescript", "node", "frameworks"]
            },
            {
                "name": "React Blog",
                "type": "rss",
                "url": "https://react.dev/rss.xml",
                "category": "frameworks",
                "reliability": 10,
                "topics": ["react", "jsx", "hooks", "nextjs"]
            },
            {
                "name": "Vue.js News",
                "type": "rss",
                "url": "https://news.vuejs.org/rss.xml",
                "category": "frameworks",
                "reliability": 10,
                "topics": ["vue", "nuxt", "composition api"]
            },
            
            # Sources backend/fullstack
            {
                "name": "Node.js Blog",
                "type": "rss",
                "url": "https://nodejs.org/en/feed/blog.xml",
                "category": "backend",
                "reliability": 10,
                "topics": ["nodejs", "express", "npm", "backend"]
            },
            {
                "name": "Web.dev",
                "type": "rss",
                "url": "https://web.dev/feed.xml",
                "category": "webdev",
                "reliability": 10,
                "topics": ["performance", "pwa", "web standards", "accessibility", "seo"]
            },
            
            # Sources communautaires spécialisées
            {
                "name": "Dev.to - JavaScript",
                "type": "rss",
                "url": "https://dev.to/feed/tag/javascript",
                "category": "community",
                "reliability": 7,
                "topics": ["javascript", "tutorials", "tips"]
            },
            {
                "name": "Dev.to - Frontend",
                "type": "rss",
                "url": "https://dev.to/feed/tag/frontend",
                "category": "community",
                "reliability": 7,
                "topics": ["frontend", "css", "html", "javascript"]
            },
            {
                "name": "Dev.to - React",
                "type": "rss",
                "url": "https://dev.to/feed/tag/react",
                "category": "community",
                "reliability": 7,
                "topics": ["react", "components", "hooks"]
            },
            
            # Sources d'actualités tech orientées web
            {
                "name": "The Verge - Web",
                "type": "rss",
                "url": "https://www.theverge.com/web/rss/index.xml",
                "category": "news",
                "reliability": 8,
                "topics": ["web platforms", "browsers", "standards"]
            },
            {
                "name": "Mozilla Hacks",
                "type": "rss",
                "url": "https://hacks.mozilla.org/feed/",
                "category": "webdev",
                "reliability": 9,
                "topics": ["firefox", "web standards", "javascript", "css", "webassembly"]
            }
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Mots-clés spécifiques au développement web
        self.webdev_keywords = {
            'high_priority': [
                'javascript', 'typescript', 'react', 'vue', 'angular', 'nodejs', 'npm',
                'css', 'html', 'frontend', 'backend', 'fullstack', 'responsive', 'pwa',
                'performance', 'accessibility', 'seo', 'webpack', 'vite', 'nextjs', 'nuxtjs'
            ],
            'medium_priority': [
                'framework', 'library', 'api', 'rest', 'graphql', 'database', 'mongodb',
                'express', 'fastify', 'svelte', 'solid', 'remix', 'astro', 'tailwind',
                'sass', 'scss', 'typescript', 'testing', 'jest', 'cypress'
            ],
            'tools_and_tech': [
                'git', 'github', 'gitlab', 'docker', 'deployment', 'hosting', 'vercel',
                'netlify', 'aws', 'firebase', 'supabase', 'prisma', 'trpc'
            ]
        }
        
    def scrape_all_sources(self, max_articles: int = 30) -> List[Dict]:
        all_articles = []
        
        for source in self.sources:
            try:
                articles = self._scrape_rss(source)
                # Filtrer par mots-clés pertinents
                webdev_articles = self._filter_webdev_articles(articles)
                all_articles.extend(webdev_articles)
                logger.info(f"Scraped {len(webdev_articles)} webdev articles from {source['name']}")
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping {source['name']}: {e}")
        
        # Dédupliquer et scorer
        unique_articles = self._deduplicate_articles(all_articles)
        scored_articles = self._score_webdev_articles(unique_articles)
        
        return sorted(scored_articles, key=lambda x: x['relevance_score'], reverse=True)[:max_articles]
    
    def _scrape_rss(self, source: Dict) -> List[Dict]:
        articles = []
        feed = feedparser.parse(source['url'])
        
        for entry in feed.entries[:15]:  # Limiter par source
            try:
                article = {
                    'title': entry.title,
                    'url': entry.link,
                    'source': source['name'],
                    'category': source['category'],
                    'reliability': source['reliability'],
                    'source_topics': source['topics'],
                    'published': self._parse_date(entry.get('published', '')),
                    'summary': BeautifulSoup(entry.get('summary', ''), 'html.parser').get_text()[:400],
                    'scraped_at': datetime.now()
                }
                articles.append(article)
            except Exception as e:
                logger.debug(f"Error parsing RSS entry: {e}")
                
        return articles
    
    def _parse_date(self, date_str: str) -> datetime:
        try:
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            if parsed_date.tzinfo is not None:
                parsed_date = parsed_date.replace(tzinfo=None)
            return parsed_date
        except:
            return datetime.now()
    
    def _filter_webdev_articles(self, articles: List[Dict]) -> List[Dict]:
        """Filtre les articles pertinents pour le développement web"""
        webdev_articles = []
        
        for article in articles:
            text_content = (article['title'] + ' ' + article.get('summary', '')).lower()
            
            # Vérifier si l'article contient des mots-clés webdev
            has_webdev_keywords = any(
                keyword in text_content 
                for keyword_list in self.webdev_keywords.values() 
                for keyword in keyword_list
            )
            
            # Ou si la source est spécialisée webdev
            is_webdev_source = any(
                topic in text_content 
                for topic in article.get('source_topics', [])
            )
            
            if has_webdev_keywords or is_webdev_source:
                webdev_articles.append(article)
                
        return webdev_articles
    
    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            normalized_title = re.sub(r'[^\w\s]', '', article['title'].lower())
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_articles.append(article)
                
        return unique_articles
    
    def _score_webdev_articles(self, articles: List[Dict]) -> List[Dict]:
        """Score spécialisé pour les articles de développement web"""
        for article in articles:
            score = 0
            
            # Score de base par fiabilité
            score += article['reliability'] * 8
            
            # Score par fraîcheur
            age_hours = (datetime.now() - article.get('published', datetime.now())).total_seconds() / 3600
            if age_hours < 12:
                score += 25
            elif age_hours < 48:
                score += 15
            elif age_hours < 168:  # 1 semaine
                score += 8
            
            # Score par mots-clés webdev
            text_content = (article['title'] + ' ' + article.get('summary', '')).lower()
            
            for keyword in self.webdev_keywords['high_priority']:
                if keyword in text_content:
                    score += 20
                    
            for keyword in self.webdev_keywords['medium_priority']:
                if keyword in text_content:
                    score += 12
                    
            for keyword in self.webdev_keywords['tools_and_tech']:
                if keyword in text_content:
                    score += 8
            
            # Bonus pour catégories prioritaires
            priority_categories = ['webdev', 'frontend', 'javascript', 'frameworks']
            if article['category'] in priority_categories:
                score += 15
            
            # Bonus pour sources officielles
            official_sources = ['React Blog', 'Vue.js News', 'Node.js Blog', 'Web.dev', 'Mozilla Hacks']
            if article['source'] in official_sources:
                score += 20
            
            article['relevance_score'] = max(0, score)
            
        return articles
    
    def get_articles_by_category(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        categorized = {}
        for article in articles:
            category = article['category']
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(article)
        return categorized
    
    def get_trending_webdev_topics(self, articles: List[Dict]) -> List[str]:
        """Extraction des tendances spécifiques au développement web"""
        topic_frequency = {}
        
        for article in articles:
            text = (article['title'] + ' ' + article.get('summary', '')).lower()
            
            # Compter les occurrences des technologies webdev
            for keyword_list in self.webdev_keywords.values():
                for keyword in keyword_list:
                    if keyword in text:
                        topic_frequency[keyword] = topic_frequency.get(keyword, 0) + article.get('relevance_score', 0)
        
        # Retourner les 10 sujets les plus tendance
        trending = sorted(topic_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        return [topic for topic, _ in trending]