import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from loguru import logger
import time
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin, urlparse
import feedparser
import signal
from contextlib import contextmanager
from src.database import DatabaseManager
from readability import Document
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import hashlib

class FullStackDevScraper:
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
        self.cache_duration_hours = 6  # Durée de vie du cache en heures
        self.request_timeout = 15  # Timeout réduit pour les requêtes HTTP
        self.max_retries = 2  # Nombre maximum de tentatives
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Liste des flux RSS problématiques à ignorer temporairement
        self.problematic_feeds = {
            'https://grafikart.fr/tutoriels.rss',  # 404 Not Found
            'https://php.net/releases/feed.php',  # Souvent en timeout
            'https://www.python.org/blog/rss/',   # Très lent
        }
        self.sources = [
            # Sources développement françaises
            {
                "name": "Journal du Hacker",
                "type": "rss",
                "url": "https://www.journalduhacker.net/rss",
                "category": "dev_fr",
                "reliability": 8,
                "domains": ["frontend", "backend", "ai"]
            },
            {
                "name": "Grafikart",
                "type": "rss",
                "url": "https://grafikart.fr/tutoriels.rss",
                "category": "dev_fr",
                "reliability": 9,
                "domains": ["frontend", "backend"]
            },
            {
                "name": "Développez.com",
                "type": "rss",
                "url": "https://www.developpez.com/index/rss",
                "category": "dev_fr",
                "reliability": 8,
                "domains": ["frontend", "backend", "ai"]
            },
            
            # Sources frontend spécialisées
            {
                "name": "CSS-Tricks",
                "type": "rss",
                "url": "https://css-tricks.com/feed/",
                "category": "frontend",
                "reliability": 9,
                "domains": ["frontend"]
            },
            {
                "name": "A List Apart",
                "type": "rss",
                "url": "https://alistapart.com/main/feed/",
                "category": "frontend",
                "reliability": 10,
                "domains": ["frontend"]
            },
            {
                "name": "Smashing Magazine",
                "type": "rss",
                "url": "https://www.smashingmagazine.com/feed/",
                "category": "frontend",
                "reliability": 9,
                "domains": ["frontend"]
            },
            {
                "name": "React Blog",
                "type": "rss",
                "url": "https://react.dev/rss.xml",
                "category": "frontend",
                "reliability": 10,
                "domains": ["frontend"]
            },
            {
                "name": "Vue.js News",
                "type": "rss",
                "url": "https://news.vuejs.org/rss.xml",
                "category": "frontend",
                "reliability": 10,
                "domains": ["frontend"]
            },
            {
                "name": "Angular Blog",
                "type": "rss",
                "url": "https://blog.angular.io/feed",
                "category": "frontend",
                "reliability": 10,
                "domains": ["frontend"]
            },
            {
                "name": "Web.dev",
                "type": "rss",
                "url": "https://web.dev/feed.xml",
                "category": "frontend",
                "reliability": 10,
                "domains": ["frontend"]
            },
            {
                "name": "Mozilla Hacks",
                "type": "rss",
                "url": "https://hacks.mozilla.org/feed/",
                "category": "frontend",
                "reliability": 9,
                "domains": ["frontend"]
            },
            {
                "name": "Frontend Focus",
                "type": "rss",
                "url": "https://frontendfoc.us/rss",
                "category": "frontend",
                "reliability": 8,
                "domains": ["frontend"]
            },
            {
                "name": "Codrops",
                "type": "rss",
                "url": "https://tympanus.net/codrops/feed/",
                "category": "frontend",
                "reliability": 8,
                "domains": ["frontend"]
            },
            {
                "name": "CSS Weekly",
                "type": "rss",
                "url": "https://css-weekly.com/feed/",
                "category": "frontend",
                "reliability": 8,
                "domains": ["frontend"]
            },
            
            # Sources backend spécialisées
            {
                "name": "Node.js Blog",
                "type": "rss",
                "url": "https://nodejs.org/en/feed/blog.xml",
                "category": "backend",
                "reliability": 10,
                "domains": ["backend"]
            },
            {
                "name": "Django News",
                "type": "rss",
                "url": "https://django-news.com/issues.rss",
                "category": "backend",
                "reliability": 9,
                "domains": ["backend"]
            },
            {
                "name": "Spring Blog",
                "type": "rss",
                "url": "https://spring.io/blog.atom",
                "category": "backend",
                "reliability": 9,
                "domains": ["backend"]
            },
            {
                "name": "Go Dev Blog",
                "type": "rss",
                "url": "https://go.dev/blog/feed.atom",
                "category": "backend",
                "reliability": 10,
                "domains": ["backend"]
            },
            {
                "name": "Rust Blog",
                "type": "rss",
                "url": "https://blog.rust-lang.org/feed.xml",
                "category": "backend",
                "reliability": 10,
                "domains": ["backend"]
            },
            {
                "name": "PHP.net News",
                "type": "rss",
                "url": "https://www.php.net/feed.atom",
                "category": "backend",
                "reliability": 9,
                "domains": ["backend"]
            },
            {
                "name": "Ruby Weekly",
                "type": "rss",
                "url": "https://rubyweekly.com/rss/",
                "category": "backend",
                "reliability": 8,
                "domains": ["backend"]
            },
            {
                "name": "Real Python",
                "type": "rss",
                "url": "https://realpython.com/atom.xml",
                "category": "backend",
                "reliability": 9,
                "domains": ["backend"]
            },
            {
                "name": "Database Weekly",
                "type": "rss",
                "url": "https://dbweekly.com/rss/",
                "category": "backend",
                "reliability": 8,
                "domains": ["backend"]
            },
            {
                "name": "AWS News",
                "type": "rss",
                "url": "https://aws.amazon.com/about-aws/whats-new/recent/feed/",
                "category": "backend",
                "reliability": 9,
                "domains": ["backend"]
            },
            {
                "name": "Microsoft DevBlogs",
                "type": "rss",
                "url": "https://devblogs.microsoft.com/feed/",
                "category": "backend",
                "reliability": 9,
                "domains": ["backend"]
            },
            {
                "name": "Google Cloud Blog",
                "type": "rss",
                "url": "https://cloud.google.com/blog/rss",
                "category": "backend",
                "reliability": 9,
                "domains": ["backend"]
            },
            {
                "name": "Kubernetes Blog",
                "type": "rss",
                "url": "https://kubernetes.io/feed.xml",
                "category": "backend",
                "reliability": 9,
                "domains": ["backend"]
            },
            {
                "name": "Docker Blog",
                "type": "rss",
                "url": "https://www.docker.com/blog/feed/",
                "category": "backend",
                "reliability": 9,
                "domains": ["backend"]
            },
            
            # Sources IA et ML
            {
                "name": "OpenAI Blog",
                "type": "rss",
                "url": "https://openai.com/news/rss.xml",
                "category": "ai",
                "reliability": 10,
                "domains": ["ai"]
            },
            {
                "name": "Google AI Blog",
                "type": "rss",
                "url": "https://research.google/blog/rss/",
                "category": "ai",
                "reliability": 10,
                "domains": ["ai"]
            },
            {
                "name": "Anthropic News",
                "type": "rss",
                "url": "https://rsshub.app/anthropic/news",
                "category": "ai",
                "reliability": 10,
                "domains": ["ai"]
            },
            {
                "name": "Towards Data Science",
                "type": "rss",
                "url": "https://towardsdatascience.com/feed",
                "category": "ai",
                "reliability": 8,
                "domains": ["ai"]
            },
            {
                "name": "Machine Learning Mastery",
                "type": "rss",
                "url": "https://machinelearningmastery.com/feed/",
                "category": "ai",
                "reliability": 8,
                "domains": ["ai"]
            },
            {
                "name": "arXiv ML Updates",
                "type": "rss",
                "url": "https://rss.arxiv.org/rss/cs.LG",
                "category": "ai",
                "reliability": 9,
                "domains": ["ai"]
            },
            {
                "name": "Hugging Face Blog",
                "type": "rss",
                "url": "https://huggingface.co/blog/feed.xml",
                "category": "ai",
                "reliability": 10,
                "domains": ["ai"]
            },
            {
                "name": "DeepMind Blog",
                "type": "rss",
                "url": "https://deepmind.com/blog/rss.xml",
                "category": "ai",
                "reliability": 10,
                "domains": ["ai"]
            },
            {
                "name": "Meta AI Blog",
                "type": "rss",
                "url": "https://research.facebook.com/feed/",
                "category": "ai",
                "reliability": 9,
                "domains": ["ai"]
            },
            {
                "name": "MIT CSAIL News",
                "type": "rss",
                "url": "https://news.mit.edu/rss/research",
                "category": "ai",
                "reliability": 10,
                "domains": ["ai"]
            },
            {
                "name": "Stanford AI Lab",
                "type": "rss",
                "url": "https://ai.stanford.edu/blog/feed.xml",
                "category": "ai",
                "reliability": 10,
                "domains": ["ai"]
            },
            {
                "name": "AI Research Blog",
                "type": "rss",
                "url": "https://research.google/blog/rss/",
                "category": "ai",
                "reliability": 9,
                "domains": ["ai"]
            },
            {
                "name": "Weights & Biases Blog",
                "type": "rss",
                "url": "https://wandb.ai/blog/rss.xml",
                "category": "ai",
                "reliability": 8,
                "domains": ["ai"]
            },
            {
                "name": "Gradient Flow",
                "type": "rss",
                "url": "https://gradientflow.com/feed/",
                "category": "ai",
                "reliability": 8,
                "domains": ["ai"]
            },
            {
                "name": "AI/ML Weekly",
                "type": "rss",
                "url": "https://aimlweekly.com/feed/",
                "category": "ai",
                "reliability": 8,
                "domains": ["ai"]
            },
            {
                "name": "The Batch (DeepLearning.AI)",
                "type": "rss",
                "url": "https://www.deeplearning.ai/the-batch/rss/",
                "category": "ai",
                "reliability": 9,
                "domains": ["ai"]
            },
            
            # Sources polyvalentes tech
            {
                "name": "GitHub Blog",
                "type": "rss",
                "url": "https://github.blog/feed/",
                "category": "devtools",
                "reliability": 9,
                "domains": ["frontend", "backend", "ai"]
            },
            {
                "name": "Stack Overflow Blog",
                "type": "rss",
                "url": "https://stackoverflow.blog/feed/",
                "category": "devtools",
                "reliability": 8,
                "domains": ["frontend", "backend", "ai"]
            },
            {
                "name": "InfoQ",
                "type": "rss",
                "url": "https://www.infoq.com/feed/",
                "category": "enterprise",
                "reliability": 9,
                "domains": ["frontend", "backend", "ai"]
            },
            {
                "name": "The New Stack",
                "type": "rss",
                "url": "https://thenewstack.io/feed/",
                "category": "devops",
                "reliability": 8,
                "domains": ["backend", "ai"]
            },
            {
                "name": "TechCrunch",
                "type": "rss",
                "url": "https://techcrunch.com/category/startups/feed/",
                "category": "general",
                "reliability": 8,
                "domains": ["frontend", "backend", "ai"]
            },
            {
                "name": "Ars Technica",
                "type": "rss",
                "url": "https://feeds.arstechnica.com/arstechnica/index",
                "category": "general",
                "reliability": 9,
                "domains": ["frontend", "backend", "ai"]
            },
            {
                "name": "TechCrunch",
                "type": "rss",
                "url": "https://techcrunch.com/feed/",
                "category": "general",
                "reliability": 8,
                "domains": ["frontend", "backend", "ai"]
            },
            {
                "name": "MIT Technology Review",
                "type": "rss",
                "url": "https://www.technologyreview.com/feed/",
                "category": "general",
                "reliability": 10,
                "domains": ["frontend", "backend", "ai"]
            },
            {
                "name": "IEEE Spectrum",
                "type": "rss",
                "url": "https://spectrum.ieee.org/rss",
                "category": "general",
                "reliability": 9,
                "domains": ["frontend", "backend", "ai"]
            },
            {
                "name": "VentureBeat",
                "type": "rss",
                "url": "https://venturebeat.com/feed/",
                "category": "general",
                "reliability": 7,
                "domains": ["frontend", "backend", "ai"]
            },
            
            # Sources communautaires
            {
                "name": "Dev.to - JavaScript",
                "type": "rss",
                "url": "https://dev.to/feed/tag/javascript",
                "category": "community",
                "reliability": 7,
                "domains": ["frontend", "backend"]
            },
            {
                "name": "Dev.to - Python",
                "type": "rss",
                "url": "https://dev.to/feed/tag/python",
                "category": "community",
                "reliability": 7,
                "domains": ["backend", "ai"]
            },
            {
                "name": "Dev.to - Machine Learning",
                "type": "rss",
                "url": "https://dev.to/feed/tag/machinelearning",
                "category": "community",
                "reliability": 7,
                "domains": ["ai"]
            },
            {
                "name": "Hacker News",
                "type": "web",
                "url": "https://news.ycombinator.com/",
                "selector": ".athing",
                "title_selector": ".titleline > a",
                "score_selector": ".score",
                "category": "community",
                "reliability": 8,
                "domains": ["frontend", "backend", "ai"]
            }
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Technologies par domaine
        self.tech_keywords = {
            'frontend': {
                'high': ['javascript', 'typescript', 'react', 'vue', 'angular', 'svelte', 'css', 'html', 'nextjs', 'nuxtjs', 'remix'],
                'medium': ['webpack', 'vite', 'tailwind', 'sass', 'responsive', 'pwa', 'webcomponents', 'solid', 'astro'],
                'tools': ['npm', 'yarn', 'pnpm', 'eslint', 'prettier', 'jest', 'cypress', 'playwright']
            },
            'backend': {
                'high': ['nodejs', 'python', 'java', 'go', 'rust', 'php', 'csharp', 'dotnet', 'django', 'fastapi', 'express', 'spring'],
                'medium': ['api', 'rest', 'graphql', 'grpc', 'microservices', 'serverless', 'lambda', 'kubernetes', 'docker'],
                'tools': ['mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'kafka', 'rabbitmq', 'nginx']
            },
            'ai': {
                'high': ['ai', 'ml', 'machinelearning', 'deeplearning', 'llm', 'gpt', 'transformers', 'pytorch', 'tensorflow'],
                'medium': ['nlp', 'computervision', 'reinforcement', 'chatbot', 'embedding', 'vectordb', 'langchain', 'openai'],
                'tools': ['jupyter', 'pandas', 'numpy', 'scikit-learn', 'huggingface', 'anthropic', 'claude', 'gemini']
            }
        }
        
    def scrape_all_sources(self, max_articles: int = 40, use_cache: bool = True) -> List[Dict]:
        """Scrape toutes les sources avec données enrichies pour le générateur"""
        # Nettoyer le cache expiré
        self.db.clear_expired_cache()
        
        all_articles = []
        sources_to_scrape = []
        
        if use_cache:
            # Récupérer tous les articles en cache
            cached_articles = self.db.get_cached_articles()
            logger.info(f"Found {len(cached_articles)} cached articles")
            all_articles.extend(cached_articles)
            
            # Identifier les sources qui ont des articles en cache
            cached_sources = set(article['source'] for article in cached_articles)
            
            # Déterminer quelles sources doivent être scrapées
            for source in self.sources:
                if source['name'] not in cached_sources:
                    sources_to_scrape.append(source)
        else:
            sources_to_scrape = self.sources
        
        logger.info(f"Will scrape {len(sources_to_scrape)} sources (out of {len(self.sources)} total)")
        
        # Scraper les sources nécessaires
        new_articles = []
        for source in sources_to_scrape:
            try:
                if source['type'] == 'rss':
                    articles = self._scrape_rss(source)
                else:
                    articles = self._scrape_web(source)
                    
                # Filtrer par pertinence technologique
                relevant_articles = self._filter_tech_articles(articles)
                new_articles.extend(relevant_articles)
                all_articles.extend(relevant_articles)
                logger.info(f"Scraped {len(relevant_articles)} tech articles from {source['name']}")
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping {source['name']}: {e}")
        
        # Sauvegarder les nouveaux articles dans le cache
        if new_articles and use_cache:
            self.db.save_articles_to_cache(new_articles, self.cache_duration_hours)
            logger.info(f"Saved {len(new_articles)} new articles to cache")
        
        # Filtrer par fraîcheur (articles de moins de 3 jours)
        fresh_articles = self._filter_by_freshness(all_articles, max_days=3)
        logger.info(f"Kept {len(fresh_articles)} articles after freshness filter (< 3 days)")
        
        # Dédupliquer et scorer
        unique_articles = self._deduplicate_articles(fresh_articles)
        scored_articles = self._score_tech_articles(unique_articles)
        
        # Équilibrer les domaines
        balanced_articles = self._balance_domains(scored_articles, max_articles)
        
        # Enrichir les données finales pour le générateur
        final_articles = self._prepare_articles_for_generator(balanced_articles)
        
        # Valider et nettoyer les articles
        validated_articles = self.validate_and_clean_articles(final_articles)
        
        return sorted(validated_articles, key=lambda x: x['relevance_score'], reverse=True)[:max_articles]
    
    def _scrape_rss(self, source: Dict) -> List[Dict]:
        articles = []
        
        # Tenter de récupérer le feed avec timeout et retry
        for attempt in range(self.max_retries + 1):
            try:
                # Faire la requête HTTP avec timeout explicite
                response = requests.get(
                    source['url'], 
                    headers=self.headers, 
                    timeout=self.request_timeout
                )
                response.raise_for_status()
                
                # Parser le contenu RSS
                feed = feedparser.parse(response.content)
                
                # Vérifier si le feed est valide
                if hasattr(feed, 'entries') and feed.entries:
                    break
                else:
                    logger.warning(f"Empty or invalid RSS feed for {source['name']}")
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)  # Backoff exponentiel
                        continue
                    else:
                        return []
                        
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout fetching RSS feed for {source['name']} (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)  # Backoff exponentiel
                    continue
                else:
                    logger.error(f"Max retries exceeded for {source['name']} due to timeout")
                    return []
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error for {source['name']}: {e} (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)  # Backoff exponentiel
                    continue
                else:
                    logger.error(f"Max retries exceeded for {source['name']}: {e}")
                    return []
                    
            except Exception as e:
                logger.error(f"Unexpected error fetching RSS feed for {source['name']}: {e}")
                return []
        
        # Parser les articles avec extraction enrichie
        articles = []
        for entry in feed.entries[:12]:  # Augmenter à 12 articles pour plus de choix
            try:
                # Extraire toutes les métadonnées disponibles
                article = {
                    'title': entry.get('title', '').strip(),
                    'url': entry.get('link', ''),
                    'source': source['name'],
                    'category': source['category'],
                    'reliability': source['reliability'],
                    'domains': source['domains'],
                    'published': self._parse_date(entry.get('published', entry.get('updated', ''))),
                    'author': entry.get('author', ''),
                    'tags': [],
                    'summary': self._clean_html_summary(entry.get('summary', '')),
                    'content': '',  # Sera rempli par _extract_content_for_top_articles
                    'code_snippets': [],
                    'technologies_found': [],
                    'key_points': [],
                    'extraction_quality': 'pending',
                    'scraped_at': datetime.now(),
                    'metadata': {
                        'feed_title': feed.feed.get('title', ''),
                        'feed_subtitle': feed.feed.get('subtitle', ''),
                        'entry_id': entry.get('id', ''),
                    }
                }
                
                # Extraire les tags/catégories si disponibles
                if hasattr(entry, 'tags'):
                    article['tags'] = [tag.term for tag in entry.tags if hasattr(tag, 'term')][:5]
                
                # Essayer d'extraire plus de contenu si disponible
                if hasattr(entry, 'content') and entry.content:
                    # Certains feeds RSS ont le contenu complet dans 'content'
                    full_content = ''
                    for content in entry.content:
                        if hasattr(content, 'value'):
                            full_content += content.value + ' '
                    if full_content:
                        article['content'] = self._clean_html_summary(full_content)
                
                # Si pas de contenu, utiliser le summary
                if not article['content']:
                    article['content'] = article['summary']
                
                # Analyse préliminaire des technologies dans le titre et summary
                text_preview = (article['title'] + ' ' + article['summary']).lower()
                tech_mentions = []
                for domain_kw in self.tech_keywords.values():
                    for kw_list in domain_kw.values():
                        for kw in kw_list:
                            if kw in text_preview:
                                tech_mentions.append(kw)
                article['preview_technologies'] = tech_mentions[:5]
                
                articles.append(article)
                
            except Exception as e:
                logger.debug(f"Error parsing RSS entry from {source['name']}: {e}")
        
        # Extraction de contenu enrichie pour les articles prometteurs
        if articles:
            self._extract_content_for_top_articles(articles)
                
        return articles
    
    def _scrape_web(self, source: Dict) -> List[Dict]:
        articles = []
        
        # Tenter de récupérer la page avec timeout et retry
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(
                    source['url'], 
                    headers=self.headers, 
                    timeout=self.request_timeout
                )
                response.raise_for_status()
                break
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout fetching web page for {source['name']} (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"Max retries exceeded for {source['name']} due to timeout")
                    return []
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error for {source['name']}: {e} (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"Max retries exceeded for {source['name']}: {e}")
                    return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.select(source['selector'])[:15]
        
        for item in items:
            try:
                title_elem = item.select_one(source['title_selector'])
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                
                if not url.startswith('http'):
                    url = urljoin(source['url'], url)
                
                article = {
                    'title': title,
                    'url': url,
                    'source': source['name'],
                    'category': source['category'],
                    'reliability': source['reliability'],
                    'domains': source['domains'],
                    'published': datetime.now() - timedelta(hours=2),
                    'summary': '',
                    'scraped_at': datetime.now()
                }
                
                # Score HackerNews
                if source['name'] == 'Hacker News' and 'score_selector' in source:
                    score_elem = item.find_next_sibling()
                    if score_elem:
                        score_elem = score_elem.select_one(source['score_selector'])
                        if score_elem:
                            score_text = score_elem.get_text()
                            article['hn_score'] = int(re.findall(r'\d+', score_text)[0])
                
                articles.append(article)
                
            except Exception as e:
                logger.debug(f"Error extracting article: {e}")
                
        return articles
    
    def _clean_html_summary(self, summary: str) -> str:
        """Clean HTML from summary text with better preservation of content"""
        if not summary:
            return ""
        
        try:
            # Vérifier si c'est du HTML ou du texte brut
            if '<' in summary and '>' in summary:
                # C'est du HTML, nettoyer avec BeautifulSoup
                soup = BeautifulSoup(summary, 'html.parser')
                
                # Préserver les sauts de ligne des éléments de bloc
                for br in soup.find_all('br'):
                    br.replace_with(' ')
                for p in soup.find_all('p'):
                    p.append(' ')
                for div in soup.find_all('div'):
                    div.append(' ')
                
                # Extraire le texte
                text = soup.get_text(separator=' ')
            else:
                # C'est du texte brut
                text = summary
            
            # Nettoyer intelligemment
            # Supprimer les espaces multiples mais garder la structure
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Supprimer les caractères spéciaux répétitifs
            text = re.sub(r'[\-=_]{3,}', '', text)
            text = re.sub(r'\s*\|\s*', ' - ', text)
            
            # Garder plus de contenu pour un meilleur contexte
            return text[:800]  # Augmenter de 400 à 800 caractères
            
        except Exception as e:
            logger.debug(f"Error cleaning summary: {e}")
            return summary[:800] if summary else ""
    
    def _parse_date(self, date_str: str) -> datetime:
        try:
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            if parsed_date.tzinfo is not None:
                parsed_date = parsed_date.replace(tzinfo=None)
            return parsed_date
        except:
            return datetime.now()
    
    def _filter_by_freshness(self, articles: List[Dict], max_days: int = 3) -> List[Dict]:
        """Filtre les articles par fraîcheur (garde seulement les articles récents)"""
        fresh_articles = []
        cutoff_date = datetime.now() - timedelta(days=max_days)
        
        for article in articles:
            published_date = article.get('published', datetime.now())
            
            # S'assurer que la date est un objet datetime
            if isinstance(published_date, str):
                published_date = self._parse_date(published_date)
            
            # Garder seulement les articles récents
            if published_date >= cutoff_date:
                fresh_articles.append(article)
            else:
                logger.debug(f"Filtered out old article: {article['title'][:50]}... (published: {published_date})")
        
        return fresh_articles
    
    def _extract_article_content(self, article_url: str, max_length: int = 5000) -> Dict[str, str]:
        """Extrait le contenu complet d'un article avec métadonnées enrichies"""
        result = {
            'content': '',
            'clean_content': '',
            'code_snippets': [],
            'technologies': [],
            'key_points': [],
            'extraction_quality': 'none'
        }
        
        try:
            # Augmenter le timeout pour une meilleure extraction
            response = requests.get(
                article_url, 
                headers=self.headers, 
                timeout=10,  # Timeout plus généreux
                stream=True
            )
            response.raise_for_status()
            
            # Limiter la taille du contenu téléchargé
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > 1000000:  # Limiter à 1MB
                    break
            
            # Utiliser readability pour extraire le contenu principal
            doc = Document(content)
            result['content'] = doc.summary()
            
            # Extraction avancée avec BeautifulSoup
            soup = BeautifulSoup(doc.content(), 'html.parser')
            
            # Extraire les snippets de code
            code_blocks = soup.find_all(['code', 'pre'])
            for block in code_blocks[:5]:  # Limiter à 5 snippets
                code_text = block.get_text(strip=True)
                if len(code_text) > 50:  # Ignorer les petits snippets
                    result['code_snippets'].append(code_text[:500])
            
            # Supprimer les éléments non pertinents
            for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'aside', 'header', 'form', 'iframe', 'img']):
                tag.decompose()
            
            # Extraire les paragraphes principaux
            paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
            clean_text = []
            
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 30:  # Garder seulement les paragraphes significatifs
                    clean_text.append(text)
            
            # Joindre le texte nettoyé
            result['clean_content'] = ' '.join(clean_text)[:max_length]
            
            # Extraire les technologies mentionnées
            full_text = ' '.join(clean_text).lower()
            all_tech_keywords = []
            for domain_keywords in self.tech_keywords.values():
                for keyword_list in domain_keywords.values():
                    all_tech_keywords.extend(keyword_list)
            
            found_techs = set()
            for tech in all_tech_keywords:
                if tech in full_text:
                    found_techs.add(tech)
            result['technologies'] = list(found_techs)[:10]
            
            # Extraire les points clés (titres H2/H3)
            key_headings = soup.find_all(['h2', 'h3'])[:5]
            result['key_points'] = [h.get_text(strip=True) for h in key_headings if len(h.get_text(strip=True)) > 10]
            
            # Évaluer la qualité de l'extraction
            if len(result['clean_content']) > 1000:
                result['extraction_quality'] = 'high'
            elif len(result['clean_content']) > 500:
                result['extraction_quality'] = 'medium'
            elif len(result['clean_content']) > 100:
                result['extraction_quality'] = 'low'
            else:
                result['extraction_quality'] = 'poor'
            
            return result
            
        except requests.exceptions.Timeout:
            logger.debug(f"Timeout extracting content from {article_url}")
            result['extraction_quality'] = 'timeout'
            return result
        except requests.exceptions.RequestException as e:
            logger.debug(f"Error extracting content from {article_url}: {e}")
            result['extraction_quality'] = 'error'
            return result
        except Exception as e:
            logger.debug(f"Unexpected error extracting content from {article_url}: {e}")
            result['extraction_quality'] = 'error'
            return result
    
    def _extract_content_for_top_articles(self, articles: List[Dict]) -> None:
        """Extrait le contenu enrichi pour les articles les plus pertinents"""
        if not articles:
            return
            
        # Calculer un score de priorité pour chaque article
        for article in articles:
            priority_score = 0
            
            # Score basé sur la fraîcheur
            hours_old = (datetime.now() - article.get('published', datetime.now())).total_seconds() / 3600
            if hours_old < 6:
                priority_score += 30
            elif hours_old < 24:
                priority_score += 20
            elif hours_old < 48:
                priority_score += 10
            
            # Score basé sur la source
            if article.get('reliability', 0) >= 9:
                priority_score += 20
            elif article.get('reliability', 0) >= 7:
                priority_score += 10
            
            # Score basé sur les mots-clés technologiques dans le titre
            title_lower = article['title'].lower()
            tech_count = sum(1 for domain_kw in self.tech_keywords.values() 
                           for kw_list in domain_kw.values() 
                           for kw in kw_list if kw in title_lower)
            priority_score += tech_count * 5
            
            article['_priority_score'] = priority_score
        
        # Trier par score de priorité et sélectionner les meilleurs
        articles.sort(key=lambda x: x.get('_priority_score', 0), reverse=True)
        top_articles = articles[:min(8, len(articles))]  # Augmenter à 8 articles
        
        def extract_content_for_article(article):
            """Fonction pour extraire le contenu enrichi d'un article"""
            try:
                extracted_data = self._extract_article_content(article['url'])
                
                # Mettre à jour l'article avec les données enrichies
                if extracted_data['extraction_quality'] in ['high', 'medium']:
                    article['content'] = extracted_data['clean_content']
                    article['code_snippets'] = extracted_data['code_snippets']
                    article['technologies_found'] = extracted_data['technologies']
                    article['key_points'] = extracted_data['key_points']
                    article['extraction_quality'] = extracted_data['extraction_quality']
                    logger.info(f"High quality extraction for: {article['title'][:50]}... (quality: {extracted_data['extraction_quality']})")
                elif extracted_data['extraction_quality'] == 'low':
                    # Garder même le contenu de basse qualité mais le marquer
                    article['content'] = extracted_data['clean_content'] or article.get('summary', '')
                    article['extraction_quality'] = extracted_data['extraction_quality']
                    logger.debug(f"Low quality extraction for: {article['title'][:50]}...")
                else:
                    # Fallback sur le résumé
                    article['content'] = article.get('summary', '')
                    article['extraction_quality'] = 'fallback'
                    
            except Exception as e:
                logger.error(f"Failed to extract content for {article['title'][:50]}...: {e}")
                article['extraction_quality'] = 'error'
        
        # Extraire le contenu en parallèle avec plus de workers
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(extract_content_for_article, article) for article in top_articles]
            
            # Attendre plus longtemps pour une meilleure extraction
            for future in as_completed(futures, timeout=30):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Content extraction failed: {e}")
    
    def _filter_tech_articles(self, articles: List[Dict]) -> List[Dict]:
        """Filtre les articles pertinents pour le développement complet"""
        tech_articles = []
        
        for article in articles:
            text_content = (article['title'] + ' ' + article.get('summary', '')).lower()
            
            # Vérifier pertinence par domaine
            relevant_domains = []
            for domain, keywords in self.tech_keywords.items():
                for keyword_list in keywords.values():
                    if any(keyword in text_content for keyword in keyword_list):
                        relevant_domains.append(domain)
                        break
            
            # Garder si pertinent pour au moins un domaine ou source spécialisée
            if relevant_domains or any(domain in article['domains'] for domain in ['frontend', 'backend', 'ai']):
                article['relevant_domains'] = list(set(relevant_domains))
                tech_articles.append(article)
                
        return tech_articles
    
    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Déduplication intelligente basée sur le contenu et la similarité"""
        unique_articles = []
        seen_signatures = set()
        
        for article in articles:
            # Normalisation avancée du titre
            title = article['title'].lower()
            
            # Supprimer les mots vides et normaliser
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'how', 'why', 'what', 'when', 'where'}
            title_words = re.findall(r'\b\w+\b', title)
            significant_words = [w for w in title_words if w not in stop_words and len(w) > 2]
            
            # Créer une signature basée sur les mots significatifs
            if len(significant_words) >= 3:
                # Utiliser les 3-4 mots les plus significatifs
                signature = ' '.join(sorted(significant_words[:4]))
            else:
                # Fallback sur titre normalisé complet
                signature = re.sub(r'[^\w\s]', '', title)
            
            # Vérifier la similarité avec les articles déjà sélectionnés
            is_duplicate = False
            for seen_sig in seen_signatures:
                # Calculer la similarité
                common_words = set(signature.split()) & set(seen_sig.split())
                if len(common_words) >= min(3, len(signature.split()) * 0.7):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_signatures.add(signature)
                unique_articles.append(article)
            else:
                logger.debug(f"Duplicate detected: {article['title'][:50]}...")
                
        return unique_articles
    
    def _score_tech_articles(self, articles: List[Dict]) -> List[Dict]:
        """Score optimisé pour la qualité et pertinence du contenu"""
        for article in articles:
            score = 0
            
            # Score de base par fiabilité (augmenté pour privilégier les sources fiables)
            reliability = article['reliability']
            score += reliability * 8  # Augmenté de 6 à 8
            
            # Score par fraîcheur (courbe optimisée)
            published_date = article.get('published', datetime.now())
            if isinstance(published_date, str):
                published_date = self._parse_date(published_date)
            age_hours = (datetime.now() - published_date).total_seconds() / 3600
            if age_hours < 3:  # Super récent (moins de 3h)
                score += 50
            elif age_hours < 12:  # Très récent (moins de 12h)
                score += 40
            elif age_hours < 24:  # Récent (moins de 24h)
                score += 30
            elif age_hours < 48:  # Assez récent (moins de 2 jours)
                score += 20
            elif age_hours < 72:  # Limite (moins de 3 jours)
                score += 10
            else:
                score += 0
            
            # Score par domaines techniques (amélioré)
            text_content = (article['title'] + ' ' + article.get('summary', '')).lower()
            domain_matches = 0
            
            for domain, keywords in self.tech_keywords.items():
                domain_score = 0
                
                # Score pondéré par importance des mots-clés
                for keyword in keywords['high']:
                    if keyword in text_content:
                        domain_score += 20  # Augmenté de 15 à 20
                        domain_matches += 1
                        
                for keyword in keywords['medium']:
                    if keyword in text_content:
                        domain_score += 12  # Augmenté de 10 à 12
                        domain_matches += 1
                        
                for keyword in keywords['tools']:
                    if keyword in text_content:
                        domain_score += 6   # Augmenté de 5 à 6
                
                # Limiter le score par domaine mais permettre plus de variation
                score += min(domain_score, 40)  # Augmenté de 30 à 40
            
            # Bonus pour diversité technologique (articles couvrant plusieurs domaines)
            if domain_matches >= 3:
                score += 25
            elif domain_matches >= 2:
                score += 15
            
            # Bonus pour sources premium (élargi)
            premium_sources = [
                'OpenAI Blog', 'Google AI Blog', 'React Blog', 'Node.js Blog', 'Go Dev Blog', 'Rust Blog',
                'Hugging Face Blog', 'DeepMind Blog', 'Meta AI Blog', 'MIT CSAIL News', 'Stanford AI Lab',
                'MIT Technology Review', 'IEEE Spectrum', 'Spring Blog', 'Django News'
            ]
            if article['source'] in premium_sources:
                score += 30  # Augmenté de 25 à 30
            
            # Bonus pour sources académiques/recherche
            academic_sources = ['MIT CSAIL News', 'Stanford AI Lab', 'Papers With Code', 'MIT Technology Review', 'IEEE Spectrum']
            if article['source'] in academic_sources:
                score += 20
            
            # Bonus pour articles multi-domaines
            relevant_domains = article.get('relevant_domains', [])
            if len(relevant_domains) > 1:
                score += 15  # Augmenté de 10 à 15
            
            # Bonus HackerNews optimisé
            if 'hn_score' in article:
                hn_score = article['hn_score']
                if hn_score >= 100:
                    score += 30
                elif hn_score >= 50:
                    score += 20
                elif hn_score >= 20:
                    score += 10
                else:
                    score += 5
            
            # Malus pour titres trop courts ou peu informatifs
            title_length = len(article['title'])
            if title_length < 20:
                score -= 10
            elif title_length > 120:
                score -= 5
            
            # Bonus pour résumé détaillé
            summary_length = len(article.get('summary', ''))
            if summary_length > 200:
                score += 10
            elif summary_length > 100:
                score += 5
            
            article['relevance_score'] = max(0, score)
            
        return articles
    
    def _balance_domains(self, articles: List[Dict], max_articles: int) -> List[Dict]:
        """Équilibrage optimisé pour la qualité par domaine"""
        articles_by_domain = {'frontend': [], 'backend': [], 'ai': [], 'multi': []}
        
        for article in articles:
            domains = article.get('relevant_domains', [])
            if len(domains) > 1:
                articles_by_domain['multi'].append(article)
            elif 'ai' in domains:
                articles_by_domain['ai'].append(article)
            elif 'backend' in domains:
                articles_by_domain['backend'].append(article)
            elif 'frontend' in domains:
                articles_by_domain['frontend'].append(article)
            else:
                # Assigner selon la catégorie de la source avec priorité qualité
                source_category = article.get('category', '')
                if source_category in ['ai']:
                    articles_by_domain['ai'].append(article)
                elif source_category in ['backend']:
                    articles_by_domain['backend'].append(article)
                else:
                    articles_by_domain['frontend'].append(article)
        
        # Équilibrage adaptatif basé sur la qualité disponible
        balanced = []
        
        # Trier chaque domaine par score de pertinence
        for domain in articles_by_domain:
            articles_by_domain[domain].sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Répartition dynamique selon le contenu disponible
        domain_counts = {k: len(v) for k, v in articles_by_domain.items()}
        total_available = sum(domain_counts.values())
        
        if total_available == 0:
            return []
        
        # Assurer un minimum de qualité par domaine
        min_score_threshold = 50  # Score minimum pour être sélectionné
        
        # Calculer les quotas adaptatifs
        base_quota = max_articles // 4  # Base de 25% par domaine principal
        remaining = max_articles
        
        # Priorité aux domaines avec du contenu de qualité
        for domain in ['ai', 'backend', 'frontend', 'multi']:
            quality_articles = [a for a in articles_by_domain[domain] if a['relevance_score'] >= min_score_threshold]
            
            if domain == 'multi':
                # Articles multi-domaines : 15% minimum, 25% maximum
                quota = min(len(quality_articles), max(int(max_articles * 0.15), int(max_articles * 0.25)))
            else:
                # Domaines spécialisés : équilibré selon disponibilité
                available_count = len(quality_articles)
                if available_count == 0:
                    quota = 0
                elif available_count < base_quota:
                    quota = available_count
                else:
                    quota = min(base_quota + 2, available_count)  # +2 pour favoriser la diversité
            
            selected = quality_articles[:quota]
            balanced.extend(selected)
            remaining -= len(selected)
        
        # Compléter avec les meilleurs articles restants si besoin
        if remaining > 0:
            all_remaining = []
            for domain_articles in articles_by_domain.values():
                for article in domain_articles:
                    if article not in balanced and article['relevance_score'] >= min_score_threshold:
                        all_remaining.append(article)
            
            all_remaining.sort(key=lambda x: x['relevance_score'], reverse=True)
            balanced.extend(all_remaining[:remaining])
        
        return balanced
    
    def get_articles_by_domain(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Organise les articles par domaine technique"""
        by_domain = {'frontend': [], 'backend': [], 'ai': [], 'multi': []}
        
        for article in articles:
            domains = article.get('relevant_domains', [])
            if len(domains) > 1:
                by_domain['multi'].append(article)
            elif 'ai' in domains:
                by_domain['ai'].append(article)
            elif 'backend' in domains:
                by_domain['backend'].append(article)
            elif 'frontend' in domains:
                by_domain['frontend'].append(article)
                
        return by_domain
    
    def get_trending_technologies(self, articles: List[Dict]) -> Dict[str, List[str]]:
        """Technologies tendances par domaine"""
        tech_counts = {'frontend': {}, 'backend': {}, 'ai': {}}
        
        for article in articles:
            text = (article['title'] + ' ' + article.get('summary', '')).lower()
            
            for domain, keywords in self.tech_keywords.items():
                for keyword_list in keywords.values():
                    for keyword in keyword_list:
                        if keyword in text:
                            if keyword not in tech_counts[domain]:
                                tech_counts[domain][keyword] = 0
                            # Pondérer par le score et la qualité d'extraction
                            weight = article.get('relevance_score', 1)
                            if article.get('extraction_quality') == 'high':
                                weight *= 1.5
                            elif article.get('extraction_quality') == 'medium':
                                weight *= 1.2
                            tech_counts[domain][keyword] += weight
        
        # Top 5 par domaine
        trending = {}
        for domain, counts in tech_counts.items():
            sorted_techs = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
            trending[domain] = [tech for tech, _ in sorted_techs]
            
        return trending
    
    def scrape_domain_sources(self, domain: str, max_articles: int = 50, use_cache: bool = True) -> List[Dict]:
        """Scrape seulement les sources d'un domaine spécifique"""
        # Nettoyer le cache expiré
        self.db.clear_expired_cache()
        
        domain_articles = []
        
        # Mapper les domaines aux catégories de sources
        domain_categories = {
            'frontend': ['frontend', 'dev_fr', 'community'],
            'backend': ['backend', 'dev_fr', 'devops', 'enterprise', 'community'],
            'ai': ['ai', 'dev_fr', 'community'],
        }
        
        # Filtrer les sources par domaine
        target_categories = domain_categories.get(domain, [])
        domain_sources = []
        domain_source_names = []
        
        for source in self.sources:
            source_category = source.get('category', '')
            source_domains = source.get('domains', [])
            
            # Inclure si la catégorie correspond ou si le domaine est dans les domaines de la source
            if source_category in target_categories or domain in source_domains:
                domain_sources.append(source)
                domain_source_names.append(source['name'])
        
        logger.info(f"Domain {domain} has {len(domain_sources)} relevant sources")
        
        if use_cache:
            # Récupérer TOUS les articles en cache pour ce domaine
            cached_articles = self.db.get_cached_articles(source_names=domain_source_names)
            logger.info(f"Found {len(cached_articles)} cached articles for domain {domain}")
            
            # Filtrer et scorer les articles du cache immédiatement
            fresh_cached = self._filter_by_freshness(cached_articles, max_days=3)
            unique_cached = self._deduplicate_articles(fresh_cached)
            scored_cached = self._score_domain_articles(unique_cached, domain)
            
            # Trier et prendre les meilleurs articles du cache
            sorted_cached = sorted(scored_cached, key=lambda x: x['relevance_score'], reverse=True)
            
            logger.info(f"Cache has {len(sorted_cached)} scored articles for domain {domain}")
            
            # Si on a déjà assez d'articles de qualité dans le cache, on retourne directement
            if len(sorted_cached) >= max_articles:
                logger.info(f"Cache has enough articles ({len(sorted_cached)} >= {max_articles}), skipping scraping")
                return sorted_cached[:max_articles]
            
            # Sinon, on ajoute les articles du cache et on scrape pour compléter
            domain_articles.extend(cached_articles)
            
            # On calcule combien d'articles supplémentaires on a besoin
            articles_needed = max(10, max_articles - len(sorted_cached))  # Au moins 10 articles frais
            logger.info(f"Need {articles_needed} more articles, will scrape some sources")
            
            # Identifier les sources qui ont le moins d'articles récents en cache
            source_article_counts = {}
            for source in domain_sources:
                source_article_counts[source['name']] = sum(1 for a in cached_articles if a['source'] == source['name'])
            
            # Trier les sources par nombre d'articles en cache (moins = priorité)
            sources_to_scrape = sorted(domain_sources, key=lambda s: source_article_counts.get(s['name'], 0))
            # Limiter le nombre de sources à scraper
            sources_to_scrape = sources_to_scrape[:max(3, len(sources_to_scrape) // 4)]  # Max 25% des sources
        else:
            sources_to_scrape = domain_sources
        
        logger.info(f"Will scrape {len(sources_to_scrape)} sources for domain {domain}")
        
        # Scraper les sources en parallèle (limité à 4 threads)
        new_articles = []
        
        def scrape_source(source):
            """Fonction pour scraper une source"""
            try:
                if source['type'] == 'rss':
                    articles = self._scrape_rss(source)
                else:
                    articles = self._scrape_web(source)
                    
                # Filtrer par pertinence technologique
                relevant_articles = self._filter_tech_articles(articles)
                logger.info(f"Scraped {len(relevant_articles)} tech articles from {source['name']}")
                return relevant_articles
                
            except Exception as e:
                logger.error(f"Error scraping {source['name']}: {e}")
                return []
        
        # Scraping parallèle avec un maximum de 4 threads
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(scrape_source, source) for source in sources_to_scrape]
            
            # Collecter les résultats avec timeout
            for future in as_completed(futures, timeout=60):
                try:
                    articles = future.result()
                    if articles:
                        new_articles.extend(articles)
                        domain_articles.extend(articles)
                except Exception as e:
                    logger.error(f"Error in parallel scraping: {e}")
        
        # Sauvegarder les nouveaux articles dans le cache
        if new_articles and use_cache:
            self.db.save_articles_to_cache(new_articles, self.cache_duration_hours)
            logger.info(f"Saved {len(new_articles)} new articles to cache for domain {domain}")
        
        # Filtrer par fraîcheur (articles de moins de 3 jours)
        fresh_articles = self._filter_by_freshness(domain_articles, max_days=3)
        logger.info(f"Kept {len(fresh_articles)} articles after freshness filter (< 3 days)")
        
        # Dédupliquer et scorer spécifiquement pour le domaine
        unique_articles = self._deduplicate_articles(fresh_articles)
        scored_articles = self._score_domain_articles(unique_articles, domain)
        
        # Trier par score et limiter
        sorted_articles = sorted(scored_articles, key=lambda x: x['relevance_score'], reverse=True)
        
        return sorted_articles[:max_articles]
    
    def _score_domain_articles(self, articles: List[Dict], target_domain: str) -> List[Dict]:
        """Score les articles spécifiquement pour un domaine cible"""
        keywords = self.tech_keywords.get(target_domain, {})
        
        if not keywords:
            # Fallback au scoring général si le domaine n'est pas reconnu
            return self._score_tech_articles(articles)
        
        for article in articles:
            score = 0
            
            # Score de base selon la fiabilité de la source
            score += article.get('reliability', 5) * 8
            
            # Score de fraîcheur (courbe exponentielle)
            hours_old = (datetime.now() - article['published']).total_seconds() / 3600
            if hours_old <= 24:
                score += 50
            elif hours_old <= 48:
                score += 30
            elif hours_old <= 72:
                score += 15
            else:
                score += 5
            
            # Analyse du contenu pour le domaine spécifique
            text_content = f"{article['title']} {article.get('summary', '')}".lower()
            
            domain_score = 0
            domain_matches = 0
            
            # Mots-clés haute priorité pour le domaine cible
            for keyword in keywords.get('high', []):
                if keyword in text_content:
                    domain_score += 30  # Score élevé pour les mots-clés prioritaires
                    domain_matches += 1
            
            # Mots-clés moyenne priorité
            for keyword in keywords.get('medium', []):
                if keyword in text_content:
                    domain_score += 20
                    domain_matches += 1
            
            # Outils et technologies
            for keyword in keywords.get('tools', []):
                if keyword in text_content:
                    domain_score += 15
                    domain_matches += 1
            
            # Bonus supplémentaire si l'article a plusieurs mots-clés du domaine
            if domain_matches >= 3:
                domain_score += 40
            elif domain_matches >= 2:
                domain_score += 25
            elif domain_matches >= 1:
                domain_score += 10
            
            # Malus si aucun mot-clé du domaine cible n'est trouvé
            if domain_matches == 0:
                domain_score -= 30
            
            score += domain_score
            
            # Bonus pour sources spécialisées dans le domaine
            source_domains = article.get('domains', [])
            if target_domain in source_domains:
                score += 25
            
            # Bonus pour catégorie de source alignée
            source_category = article.get('category', '')
            if target_domain == 'frontend' and source_category == 'frontend':
                score += 20
            elif target_domain == 'backend' and source_category in ['backend', 'devops', 'enterprise']:
                score += 20
            elif target_domain == 'ai' and source_category == 'ai':
                score += 20
            
            # Bonus pour sources premium
            premium_sources = [
                'OpenAI Blog', 'Google AI Blog', 'React Blog', 'Node.js Blog', 'Go Dev Blog', 'Rust Blog',
                'Hugging Face Blog', 'DeepMind Blog', 'Meta AI Blog', 'MIT CSAIL News', 'Stanford AI Lab',
                'MIT Technology Review', 'IEEE Spectrum', 'Spring Blog', 'Django News', 'CSS-Tricks',
                'A List Apart', 'Smashing Magazine', 'Vue.js News', 'Angular Blog', 'Web.dev'
            ]
            if article['source'] in premium_sources:
                score += 30
            
            # Malus pour titres peu informatifs
            title_length = len(article['title'])
            if title_length < 20:
                score -= 15
            elif title_length > 120:
                score -= 5
            
            # Bonus pour résumé détaillé
            summary_length = len(article.get('summary', ''))
            if summary_length > 200:
                score += 10
            elif summary_length > 100:
                score += 5
            
            article['relevance_score'] = max(0, score)
            article['domain_matches'] = domain_matches
            
        return articles
    
    def _prepare_articles_for_generator(self, articles: List[Dict]) -> List[Dict]:
        """Prépare et structure les articles pour une utilisation optimale par le générateur"""
        prepared_articles = []
        
        for article in articles:
            # Structure optimisée pour le générateur
            prepared_article = {
                # Informations de base
                'id': article.get('url', '').split('/')[-1][:50] or str(hash(article['title']))[:8],
                'title': article['title'],
                'url': article['url'],
                'source': article['source'],
                'published': article['published'],
                'author': article.get('author', ''),
                
                # Scores et qualité
                'relevance_score': article.get('relevance_score', 0),
                'reliability': article.get('reliability', 5),
                'extraction_quality': article.get('extraction_quality', 'unknown'),
                
                # Contenu principal
                'content': {
                    'summary': article.get('summary', ''),
                    'full_text': article.get('content', ''),
                    'key_points': article.get('key_points', []),
                    'code_snippets': article.get('code_snippets', []),
                },
                
                # Métadonnées techniques
                'technical_data': {
                    'domains': article.get('relevant_domains', article.get('domains', [])),
                    'technologies': list(set(
                        article.get('technologies_found', []) + 
                        article.get('preview_technologies', [])
                    )),
                    'tags': article.get('tags', []),
                    'category': article.get('category', ''),
                },
                
                # Indicateurs pour le générateur
                'generation_hints': {
                    'has_code': len(article.get('code_snippets', [])) > 0,
                    'is_tutorial': any(word in article['title'].lower() 
                                     for word in ['tutorial', 'guide', 'how to', 'introduction']),
                    'is_news': any(word in article['title'].lower() 
                                 for word in ['announces', 'releases', 'launches', 'introduces']),
                    'is_technical': len(article.get('technologies_found', [])) >= 3,
                    'content_length': len(article.get('content', '')),
                    'freshness': self._calculate_freshness(article['published']),
                },
                
                # Données pour enrichissement
                'enrichment_data': {
                    'needs_more_content': article.get('extraction_quality', '') in ['low', 'poor', 'fallback'],
                    'confidence_level': self._calculate_confidence_level(article),
                    'suggested_angle': self._suggest_content_angle(article),
                }
            }
            
            prepared_articles.append(prepared_article)
        
        return prepared_articles
    
    def _calculate_confidence_level(self, article: Dict) -> str:
        """Calcule le niveau de confiance pour la génération de contenu"""
        score = 0
        
        # Qualité d'extraction
        quality = article.get('extraction_quality', 'unknown')
        if quality == 'high':
            score += 40
        elif quality == 'medium':
            score += 25
        elif quality == 'low':
            score += 10
        
        # Fiabilité de la source
        reliability = article.get('reliability', 5)
        score += reliability * 3
        
        # Contenu disponible
        content_length = len(article.get('content', ''))
        if content_length > 2000:
            score += 30
        elif content_length > 1000:
            score += 20
        elif content_length > 500:
            score += 10
        
        # Technologies identifiées
        tech_count = len(article.get('technologies_found', []))
        if tech_count >= 5:
            score += 20
        elif tech_count >= 3:
            score += 15
        elif tech_count >= 1:
            score += 10
        
        # Points clés extraits
        if len(article.get('key_points', [])) >= 3:
            score += 10
        
        # Snippets de code
        if len(article.get('code_snippets', [])) > 0:
            score += 15
        
        # Déterminer le niveau
        if score >= 80:
            return 'high'
        elif score >= 50:
            return 'medium'
        elif score >= 30:
            return 'low'
        else:
            return 'very_low'
    
    def _suggest_content_angle(self, article: Dict) -> str:
        """Suggère un angle de contenu pour le générateur"""
        title_lower = article['title'].lower()
        content_lower = (article.get('content', '') + ' ' + article.get('summary', '')).lower()
        
        # Détecter le type de contenu
        if any(word in title_lower for word in ['tutorial', 'guide', 'how to', 'getting started']):
            return 'tutorial'
        elif any(word in title_lower for word in ['releases', 'announces', 'launches', 'introduces', 'version']):
            return 'news_analysis'
        elif any(word in title_lower for word in ['vs', 'versus', 'comparison', 'differences']):
            return 'comparison'
        elif any(word in title_lower for word in ['best practices', 'tips', 'mistakes', 'patterns']):
            return 'best_practices'
        elif any(word in title_lower for word in ['performance', 'optimization', 'speed', 'faster']):
            return 'performance'
        elif any(word in title_lower for word in ['security', 'vulnerabilit', 'exploit', 'patch']):
            return 'security'
        elif any(word in content_lower for word in ['research', 'paper', 'study', 'findings']):
            return 'research_insights'
        elif len(article.get('code_snippets', [])) > 2:
            return 'code_deep_dive'
        elif 'ai' in article.get('domains', []) or any(word in content_lower for word in ['llm', 'machine learning', 'neural']):
            return 'ai_innovation'
        else:
            # Angle par défaut basé sur le domaine principal
            domains = article.get('relevant_domains', [])
            if 'frontend' in domains:
                return 'frontend_trends'
            elif 'backend' in domains:
                return 'backend_architecture'
            else:
                return 'technical_insights'
    
    def _calculate_freshness(self, published_date: datetime) -> str:
        """Calcule la fraîcheur d'un article"""
        if not isinstance(published_date, datetime):
            return 'unknown'
        
        age = datetime.now() - published_date
        hours = age.total_seconds() / 3600
        
        if hours < 6:
            return 'breaking'
        elif hours < 12:
            return 'very_fresh'
        elif hours < 24:
            return 'fresh'
        elif hours < 48:
            return 'recent'
        elif hours < 72:
            return 'relevant'
        else:
            return 'older'
    
    def validate_and_clean_articles(self, articles: List[Dict]) -> List[Dict]:
        """Valide et nettoie les articles pour assurer la qualité des données"""
        cleaned_articles = []
        
        for article in articles:
            try:
                # Vérifications de base
                if not article.get('title') or not article.get('url'):
                    logger.warning(f"Skipping article without title or URL")
                    continue
                
                # Nettoyer le titre
                article['title'] = self._clean_title(article['title'])
                
                # S'assurer que les dates sont au bon format
                if 'published' in article and not isinstance(article['published'], datetime):
                    article['published'] = self._parse_date(str(article['published']))
                
                # Valider et nettoyer le contenu
                if 'content' in article and isinstance(article['content'], dict):
                    content = article['content']
                    
                    # Nettoyer le texte complet
                    if 'full_text' in content:
                        content['full_text'] = self._clean_text_content(content['full_text'])
                    
                    # Nettoyer les snippets de code
                    if 'code_snippets' in content:
                        content['code_snippets'] = [self._clean_code_snippet(s) for s in content['code_snippets'] if s]
                    
                    # Valider les points clés
                    if 'key_points' in content:
                        content['key_points'] = [p.strip() for p in content['key_points'] if p and len(p.strip()) > 10]
                
                # Générer un ID unique si nécessaire
                if 'id' not in article or not article['id']:
                    article['id'] = self._generate_article_id(article)
                
                # Ajouter des métadonnées de validation
                article['validation'] = {
                    'validated_at': datetime.now(),
                    'content_quality': self._assess_content_quality(article),
                    'is_complete': self._check_article_completeness(article)
                }
                
                cleaned_articles.append(article)
                
            except Exception as e:
                logger.error(f"Error validating article: {e}")
                continue
        
        return cleaned_articles
    
    def _clean_title(self, title: str) -> str:
        """Nettoie et normalise un titre"""
        # Supprimer les espaces multiples
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Supprimer les caractères spéciaux indésirables au début/fin
        title = re.sub(r'^[\W_]+|[\W_]+$', '', title)
        
        # Limiter la longueur
        if len(title) > 200:
            title = title[:197] + '...'
        
        return title
    
    def _clean_text_content(self, text: str) -> str:
        """Nettoie le contenu textuel"""
        if not text:
            return ''
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normaliser les espaces et sauts de ligne
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Supprimer les URLs très longues qui polluent le texte
        text = re.sub(r'https?://\S{100,}', '[URL]', text)
        
        return text.strip()
    
    def _clean_code_snippet(self, code: str) -> str:
        """Nettoie un snippet de code"""
        if not code:
            return ''
        
        # Supprimer les espaces en début/fin
        code = code.strip()
        
        # Limiter la taille
        if len(code) > 1000:
            code = code[:997] + '...'
        
        return code
    
    def _generate_article_id(self, article: Dict) -> str:
        """Génère un ID unique pour un article"""
        # Utiliser le titre et l'URL pour générer un hash unique
        unique_string = f"{article.get('title', '')}{article.get('url', '')}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:12]
    
    def _assess_content_quality(self, article: Dict) -> str:
        """Evalue la qualité globale du contenu"""
        score = 0
        
        # Vérifier la présence de contenu
        content = article.get('content', {})
        if isinstance(content, dict):
            if len(content.get('full_text', '')) > 1000:
                score += 3
            elif len(content.get('full_text', '')) > 500:
                score += 2
            elif len(content.get('summary', '')) > 200:
                score += 1
            
            if content.get('key_points'):
                score += 1
            
            if content.get('code_snippets'):
                score += 1
        
        # Vérifier les métadonnées techniques
        tech_data = article.get('technical_data', {})
        if tech_data.get('technologies'):
            score += 1
        
        # Vérifier la qualité d'extraction
        if article.get('extraction_quality') in ['high', 'medium']:
            score += 2
        
        # Déterminer le niveau
        if score >= 7:
            return 'excellent'
        elif score >= 5:
            return 'good'
        elif score >= 3:
            return 'acceptable'
        else:
            return 'poor'
    
    def _check_article_completeness(self, article: Dict) -> bool:
        """Vérifie si un article contient toutes les données essentielles"""
        required_fields = ['title', 'url', 'source', 'published']
        
        for field in required_fields:
            if not article.get(field):
                return False
        
        # Vérifier qu'il y a au moins un contenu
        content = article.get('content', {})
        if isinstance(content, dict):
            has_content = bool(content.get('summary') or content.get('full_text'))
        else:
            has_content = bool(content)
        
        return has_content