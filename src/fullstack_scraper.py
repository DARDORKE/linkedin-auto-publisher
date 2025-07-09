"""
Scraper optimisé pour récupérer des articles tech de qualité
Version simplifiée et performante
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from loguru import logger
import time
from typing import List, Dict, Optional, Set, Tuple, Any
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
        
        # WebSocket session pour le suivi des progrès
        self.websocket_session_id = None
        self.websocket_service = None
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Sources de qualité par domaine
        self._init_quality_sources()
        
        # Mots-clés pour la pertinence
        self.domain_keywords = {
            'frontend': ['react', 'vue', 'angular', 'svelte', 'css', 'javascript', 'typescript', 
                        'nextjs', 'nuxtjs', 'tailwind', 'webpack', 'vite'],
            'backend': ['nodejs', 'python', 'java', 'go', 'golang', 'rust', 'php', 'laravel', 'symfony', 'api', 'database', 'docker', 
                       'kubernetes', 'microservices', 'serverless', 'redis', 'postgresql', 'mysql', 'composer'],
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
                {"name": "Vue.js Blog", "url": "https://blog.vuejs.org/feed.rss", "weight": 9},
                {"name": "Angular Blog", "url": "https://blog.angular.io/feed", "weight": 9},
                {"name": "Frontend Focus", "url": "https://frontendfoc.us/rss", "weight": 8},
                {"name": "A List Apart", "url": "https://alistapart.com/main/feed/", "weight": 9},
            ],
            'backend': [
                # Sources PHP (priorités)
                {"name": "PHP.net News", "url": "https://www.php.net/news.rss", "weight": 10},
                {"name": "Laravel News", "url": "https://laravel-news.com/feed", "weight": 9},
                # Sources Golang (priorités)
                {"name": "Go Dev Blog", "url": "https://go.dev/blog/feed.atom", "weight": 10},
                {"name": "Golang Weekly", "url": "https://golangweekly.com/rss/", "weight": 9},
                # Sources générales backend
                {"name": "Docker Blog", "url": "https://www.docker.com/blog/feed/", "weight": 9},
                {"name": "Python Official Blog", "url": "https://blog.python.org/feeds/posts/default", "weight": 10},
                # Sources supplémentaires (si limite augmentée)
                {"name": "Symfony Blog", "url": "https://symfony.com/blog.rss", "weight": 9},
                {"name": "Node.js Medium", "url": "https://medium.com/feed/the-node-js-collection", "weight": 9},
                {"name": "Rust Blog", "url": "https://blog.rust-lang.org/feed.xml", "weight": 10},
                {"name": "Django News", "url": "https://django-news.com/issues.rss", "weight": 9},
                {"name": "AWS News", "url": "https://aws.amazon.com/about-aws/whats-new/recent/feed/", "weight": 8},
                {"name": "Kubernetes Blog", "url": "https://kubernetes.io/feed.xml", "weight": 9},
                {"name": "Node Weekly", "url": "https://nodeweekly.com/rss/", "weight": 9},
                {"name": "PHP The Right Way", "url": "https://www.phptherightway.com/feed.xml", "weight": 8},
                {"name": "SitePoint PHP", "url": "https://www.sitepoint.com/php/feed/", "weight": 8},
                {"name": "Go Time Podcast", "url": "https://changelog.com/gotime/feed", "weight": 8},
                {"name": "Gopher Academy", "url": "https://blog.gopheracademy.com/index.xml", "weight": 8},
                {"name": "Dave Cheney", "url": "https://dave.cheney.net/feed", "weight": 8},
            ],
            'ai': [
                {"name": "MIT Technology Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/", "weight": 10},
                {"name": "Berkeley AI Research", "url": "https://bair.berkeley.edu/blog/feed.xml", "weight": 10},
                {"name": "The Gradient", "url": "https://thegradient.pub/rss/", "weight": 10},
                {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml", "weight": 9},
                {"name": "Anthropic News", "url": "https://rsshub.app/anthropic/news", "weight": 10},
                {"name": "Towards Data Science", "url": "https://towardsdatascience.com/feed", "weight": 7},
                {"name": "Machine Learning Mastery", "url": "https://machinelearningmastery.com/feed/", "weight": 8},
                {"name": "The Batch", "url": "https://www.deeplearning.ai/the-batch/rss/", "weight": 9},
                {"name": "Distill", "url": "https://distill.pub/rss.xml", "weight": 8},
            ],
            'general': [
                {"name": "GitHub Blog", "url": "https://github.blog/feed/", "weight": 9},
                {"name": "Stack Overflow Blog", "url": "https://stackoverflow.blog/feed/", "weight": 8},
                {"name": "InfoQ", "url": "https://www.infoq.com/feed/", "weight": 9},
                {"name": "The New Stack", "url": "https://thenewstack.io/feed/", "weight": 8},
                {"name": "Dev.to - Top", "url": "https://dev.to/feed", "weight": 7},
            ]
        }
    
    def set_websocket_session(self, session_id: str, websocket_service) -> None:
        """Configure la session WebSocket pour le suivi des progrès"""
        self.websocket_session_id = session_id
        self.websocket_service = websocket_service
    
    def _emit_progress(self, progress_data: Dict[str, Any]) -> None:
        """Émet un événement de progression via WebSocket"""
        if self.websocket_service and self.websocket_session_id:
            try:
                self.websocket_service.update_scraping_progress(self.websocket_session_id, progress_data)
            except Exception as e:
                logger.debug(f"Error emitting progress: {e}")
    
    def scrape_all_sources(self, max_articles: int = 40, use_cache: bool = True) -> List[Dict]:
        """
        Scrape toutes les sources et retourne les meilleurs articles
        Optimisé pour la performance et la qualité
        """
        # Nettoyer le cache expiré
        self.db.clear_expired_cache()
        
        # Collecter les articles par domaine
        domain_articles = {}
        
        # Articles par domaine souhaités - augmenté pour couvrir toutes les technologies
        articles_per_domain = {
            'frontend': max(15, max_articles // 3),
            'backend': max(30, max_articles // 2),  # Augmenté pour PHP, Golang, Python, Node.js, etc.
            'ai': max(15, max_articles // 3),
            'general': max(10, max_articles // 6)
        }
        
        # Scraper chaque domaine
        for domain, count in articles_per_domain.items():
            logger.info(f"Scraping {domain} domain (target: {count} articles)...")
            self._emit_progress({
                'type': 'domain_started',
                'domain': domain,
                'target_articles': count,
                'total_domains': len(articles_per_domain)
            })
            domain_articles[domain] = self._scrape_domain(domain, count, use_cache)
            self._emit_progress({
                'type': 'domain_completed',
                'domain': domain,
                'articles_found': len(domain_articles[domain])
            })
        
        # Combiner tous les articles
        all_articles = []
        for articles in domain_articles.values():
            all_articles.extend(articles)
        
        # Trier par score global et limiter
        all_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Préparer pour le générateur
        final_articles = self._prepare_for_generator(all_articles[:max_articles])
        
        return final_articles
    
    def scrape_domain_sources(self, domain: str, max_articles: int = 60, use_cache: bool = True) -> List[Dict]:
        """Scrape spécifiquement un domaine"""
        if domain not in self.sources:
            logger.error(f"Domain {domain} not supported")
            return []
        
        articles = self._scrape_domain(domain, max_articles, use_cache)
        return self._prepare_for_generator(articles)
    
    def _scrape_domain(self, domain: str, max_articles: int, use_cache: bool) -> List[Dict]:
        """Scrape interne pour un domaine"""
        logger.info(f"Scraping {domain} domain - cache disabled, always fetching fresh articles")
        
        # Scraper les sources
        all_articles = []
        sources = self.sources.get(domain, [])
        
        # Utiliser toutes les sources disponibles
        sources_to_scrape = sources
        
        self._emit_progress({
            'type': 'sources_started',
            'domain': domain,
            'sources_count': len(sources_to_scrape)
        })
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_source = {
                executor.submit(self._scrape_source, source): source 
                for source in sources_to_scrape
            }
            
            completed_sources = 0
            for future in as_completed(future_to_source, timeout=20):
                try:
                    source = future_to_source[future]
                    articles = future.result()
                    if articles:
                        all_articles.extend(articles)
                    completed_sources += 1
                    
                    self._emit_progress({
                        'type': 'source_completed',
                        'domain': domain,
                        'source_name': source['name'],
                        'articles_found': len(articles) if articles else 0,
                        'completed_sources': completed_sources,
                        'total_sources': len(sources_to_scrape)
                    })
                    
                except Exception as e:
                    logger.error(f"Error scraping source: {e}")
                    completed_sources += 1
                    self._emit_progress({
                        'type': 'source_error',
                        'domain': domain,
                        'source_name': future_to_source[future]['name'],
                        'error': str(e),
                        'completed_sources': completed_sources,
                        'total_sources': len(sources_to_scrape)
                    })
        
        # Traiter et scorer
        self._emit_progress({
            'type': 'processing_started',
            'domain': domain,
            'total_articles': len(all_articles)
        })
        
        processed = self._process_and_score(all_articles, domain)
        
        self._emit_progress({
            'type': 'processing_completed',
            'domain': domain,
            'processed_articles': len(processed),
            'final_articles': min(len(processed), max_articles)
        })
        
        # Cache désactivé - pas de sauvegarde
        logger.info(f"Cache disabled - not saving {len(processed)} articles")
        
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
            for entry in feed.entries[:12]:  # Max 12 articles par source pour plus de diversité
                try:
                    article = {
                        'title': entry.get('title', '').strip(),
                        'url': entry.get('link', ''),
                        'source': source['name'],
                        'source_weight': source['weight'],
                        'published': self._parse_date(entry.get('published', entry.get('updated', ''))),
                        'summary': self._clean_text(self._remove_html_tags(entry.get('summary', '')))[:600],
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
                    
                    # Si pas de contenu et summary court, marquer pour extraction prioritaire
                    if len(article['content']) < 200 and len(article['summary']) < 150:
                        article['needs_extraction'] = True
                    
                    # Marquer spécifiquement les sources connues pour avoir peu de contenu
                    if source['name'] in ['Hugging Face Blog', 'Google AI Blog', 'Web.dev', 'React Blog', 'Go Dev Blog']:
                        article['needs_extraction'] = True
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.debug(f"Error parsing entry: {e}")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {e}")
            return []
    
    def _process_and_score(self, articles: List[Dict], domain: str) -> List[Dict]:
        """Traite et score les articles avec équilibrage par technologie"""
        # Dédupliquer
        unique_articles = self._deduplicate(articles)
        
        # Scorer
        keywords = self.domain_keywords.get(domain, [])
        for article in unique_articles:
            score = 0
            
            # Score de source
            score += article.get('source_weight', 5) * 3
            
            # Score de fraîcheur (renforcé pour prioriser les articles récents)
            age_hours = (datetime.now() - article['published']).total_seconds() / 3600
            if age_hours < 6:
                score += 50  # Très récent
            elif age_hours < 12:
                score += 40  # Récent
            elif age_hours < 24:
                score += 35  # Jour 1
            elif age_hours < 48:
                score += 30  # Jour 2
            elif age_hours < 72:
                score += 25  # Jour 3
            else:
                score += 5   # Plus ancien
            
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
            
            # Détecter la technologie principale
            article['tech_category'] = self._detect_tech_category(article, domain)
        
        # Équilibrer par technologie au lieu de trier seulement par score
        balanced_articles = self._balance_by_technology(unique_articles, domain)
        
        # Enrichir tous les articles avec le contenu complet
        self._enrich_top_articles(balanced_articles)
        
        return balanced_articles
    
    def _detect_tech_category(self, article: Dict, domain: str) -> str:
        """Détecte la catégorie technologique d'un article"""
        text = (article.get('title', '') + ' ' + article.get('summary', '') + ' ' + article.get('source', '')).lower()
        
        if domain == 'backend':
            # Détecter les technologies backend
            if any(kw in text for kw in ['php', 'laravel', 'symfony', 'composer']):
                return 'php'
            elif any(kw in text for kw in ['golang', 'go ', 'gopher']):
                return 'golang'
            elif any(kw in text for kw in ['python', 'django', 'flask', 'fastapi']):
                return 'python'
            elif any(kw in text for kw in ['node.js', 'nodejs', 'javascript', 'express']):
                return 'nodejs'
            elif any(kw in text for kw in ['rust', 'cargo']):
                return 'rust'
            elif any(kw in text for kw in ['java', 'spring', 'maven']):
                return 'java'
            elif any(kw in text for kw in ['docker', 'kubernetes', 'container']):
                return 'devops'
            elif any(kw in text for kw in ['database', 'postgresql', 'mysql', 'redis']):
                return 'database'
            else:
                return 'general'
        
        elif domain == 'frontend':
            if any(kw in text for kw in ['react', 'jsx', 'nextjs']):
                return 'react'
            elif any(kw in text for kw in ['vue', 'nuxt']):
                return 'vue'
            elif any(kw in text for kw in ['angular', 'typescript']):
                return 'angular'
            elif any(kw in text for kw in ['css', 'sass', 'tailwind']):
                return 'css'
            else:
                return 'general'
        
        return 'general'
    
    def _filter_fresh_articles(self, articles: List[Dict], max_age_days: int = 3) -> List[Dict]:
        """Filtre les articles récents (moins de X jours)"""
        fresh_articles = []
        max_age_seconds = max_age_days * 24 * 3600
        current_time = datetime.now()
        
        for article in articles:
            published = article.get('published')
            if not published:
                continue
                
            # Convertir en datetime si c'est une string
            if isinstance(published, str):
                try:
                    from dateutil import parser
                    published = parser.parse(published).replace(tzinfo=None)
                except Exception as e:
                    logger.debug(f"Could not parse date '{published}': {e}")
                    continue
            elif not isinstance(published, datetime):
                continue
                
            age_seconds = (current_time - published).total_seconds()
            if age_seconds <= max_age_seconds:
                fresh_articles.append(article)
                # Log pour debug
                age_hours = age_seconds / 3600
                logger.debug(f"Fresh article: {article.get('title', 'NO TITLE')[:50]}... (age: {age_hours:.1f}h)")
        
        return fresh_articles
    
    def _get_freshness_score(self, article: Dict) -> float:
        """Calcule un score de fraîcheur pour le tri"""
        published = article.get('published')
        if not published:
            return 0.0
            
        # Convertir en datetime si nécessaire
        if isinstance(published, str):
            try:
                from dateutil import parser
                published = parser.parse(published).replace(tzinfo=None)
            except:
                return 0.0
        elif not isinstance(published, datetime):
            return 0.0
        
        # Calculer l'âge en heures
        age_hours = (datetime.now() - published).total_seconds() / 3600
        
        # Score inversé : plus c'est récent, plus le score est élevé
        if age_hours < 6:
            return 100.0
        elif age_hours < 12:
            return 90.0
        elif age_hours < 24:
            return 80.0
        elif age_hours < 48:
            return 70.0
        elif age_hours < 72:
            return 60.0
        elif age_hours < 168:  # 7 jours
            return 40.0
        else:
            return 20.0
    
    def _balance_by_technology(self, articles: List[Dict], domain: str) -> List[Dict]:
        """Équilibre la sélection d'articles par technologie pour 20 articles finaux"""
        if domain != 'backend':
            # Pour les autres domaines, garder le tri par score
            return sorted(articles, key=lambda x: x['relevance_score'], reverse=True)
        
        # PRIORITÉ 1: Équilibrage technologique d'abord
        # Grouper par technologie (tous les articles)
        tech_groups = {}
        for article in articles:
            tech = article.get('tech_category', 'general')
            if tech not in tech_groups:
                tech_groups[tech] = []
            tech_groups[tech].append(article)
        
        # Trier chaque groupe par score DE FRAÎCHEUR d'abord, puis par pertinence
        for tech in tech_groups:
            tech_groups[tech].sort(key=lambda x: (
                self._get_freshness_score(x),  # Score de fraîcheur en premier
                x['relevance_score']           # Score de pertinence en second
            ), reverse=True)
        
        # Sélection équilibrée pour 20 articles finaux
        balanced_articles = []
        target_final_count = 20
        
        # Prioriser les technologies principales
        priority_techs = ['php', 'golang', 'python', 'nodejs', 'rust', 'java']
        
        # Calculer la distribution équitable pour 20 articles
        available_techs = [tech for tech in priority_techs if tech in tech_groups and len(tech_groups[tech]) > 0]
        
        if len(available_techs) == 0:
            # Fallback si aucune tech prioritaire
            fallback_articles = sorted(articles, key=lambda x: (
                self._get_freshness_score(x),
                x['relevance_score']
            ), reverse=True)[:target_final_count]
            logger.warning(f"Using fallback selection with {len(fallback_articles)} articles")
            return fallback_articles
        
        # Distribuer équitablement les 20 articles
        base_per_tech = target_final_count // len(available_techs)  # Base par technologie
        extra_slots = target_final_count % len(available_techs)     # Slots supplémentaires
        
        tech_allocations = {}
        for i, tech in enumerate(available_techs):
            allocation = base_per_tech
            if i < extra_slots:  # Distribuer les slots supplémentaires
                allocation += 1
            tech_allocations[tech] = min(allocation, len(tech_groups[tech]))
        
        # Sélectionner les articles selon les allocations (les plus frais de chaque tech)
        for tech in available_techs:
            if tech in tech_groups:
                selected_count = tech_allocations[tech]
                selected_articles = tech_groups[tech][:selected_count]
                balanced_articles.extend(selected_articles)
                
                # Log avec info fraîcheur
                if selected_articles:
                    avg_freshness = sum(self._get_freshness_score(a) for a in selected_articles) / len(selected_articles)
                    logger.info(f"Selected {selected_count} articles for {tech} (avg freshness: {avg_freshness:.1f})")
        
        # Si on n'a pas assez d'articles, compléter avec devops/database/general
        if len(balanced_articles) < target_final_count:
            remaining_slots = target_final_count - len(balanced_articles)
            other_articles = []
            
            for tech in ['devops', 'database', 'general']:
                if tech in tech_groups:
                    other_articles.extend(tech_groups[tech])
            
            # Trier par fraîcheur puis pertinence
            other_articles.sort(key=lambda x: (
                self._get_freshness_score(x),
                x['relevance_score']
            ), reverse=True)
            balanced_articles.extend(other_articles[:remaining_slots])
        
        # S'assurer qu'on a exactement 20 articles
        final_selection = balanced_articles[:target_final_count]
        
        # Log final avec stats de fraîcheur
        if final_selection:
            avg_final_freshness = sum(self._get_freshness_score(a) for a in final_selection) / len(final_selection)
            fresh_count = sum(1 for a in final_selection if self._get_freshness_score(a) >= 60.0)  # < 72h
            logger.info(f"Balanced selection: {len(final_selection)} articles (avg freshness: {avg_final_freshness:.1f}, {fresh_count} recent)")
        
        return final_selection
    
    def _enrich_top_articles(self, articles: List[Dict]):
        """Enrichit tous les articles avec du contenu complet"""
        logger.info(f"Enriching {len(articles)} articles with full content extraction")
        
        # Traiter tous les articles pour extraire le contenu complet
        for i, article in enumerate(articles):
            try:
                # Toujours extraire le contenu complet de l'article
                content = self._extract_full_content(article['url'])
                if content:
                    article['content'] = content
                    article['extraction_quality'] = 'full'
                else:
                    # Fallback sur le summary si l'extraction échoue
                    article['content'] = article.get('summary', '')
                    article['extraction_quality'] = 'summary_only'
                
                # Détecter les technologies mentionnées
                full_text = (article['title'] + ' ' + article['content']).lower()
                found_techs = []
                for domain_kw in self.domain_keywords.values():
                    for kw in domain_kw:
                        if kw in full_text:
                            found_techs.append(kw)
                
                article['technologies_found'] = list(set(found_techs))[:10]
                
                # Log du progrès
                if (i + 1) % 5 == 0:
                    logger.info(f"Processed {i + 1}/{len(articles)} articles")
                
            except Exception as e:
                logger.debug(f"Error enriching article {article.get('title', 'Unknown')}: {e}")
                article['extraction_quality'] = 'error'
                article['content'] = article.get('summary', '')
    
    
    def _extract_full_content(self, url: str) -> Optional[str]:
        """Extraction complète du contenu d'un article avec nettoyage avancé"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Utiliser readability pour extraction du contenu principal
            doc = Document(response.content)
            content = doc.summary()
            
            # Nettoyer avec BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Supprimer tous les éléments inutiles
            for tag in soup.find_all(['script', 'style', 'nav', 'aside', 'footer', 'header', 
                                     'form', 'input', 'button', 'select', 'textarea',
                                     'iframe', 'embed', 'object', 'applet']):
                tag.decompose()
            
            # Supprimer les commentaires HTML
            for comment in soup.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith('<!--')):
                comment.extract()
            
            # Supprimer les attributs inutiles mais garder la structure
            for tag in soup.find_all(True):
                # Garder seulement les attributs essentiels
                tag.attrs = {}
            
            # Extraire le texte avec séparateurs appropriés
            text = soup.get_text(separator=' ', strip=True)
            
            # Nettoyage avancé du texte
            cleaned_text = self._advanced_text_cleaning(text)
            
            # Limiter la taille mais permettre beaucoup plus de contenu pour la lecture complète
            return cleaned_text[:15000]  # Augmenté pour permettre la lecture complète d'articles
            
        except Exception as e:
            logger.debug(f"Error extracting full content from {url}: {e}")
            return None
    
    def _advanced_text_cleaning(self, text: str) -> str:
        """Nettoyage avancé du texte extrait"""
        if not text:
            return ""
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les retours à la ligne multiples
        text = re.sub(r'\n+', '\n', text)
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Supprimer les caractères Unicode problématiques
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
        
        # Supprimer les patterns de navigation courrants
        text = re.sub(r'(Skip to main content|Skip to content|Navigation|Menu|Search|Login|Sign up|Subscribe|Newsletter)', '', text, flags=re.IGNORECASE)
        
        # Supprimer les patterns de cookies et tracking
        text = re.sub(r'(This website uses cookies|By continuing to use|Privacy policy|Terms of service|GDPR)', '', text, flags=re.IGNORECASE)
        
        # Supprimer les patterns de partage social
        text = re.sub(r'(Share on|Follow us|Like us|Tweet|Facebook|Twitter|LinkedIn|Reddit)', '', text, flags=re.IGNORECASE)
        
        # Supprimer les patterns publicitaires
        text = re.sub(r'(Advertisement|Sponsored|Promotion|Ad|Ads)', '', text, flags=re.IGNORECASE)
        
        # Nettoyer les espaces en début et fin
        text = text.strip()
        
        return text
    
    def _prepare_for_generator(self, articles: List[Dict]) -> List[Dict]:
        """Prépare les articles pour le générateur"""
        prepared = []
        
        for article in articles:
            # Nettoyer le summary
            clean_summary = self._clean_text(self._remove_html_tags(article.get('summary', '')))
            
            prepared_article = {
                'id': hashlib.sha256(article['url'].encode()).hexdigest()[:12],
                'title': article['title'],
                'url': article['url'],
                'source': article['source'],
                'published': article['published'],
                'relevance_score': article.get('relevance_score', 0),
                'domain': article.get('domain', 'general'),
                
                # Champs compatibles avec le frontend
                'summary': clean_summary,
                'content': article.get('content', ''),
                'domains': [article.get('domain', 'general')],  # Compatible avec l'interface
                
                # Métadonnées enrichies
                'content_data': {
                    'summary': clean_summary,
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
    
    def _remove_html_tags(self, text: str) -> str:
        """Supprime les balises HTML"""
        if not text:
            return ""
        
        # Supprimer les balises HTML
        text = re.sub(r'<[^>]+>', '', text)
        # Décoder les entités HTML courantes
        text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
        
        return text

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
    
