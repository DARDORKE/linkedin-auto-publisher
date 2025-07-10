"""
Scraper amélioré avec focus sur la qualité et la diversité des articles
Intègre le nouveau système de scoring et de filtrage
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

# Import des nouveaux modules
from .sources_config import SPECIALIZED_SOURCES, QUALITY_CONFIG
from .quality_scorer import QualityScorer
from .diversity_manager import DiversityManager
from .content_filter import AdvancedContentFilter

class EnhancedFullstackScraper:
    """Scraper amélioré avec focus sur qualité, diversité et nouveautés"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
        self.cache_duration_hours = 12
        self.request_timeout = 10
        self.max_retries = 2
        
        # Nouveaux composants
        self.sources = SPECIALIZED_SOURCES
        self.quality_scorer = QualityScorer()
        self.diversity_manager = DiversityManager()
        self.content_filter = AdvancedContentFilter()
        
        # WebSocket session pour le suivi des progrès
        self.websocket_session_id = None
        self.websocket_service = None
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info("Enhanced scraper initialized with quality-focused approach")
    
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
    
    def scrape_all_sources(self, max_articles: int = 20, use_cache: bool = False) -> List[Dict]:
        """
        Scrape toutes les sources avec focus qualité et diversité
        """
        logger.info(f"Starting enhanced scraping for {max_articles} high-quality articles")
        
        # Nettoyer le cache expiré
        self.db.clear_expired_cache()
        
        # Collecter les articles par domaine
        domain_results = {}
        
        # Distribution par domaine pour garantir la diversité
        domain_targets = {
            'frontend': max_articles // 4,     # 25% pour frontend
            'backend': max_articles // 2,      # 50% pour backend (plus de variété)
            'ai': max_articles // 4,           # 25% pour AI
        }
        
        # S'assurer qu'on a au moins le minimum requis
        remaining = max_articles - sum(domain_targets.values())
        if remaining > 0:
            domain_targets['backend'] += remaining  # Donner le reste au backend
        
        # Scraper chaque domaine
        for domain, target_count in domain_targets.items():
            logger.info(f"Scraping {domain} domain (target: {target_count} articles)...")
            self._emit_progress({
                'type': 'domain_started',
                'domain': domain,
                'target_articles': target_count,
                'total_domains': len(domain_targets)
            })
            
            domain_result = self.scrape_domain(domain, target_count)
            domain_results[domain] = domain_result
            
            self._emit_progress({
                'type': 'domain_completed',
                'domain': domain,
                'articles_found': len(domain_result.get('articles', [])),
                'quality_stats': domain_result.get('stats', {})
            })
        
        # Combiner tous les articles
        all_articles = []
        total_stats = {
            'total_collected': 0,
            'after_scoring': 0,
            'after_filtering': 0,
            'final_selection': 0,
            'rejections': {}
        }
        
        for domain, result in domain_results.items():
            if result.get('status') == 'success':
                all_articles.extend(result.get('articles', []))
                
                # Agréger les stats
                domain_stats = result.get('stats', {})
                total_stats['total_collected'] += domain_stats.get('total_collected', 0)
                total_stats['after_scoring'] += domain_stats.get('after_scoring', 0)
                total_stats['after_filtering'] += domain_stats.get('after_filtering', 0)
                
                # Agréger les rejections
                for reason, count in domain_stats.get('rejections', {}).items():
                    total_stats['rejections'][reason] = total_stats['rejections'].get(reason, 0) + count
        
        # Tri final par score de qualité
        all_articles.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        # Limiter au nombre cible
        final_articles = all_articles[:max_articles]
        total_stats['final_selection'] = len(final_articles)
        
        # Préparer pour le générateur
        prepared_articles = self._prepare_for_generator(final_articles)
        
        # Log final
        logger.info(f"Enhanced scraping completed: {len(prepared_articles)} high-quality articles selected")
        logger.info(f"Final stats: {total_stats}")
        
        return prepared_articles
    
    def scrape_domain_sources(self, domain: str, max_articles: int = 20, use_cache: bool = False) -> List[Dict]:
        """Scrape spécifiquement un domaine (compatibilité avec l'ancienne API)"""
        result = self.scrape_domain(domain, max_articles)
        if result.get('status') == 'success':
            return self._prepare_for_generator(result.get('articles', []))
        return []
    
    def scrape_domain(self, domain: str, target_articles: int = 20) -> Dict:
        """Scrape un domaine avec le nouveau système qualité/diversité"""
        try:
            logger.info(f"Starting enhanced scraping for {domain}")
            
            # 1. Collecter les articles de toutes les sources spécialisées
            all_articles = self._collect_from_sources(domain)
            logger.info(f"Collected {len(all_articles)} raw articles for {domain}")
            
            if not all_articles:
                return {
                    'status': 'error',
                    'domain': domain,
                    'error': 'No articles collected from sources',
                    'articles': []
                }
            
            # 2. Enrichir avec le contenu complet en parallèle
            enriched_articles = self._enrich_articles_parallel(all_articles)
            logger.info(f"Enriched {len(enriched_articles)} articles with full content")
            
            # 3. Scorer chaque article pour la qualité
            scored_articles = self._score_articles(enriched_articles, domain)
            logger.info(f"Scored {len(scored_articles)} articles")
            
            # 4. Filtrer selon les critères de qualité
            filtered_articles, rejection_stats = self.content_filter.filter_articles(scored_articles)
            logger.info(f"Filtered to {len(filtered_articles)} articles. Rejections: {rejection_stats}")
            
            # 5. Assurer la diversité technologique
            diverse_articles = self.diversity_manager.ensure_diversity(
                filtered_articles, 
                domain, 
                target_articles
            )
            logger.info(f"Selected {len(diverse_articles)} diverse articles for {domain}")
            
            # 6. Trier par score de qualité final
            final_articles = sorted(
                diverse_articles, 
                key=lambda x: x.get('quality_score', 0), 
                reverse=True
            )
            
            return {
                'status': 'success',
                'domain': domain,
                'articles': final_articles,
                'stats': {
                    'total_collected': len(all_articles),
                    'after_enrichment': len(enriched_articles),
                    'after_scoring': len(scored_articles),
                    'after_filtering': len(filtered_articles),
                    'final_selection': len(final_articles),
                    'rejections': rejection_stats
                }
            }
            
        except Exception as e:
            logger.error(f"Error scraping {domain}: {e}")
            return {
                'status': 'error',
                'domain': domain,
                'error': str(e),
                'articles': []
            }
    
    def _collect_from_sources(self, domain: str) -> List[Dict]:
        """Collecte parallèle depuis toutes les sources du domaine"""
        domain_sources = self.sources.get(domain, {})
        all_articles = []
        
        if not domain_sources:
            logger.warning(f"No sources found for domain: {domain}")
            return []
        
        # Aplatir les sources par technologie
        flat_sources = []
        for tech, sources in domain_sources.items():
            for source in sources:
                source_with_tech = source.copy()
                source_with_tech['technology'] = tech
                flat_sources.append(source_with_tech)
        
        logger.info(f"Scraping {len(flat_sources)} sources for {domain}")
        
        self._emit_progress({
            'type': 'sources_started',
            'domain': domain,
            'sources_count': len(flat_sources)
        })
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {}
            
            for source in flat_sources:
                future = executor.submit(self._scrape_single_source, source)
                future_to_source[future] = source
            
            completed_sources = 0
            for future in as_completed(future_to_source, timeout=60):
                try:
                    source = future_to_source[future]
                    articles = future.result()
                    
                    if articles:
                        # Ajouter les métadonnées de source
                        for article in articles:
                            article['technology'] = source.get('technology', 'general')
                            article['source_config'] = source
                        all_articles.extend(articles)
                    
                    completed_sources += 1
                    
                    self._emit_progress({
                        'type': 'source_completed',
                        'domain': domain,
                        'source_name': source.get('url', 'Unknown'),
                        'technology': source.get('technology', 'general'),
                        'articles_found': len(articles) if articles else 0,
                        'completed_sources': completed_sources,
                        'total_sources': len(flat_sources)
                    })
                    
                except Exception as e:
                    source = future_to_source[future]
                    logger.error(f"Error scraping {source.get('url', 'Unknown')}: {e}")
                    completed_sources += 1
                    
                    self._emit_progress({
                        'type': 'source_error',
                        'domain': domain,
                        'source_name': source.get('url', 'Unknown'),
                        'error': str(e),
                        'completed_sources': completed_sources,
                        'total_sources': len(flat_sources)
                    })
        
        return all_articles
    
    def _scrape_single_source(self, source_config: Dict) -> List[Dict]:
        """Scrape une source individuelle avec retry"""
        url = source_config.get('url')
        if not url:
            return []
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    timeout=self.request_timeout
                )
                response.raise_for_status()
                
                feed = feedparser.parse(response.content)
                if not hasattr(feed, 'entries') or not feed.entries:
                    return []
                
                articles = []
                # Prendre plus d'articles par source pour avoir plus de choix
                for entry in feed.entries[:15]:
                    try:
                        # Valider l'entrée
                        if not entry.get('title') or not entry.get('link'):
                            continue
                        
                        article = {
                            'title': entry.get('title', '').strip(),
                            'url': entry.get('link', ''),
                            'source': source_config.get('url', 'Unknown'),
                            'source_name': source_config.get('type', 'Unknown'),
                            'published_parsed': entry.get('published_parsed'),
                            'summary': self._clean_text(
                                self._remove_html_tags(entry.get('summary', ''))
                            )[:800],
                            'content': '',  # Sera enrichi plus tard
                            'scraped_at': datetime.now(),
                            'tags': []
                        }
                        
                        # Extraire les tags si disponibles
                        if hasattr(entry, 'tags'):
                            article['tags'] = [
                                tag.term for tag in entry.tags 
                                if hasattr(tag, 'term')
                            ][:5]
                        
                        # Parser la date de publication
                        if entry.get('published_parsed'):
                            try:
                                article['published'] = datetime(*entry.published_parsed[:6])
                            except (TypeError, ValueError):
                                article['published'] = datetime.now()
                        else:
                            article['published'] = datetime.now()
                        
                        articles.append(article)
                        
                    except Exception as e:
                        logger.debug(f"Error parsing entry from {url}: {e}")
                        continue
                
                return articles
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to scrape {url} after {self.max_retries} attempts: {e}")
                    return []
                else:
                    logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                    time.sleep(1)  # Wait before retry
        
        return []
    
    def _enrich_articles_parallel(self, articles: List[Dict]) -> List[Dict]:
        """Enrichit les articles avec le contenu complet en parallèle"""
        if not articles:
            return []
        
        logger.info(f"Enriching {len(articles)} articles with full content")
        
        enriched = []
        
        # Traitement en parallèle pour l'extraction de contenu
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_article = {
                executor.submit(self._enrich_single_article, article): article 
                for article in articles
            }
            
            for future in as_completed(future_to_article, timeout=180):
                try:
                    enriched_article = future.result()
                    if enriched_article:
                        enriched.append(enriched_article)
                except Exception as e:
                    article = future_to_article[future]
                    logger.debug(f"Error enriching article {article.get('title', 'Unknown')}: {e}")
                    # Ajouter l'article sans enrichissement
                    article['content'] = article.get('summary', '')
                    article['extraction_quality'] = 'error'
                    enriched.append(article)
        
        return enriched
    
    def _enrich_single_article(self, article: Dict) -> Optional[Dict]:
        """Enrichit un article individuel"""
        try:
            # Extraire le contenu complet
            content = self._extract_full_content(article['url'])
            
            if content and len(content) > 200:
                article['content'] = content
                article['extraction_quality'] = 'full'
            else:
                # Fallback sur le summary
                article['content'] = article.get('summary', '')
                article['extraction_quality'] = 'summary_only'
            
            return article
            
        except Exception as e:
            logger.debug(f"Error enriching article {article.get('title', 'Unknown')}: {e}")
            article['content'] = article.get('summary', '')
            article['extraction_quality'] = 'error'
            return article
    
    def _extract_full_content(self, url: str) -> Optional[str]:
        """Extraction complète du contenu avec readability"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.request_timeout)
            response.raise_for_status()
            
            # Utiliser readability pour extraction du contenu principal
            doc = Document(response.content)
            content = doc.summary()
            
            # Nettoyer avec BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Supprimer tous les éléments inutiles
            for tag in soup.find_all([
                'script', 'style', 'nav', 'aside', 'footer', 'header', 
                'form', 'input', 'button', 'select', 'textarea',
                'iframe', 'embed', 'object', 'applet', 'ads', 'advertisement'
            ]):
                tag.decompose()
            
            # Supprimer les attributs inutiles
            for tag in soup.find_all(True):
                tag.attrs = {}
            
            # Extraire le texte proprement
            text = soup.get_text(separator=' ', strip=True)
            
            # Nettoyage avancé
            cleaned_text = self._advanced_text_cleaning(text)
            
            # Limiter la taille (15000 chars pour avoir assez de contenu)
            return cleaned_text[:15000] if cleaned_text else None
            
        except Exception as e:
            logger.debug(f"Error extracting content from {url}: {e}")
            return None
    
    def _advanced_text_cleaning(self, text: str) -> str:
        """Nettoyage avancé du texte extrait"""
        if not text:
            return ""
        
        # Supprimer les patterns de navigation et UI
        patterns_to_remove = [
            r'Skip to main content',
            r'Navigation|Menu|Search|Login|Sign up',
            r'Subscribe|Newsletter|Follow us',
            r'This website uses cookies',
            r'Privacy policy|Terms of service',
            r'Share on|Tweet|Facebook|LinkedIn',
            r'Advertisement|Sponsored|Promotion',
            r'[Aa]ds?\s*by',
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    def _score_articles(self, articles: List[Dict], domain: str) -> List[Dict]:
        """Score chaque article avec le nouveau système de qualité"""
        scored = []
        
        for article in articles:
            try:
                score, score_breakdown = self.quality_scorer.calculate_quality_score(
                    article, 
                    article.get('source_config', {})
                )
                
                article['quality_score'] = score
                article['score_breakdown'] = score_breakdown
                article['domain'] = domain
                
                scored.append(article)
                
            except Exception as e:
                logger.debug(f"Error scoring article {article.get('title', 'Unknown')}: {e}")
                # Donner un score par défaut
                article['quality_score'] = 0
                article['score_breakdown'] = {}
                article['domain'] = domain
                scored.append(article)
        
        return scored
    
    def _prepare_for_generator(self, articles: List[Dict]) -> List[Dict]:
        """Prépare les articles pour le générateur (compatibilité)"""
        prepared = []
        
        for article in articles:
            # Nettoyer le summary
            clean_summary = self._clean_text(self._remove_html_tags(article.get('summary', '')))
            
            prepared_article = {
                'id': hashlib.sha256(article['url'].encode()).hexdigest()[:12],
                'title': article['title'],
                'url': article['url'],
                'source': article.get('source_name', article.get('source', 'Unknown')),
                'published': article.get('published', datetime.now()),
                'relevance_score': article.get('quality_score', 0),  # Compatibilité
                'domain': article.get('domain', 'general'),
                
                # Champs requis par le frontend
                'summary': clean_summary,
                'content': article.get('content', ''),
                'domains': [article.get('domain', 'general')],
                
                # Métadonnées enrichies
                'content_data': {
                    'summary': clean_summary,
                    'full_text': article.get('content', ''),
                    'extraction_quality': article.get('extraction_quality', 'unknown')
                },
                
                'metadata': {
                    'technologies': article.get('detected_technologies', []),
                    'tags': article.get('tags', []),
                    'quality_score': article.get('quality_score', 0),
                    'score_breakdown': article.get('score_breakdown', {}),
                    'technology': article.get('technology', 'general'),
                    'freshness': self._calculate_freshness(article.get('published', datetime.now()))
                },
                
                'scraped_at': article.get('scraped_at', datetime.now())
            }
            
            prepared.append(prepared_article)
        
        return prepared
    
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
    
    def _calculate_freshness(self, published: datetime) -> str:
        """Calcule la fraîcheur de l'article"""
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
    
    # Méthodes de compatibilité avec l'ancien scraper
    def _scrape_domain(self, domain: str, max_articles: int, use_cache: bool) -> List[Dict]:
        """Méthode de compatibilité"""
        result = self.scrape_domain(domain, max_articles)
        return result.get('articles', []) if result.get('status') == 'success' else []