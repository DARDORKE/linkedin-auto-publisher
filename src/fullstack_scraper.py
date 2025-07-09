"""
Scraper optimisé pour récupérer des articles tech de qualité
Version simplifiée et performante
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from loguru import logger
import time
from typing import List, Dict, Optional, Set, Tuple
import re
from urllib.parse import urljoin
import feedparser
from src.database import DatabaseManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from readability import Document

class FullStackDevScraper:
    """Scraper optimisé pour les articles de développement fullstack"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
        self.cache_duration_hours = 12
        self.request_timeout = 8
        self.max_retries = 1
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Sources de qualité par domaine
        self._init_quality_sources()
        
        # Mots-clés pour la pertinence
        self.domain_keywords = {
            'frontend': ['react', 'vue', 'angular', 'svelte', 'css', 'javascript', 'typescript', 
                        'nextjs', 'nuxtjs', 'tailwind', 'webpack', 'vite'],
            'backend': ['nodejs', 'python', 'java', 'go', 'rust', 'api', 'database', 'docker', 
                       'kubernetes', 'microservices', 'serverless', 'redis', 'postgresql'],
            'ai': ['ai', 'ml', 'llm', 'gpt', 'transformer', 'neural', 'deep learning', 
                  'pytorch', 'tensorflow', 'langchain', 'huggingface', 'openai']
        }
    
    def _init_quality_sources(self):
        """Initialise les sources de qualité par domaine"""
        self.sources = {
            'frontend': [
                {"name": "CSS-Tricks", "url": "https://css-tricks.com/feed/", "weight": 10},
                {"name": "Smashing Magazine", "url": "https://www.smashingmagazine.com/feed/", "weight": 9},
                {"name": "Web.dev", "url": "https://web.dev/feed.xml", "weight": 10},
                {"name": "React Blog", "url": "https://react.dev/rss.xml", "weight": 10},
                {"name": "Vue.js News", "url": "https://news.vuejs.org/rss.xml", "weight": 9},
                {"name": "Angular Blog", "url": "https://blog.angular.io/feed", "weight": 9},
                {"name": "Frontend Focus", "url": "https://frontendfoc.us/rss", "weight": 8},
                {"name": "A List Apart", "url": "https://alistapart.com/main/feed/", "weight": 9},
            ],
            'backend': [
                {"name": "Node.js Blog", "url": "https://nodejs.org/en/feed/blog.xml", "weight": 10},
                {"name": "Go Dev Blog", "url": "https://go.dev/blog/feed.atom", "weight": 10},
                {"name": "Rust Blog", "url": "https://blog.rust-lang.org/feed.xml", "weight": 10},
                {"name": "Django News", "url": "https://django-news.com/issues.rss", "weight": 9},
                {"name": "AWS News", "url": "https://aws.amazon.com/about-aws/whats-new/recent/feed/", "weight": 8},
                {"name": "Docker Blog", "url": "https://www.docker.com/blog/feed/", "weight": 9},
                {"name": "Kubernetes Blog", "url": "https://kubernetes.io/feed.xml", "weight": 9},
                {"name": "Real Python", "url": "https://realpython.com/atom.xml", "weight": 9},
            ],
            'ai': [
                {"name": "OpenAI Blog", "url": "https://openai.com/news/rss.xml", "weight": 10},
                {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml", "weight": 10},
                {"name": "Google AI Blog", "url": "https://research.google/blog/rss/", "weight": 10},
                {"name": "Anthropic News", "url": "https://rsshub.app/anthropic/news", "weight": 10},
                {"name": "Towards Data Science", "url": "https://towardsdatascience.com/feed", "weight": 7},
                {"name": "Machine Learning Mastery", "url": "https://machinelearningmastery.com/feed/", "weight": 8},
                {"name": "The Batch", "url": "https://www.deeplearning.ai/the-batch/rss/", "weight": 9},
            ],
            'general': [
                {"name": "GitHub Blog", "url": "https://github.blog/feed/", "weight": 9},
                {"name": "Stack Overflow Blog", "url": "https://stackoverflow.blog/feed/", "weight": 8},
                {"name": "InfoQ", "url": "https://www.infoq.com/feed/", "weight": 9},
                {"name": "The New Stack", "url": "https://thenewstack.io/feed/", "weight": 8},
                {"name": "Dev.to - Top", "url": "https://dev.to/feed", "weight": 7},
            ]
        }
    
    def scrape_all_sources(self, max_articles: int = 40, use_cache: bool = True) -> List[Dict]:
        """
        Scrape toutes les sources et retourne les meilleurs articles
        Optimisé pour la performance et la qualité
        """
        # Nettoyer le cache expiré
        self.db.clear_expired_cache()
        
        # Collecter les articles par domaine
        domain_articles = {}
        
        # Articles par domaine souhaités
        articles_per_domain = {
            'frontend': max(10, max_articles // 3),
            'backend': max(10, max_articles // 3),
            'ai': max(10, max_articles // 3),
            'general': max(5, max_articles // 6)
        }
        
        # Scraper chaque domaine
        for domain, count in articles_per_domain.items():
            logger.info(f"Scraping {domain} domain (target: {count} articles)...")
            domain_articles[domain] = self._scrape_domain(domain, count, use_cache)
        
        # Combiner tous les articles
        all_articles = []
        for articles in domain_articles.values():
            all_articles.extend(articles)
        
        # Trier par score global et limiter
        all_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Préparer pour le générateur
        final_articles = self._prepare_for_generator(all_articles[:max_articles])
        
        return final_articles
    
    def scrape_domain_sources(self, domain: str, max_articles: int = 50, use_cache: bool = True) -> List[Dict]:
        """Scrape spécifiquement un domaine"""
        if domain not in self.sources:
            logger.error(f"Domain {domain} not supported")
            return []
        
        articles = self._scrape_domain(domain, max_articles, use_cache)
        return self._prepare_for_generator(articles)
    
    def _scrape_domain(self, domain: str, max_articles: int, use_cache: bool) -> List[Dict]:
        """Scrape interne pour un domaine"""
        # Vérifier le cache
        if use_cache:
            source_names = [s['name'] for s in self.sources.get(domain, [])]
            cached_articles = self.db.get_cached_articles(source_names=source_names)
            
            # Filtrer les articles récents
            fresh_cached = [a for a in cached_articles 
                          if (datetime.now() - a['published']).days < 3]
            
            if len(fresh_cached) >= max_articles:
                logger.info(f"Using {len(fresh_cached)} cached articles for {domain}")
                return self._process_and_score(fresh_cached, domain)[:max_articles]
        
        # Scraper les sources
        all_articles = []
        sources = self.sources.get(domain, [])
        
        # Limiter le nombre de sources pour la performance
        sources_to_scrape = sources[:6]
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_source = {
                executor.submit(self._scrape_source, source): source 
                for source in sources_to_scrape
            }
            
            for future in as_completed(future_to_source, timeout=20):
                try:
                    articles = future.result()
                    if articles:
                        all_articles.extend(articles)
                except Exception as e:
                    logger.error(f"Error scraping source: {e}")
        
        # Traiter et scorer
        processed = self._process_and_score(all_articles, domain)
        
        # Sauvegarder en cache
        if use_cache and processed:
            self.db.save_articles_to_cache(processed[:max_articles], self.cache_duration_hours)
        
        return processed[:max_articles]
    
    def _scrape_source(self, source: Dict) -> List[Dict]:
        """Scrape une source RSS"""
        try:
            response = requests.get(
                source['url'], 
                headers=self.headers, 
                timeout=self.request_timeout
            )
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            if not hasattr(feed, 'entries') or not feed.entries:
                return []
            
            articles = []
            for entry in feed.entries[:8]:  # Max 8 articles par source
                try:
                    article = {
                        'title': entry.get('title', '').strip(),
                        'url': entry.get('link', ''),
                        'source': source['name'],
                        'source_weight': source['weight'],
                        'published': self._parse_date(entry.get('published', entry.get('updated', ''))),
                        'summary': self._clean_text(entry.get('summary', ''))[:600],
                        'content': '',  # Sera rempli plus tard si nécessaire
                        'scraped_at': datetime.now(),
                        'tags': []
                    }
                    
                    # Extraire les tags
                    if hasattr(entry, 'tags'):
                        article['tags'] = [tag.term for tag in entry.tags if hasattr(tag, 'term')][:5]
                    
                    # Vérifier si l'article a du contenu complet dans le RSS
                    if hasattr(entry, 'content') and entry.content:
                        full_content = ' '.join(c.value for c in entry.content if hasattr(c, 'value'))
                        if full_content:
                            article['content'] = self._clean_text(full_content)[:2000]
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.debug(f"Error parsing entry: {e}")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {e}")
            return []
    
    def _process_and_score(self, articles: List[Dict], domain: str) -> List[Dict]:
        """Traite et score les articles"""
        # Dédupliquer
        unique_articles = self._deduplicate(articles)
        
        # Scorer
        keywords = self.domain_keywords.get(domain, [])
        for article in unique_articles:
            score = 0
            
            # Score de source
            score += article.get('source_weight', 5) * 3
            
            # Score de fraîcheur
            age_hours = (datetime.now() - article['published']).total_seconds() / 3600
            if age_hours < 12:
                score += 30
            elif age_hours < 24:
                score += 25
            elif age_hours < 48:
                score += 20
            elif age_hours < 72:
                score += 15
            else:
                score += 5
            
            # Score de pertinence
            text = (article['title'] + ' ' + article.get('summary', '')).lower()
            keyword_matches = sum(1 for kw in keywords if kw in text)
            score += min(keyword_matches * 8, 40)  # Cap à 40
            
            # Bonus pour patterns
            title_lower = article['title'].lower()
            if any(p in title_lower for p in ['tutorial', 'guide', 'how to', 'introduction']):
                score += 15
            if any(p in title_lower for p in ['releases', 'announces', 'launches', 'new']):
                score += 12
            if any(p in title_lower for p in ['tips', 'tricks', 'best practices']):
                score += 10
            
            # Malus pour titres trop courts
            if len(article['title']) < 20:
                score -= 10
            
            article['relevance_score'] = score
            article['domain'] = domain
        
        # Trier par score
        unique_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Enrichir les top articles
        self._enrich_top_articles(unique_articles[:10])
        
        return unique_articles
    
    def _enrich_top_articles(self, articles: List[Dict]):
        """Enrichit les meilleurs articles avec du contenu"""
        for i, article in enumerate(articles[:5]):  # Seulement les 5 premiers
            try:
                if not article.get('content') or len(article['content']) < 500:
                    # Extraire le contenu si pas déjà fait
                    content = self._extract_content(article['url'])
                    if content:
                        article['content'] = content
                        article['extraction_quality'] = 'full'
                    else:
                        article['content'] = article.get('summary', '')
                        article['extraction_quality'] = 'summary_only'
                else:
                    article['extraction_quality'] = 'rss_content'
                
                # Détecter les technologies mentionnées
                full_text = (article['title'] + ' ' + article['content']).lower()
                found_techs = []
                for domain_kw in self.domain_keywords.values():
                    for kw in domain_kw:
                        if kw in full_text:
                            found_techs.append(kw)
                
                article['technologies_found'] = list(set(found_techs))[:10]
                
            except Exception as e:
                logger.debug(f"Error enriching article: {e}")
                article['extraction_quality'] = 'error'
    
    def _extract_content(self, url: str) -> Optional[str]:
        """Extraction de contenu optimisée"""
        try:
            response = requests.get(url, headers=self.headers, timeout=6)
            response.raise_for_status()
            
            # Utiliser readability pour extraction
            doc = Document(response.content)
            content = doc.summary()
            
            # Nettoyer avec BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Supprimer les éléments inutiles
            for tag in soup.find_all(['script', 'style', 'nav', 'aside']):
                tag.decompose()
            
            text = soup.get_text(separator=' ', strip=True)
            return self._clean_text(text)[:3000]
            
        except Exception as e:
            logger.debug(f"Error extracting from {url}: {e}")
            return None
    
    def _prepare_for_generator(self, articles: List[Dict]) -> List[Dict]:
        """Prépare les articles pour le générateur"""
        prepared = []
        
        for article in articles:
            prepared_article = {
                'id': hashlib.sha256(article['url'].encode()).hexdigest()[:12],
                'title': article['title'],
                'url': article['url'],
                'source': article['source'],
                'published': article['published'],
                'relevance_score': article.get('relevance_score', 0),
                'domain': article.get('domain', 'general'),
                
                'content': {
                    'summary': article.get('summary', ''),
                    'full_text': article.get('content', ''),
                    'extraction_quality': article.get('extraction_quality', 'unknown')
                },
                
                'metadata': {
                    'technologies': article.get('technologies_found', []),
                    'tags': article.get('tags', []),
                    'content_type': self._detect_content_type(article['title']),
                    'freshness': self._calculate_freshness(article['published'])
                },
                
                'scraped_at': article.get('scraped_at', datetime.now())
            }
            
            prepared.append(prepared_article)
        
        return prepared
    
    def _deduplicate(self, articles: List[Dict]) -> List[Dict]:
        """Déduplique les articles"""
        seen = set()
        unique = []
        
        for article in articles:
            # Créer une clé unique basée sur le titre normalisé
            title_key = re.sub(r'\W+', '', article['title'].lower())[:60]
            
            if title_key not in seen:
                seen.add(title_key)
                unique.append(article)
        
        return unique
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte"""
        if not text:
            return ""
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        # Supprimer les séparateurs répétitifs
        text = re.sub(r'[-=_*]{4,}', '', text)
        
        return text.strip()
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse une date avec fallback"""
        try:
            from dateutil import parser
            return parser.parse(date_str).replace(tzinfo=None)
        except:
            return datetime.now()
    
    def _detect_content_type(self, title: str) -> str:
        """Détecte le type de contenu"""
        title_lower = title.lower()
        
        patterns = {
            'tutorial': ['tutorial', 'guide', 'how to', 'getting started'],
            'news': ['releases', 'announces', 'launches', 'introduces', 'ships'],
            'comparison': ['vs', 'versus', 'comparison', 'comparing'],
            'tips': ['tips', 'tricks', 'best practices', 'mistakes'],
            'deep_dive': ['deep dive', 'under the hood', 'internals', 'explained']
        }
        
        for content_type, keywords in patterns.items():
            if any(kw in title_lower for kw in keywords):
                return content_type
        
        return 'article'
    
    def _calculate_freshness(self, published: datetime) -> str:
        """Calcule la fraîcheur"""
        if not isinstance(published, datetime):
            return 'unknown'
        
        age = datetime.now() - published
        hours = age.total_seconds() / 3600
        
        if hours < 6:
            return 'hot'
        elif hours < 24:
            return 'fresh'
        elif hours < 48:
            return 'recent'
        elif hours < 72:
            return 'relevant'
        else:
            return 'older'
    
    # Méthodes de compatibilité
    def get_articles_by_domain(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Organise les articles par domaine"""
        by_domain = {'frontend': [], 'backend': [], 'ai': [], 'general': []}
        
        for article in articles:
            domain = article.get('domain', 'general')
            if domain in by_domain:
                by_domain[domain].append(article)
        
        return by_domain
    
    def get_trending_technologies(self, articles: List[Dict]) -> Dict[str, List[str]]:
        """Extrait les technologies tendances"""
        tech_counts = {'frontend': {}, 'backend': {}, 'ai': {}}
        
        for article in articles:
            domain = article.get('domain', 'general')
            if domain in tech_counts:
                for tech in article.get('metadata', {}).get('technologies', []):
                    if tech not in tech_counts[domain]:
                        tech_counts[domain][tech] = 0
                    tech_counts[domain][tech] += 1
        
        # Top 5 par domaine
        trending = {}
        for domain, counts in tech_counts.items():
            sorted_techs = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
            trending[domain] = [tech for tech, _ in sorted_techs]
        
        return trending