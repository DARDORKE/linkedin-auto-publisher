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
        self.db.clear_expired_enriched_cache()
        
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
        
        with ThreadPoolExecutor(max_workers=10) as executor:
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
                # Ajuster selon le poids de la source (sources prioritaires = plus d'articles)
                source_weight = source_config.get('weight', 7)
                max_articles_from_source = 5 if source_weight < 8 else 10 if source_weight < 9 else 15
                
                for entry in feed.entries[:max_articles_from_source]:
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
                        
                        # Parser la date de publication avec fallback sur différents champs
                        parsed_date = None
                        
                        # Essayer dans l'ordre de préférence : published_parsed, updated_parsed, puis les champs string
                        date_fields = [
                            ('published_parsed', 'parsed'),
                            ('updated_parsed', 'parsed'), 
                            ('published', 'string'),
                            ('updated', 'string'),
                            ('date', 'string')
                        ]
                        
                        for field_name, field_type in date_fields:
                            if entry.get(field_name):
                                try:
                                    if field_type == 'parsed' and entry.get(field_name):
                                        parsed_date = datetime(*entry[field_name][:6])
                                        break
                                    elif field_type == 'string' and entry.get(field_name):
                                        from dateutil import parser as date_parser
                                        parsed_date = date_parser.parse(entry[field_name])
                                        break
                                except (TypeError, ValueError, Exception) as e:
                                    logger.debug(f"Failed to parse {field_name} for {entry.get('title', 'unknown')[:30]}: {e}")
                                    continue
                        
                        if parsed_date:
                            article['published'] = parsed_date
                        else:
                            # Tentative d'extraction de date depuis l'URL ou le contenu
                            extracted_date = self._extract_date_from_url_or_content(entry)
                            if extracted_date:
                                article['published'] = extracted_date
                                logger.debug(f"Extracted date from URL/content for {entry.get('title', 'unknown')[:50]}: {extracted_date}")
                            else:
                                logger.warning(f"No valid date found for {entry.get('title', 'unknown')[:50]} - skipping article")
                                continue  # Ignorer l'article si aucune date valide n'est trouvée
                        
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
    
    def _extract_date_from_url_or_content(self, entry: Dict) -> Optional[datetime]:
        """Extrait une date à partir de l'URL ou du contenu de l'entrée RSS"""
        import re
        from dateutil import parser as date_parser
        
        # Patterns de dates couramment trouvés dans les URLs
        date_patterns = [
            r'/(\d{4})/(\d{1,2})/(\d{1,2})/',  # /2025/07/10/
            r'/(\d{4})-(\d{1,2})-(\d{1,2})/',  # /2025-07-10/
            r'(\d{4})(\d{2})(\d{2})',          # 20250710
            r'(\d{4})/(\d{1,2})/',             # /2025/07/
        ]
        
        # Chercher dans l'URL
        url = entry.get('link', '') or entry.get('id', '')
        if url:
            for pattern in date_patterns:
                match = re.search(pattern, url)
                if match:
                    try:
                        if len(match.groups()) == 3:
                            year, month, day = match.groups()
                            date = datetime(int(year), int(month), int(day))
                        elif len(match.groups()) == 2:
                            year, month = match.groups()
                            date = datetime(int(year), int(month), 1)  # Premier du mois
                        else:
                            continue
                            
                        # Vérifier que la date est raisonnable (pas dans le futur, pas trop ancienne)
                        now = datetime.now()
                        if date <= now and date >= datetime(2020, 1, 1):
                            return date
                    except (ValueError, TypeError):
                        continue
        
        # Chercher dans le titre
        title = entry.get('title', '')
        if title:
            # Pattern pour dates dans le titre
            title_patterns = [
                r'(\d{1,2})/(\d{1,2})/(\d{4})',    # 07/10/2025
                r'(\d{4})-(\d{1,2})-(\d{1,2})',    # 2025-07-10
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})',
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    try:
                        date_str = match.group(0)
                        date = date_parser.parse(date_str)
                        
                        # Vérifier que la date est raisonnable
                        now = datetime.now()
                        if date <= now and date >= datetime(2020, 1, 1):
                            return date
                    except (ValueError, TypeError):
                        continue
        
        return None
    
    def _enrich_articles_parallel(self, articles: List[Dict]) -> List[Dict]:
        """Enrichit les articles avec le contenu complet en parallèle"""
        if not articles:
            return []
        
        # Filtrer les articles trop anciens avant l'enrichissement
        max_age_days = 30  # Ne pas enrichir les articles de plus de 30 jours
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        recent_articles = []
        for article in articles:
            published_date = article.get('published')
            if published_date and isinstance(published_date, datetime):
                if published_date >= cutoff_date:
                    recent_articles.append(article)
                else:
                    # Article trop ancien, on garde juste le summary
                    article['content'] = article.get('summary', '')
                    article['extraction_quality'] = 'too_old'
                    article['skipped_enrichment'] = True
                    recent_articles.append(article)
            else:
                # Pas de date, on enrichit par précaution
                recent_articles.append(article)
        
        # Pré-charger le cache pour éviter les accès concurrents
        cache_keys = [article['url'] for article in recent_articles if not article.get('skipped_enrichment')]
        cached_contents = {}
        
        try:
            # Charger tout le cache en une fois
            for url in cache_keys:
                cached = self.db.get_enriched_content_from_cache(url)
                if cached:
                    cached_contents[url] = cached
        except Exception as e:
            logger.debug(f"Error pre-loading cache: {e}")
        
        # Séparer les articles à enrichir de ceux déjà traités
        to_enrich = []
        already_processed = []
        
        for article in recent_articles:
            if article.get('skipped_enrichment'):
                already_processed.append(article)
            elif article['url'] in cached_contents:
                # Article déjà en cache
                cached = cached_contents[article['url']]
                article['content'] = cached['content']
                article['extraction_quality'] = cached['extraction_quality']
                article['from_cache'] = True
                already_processed.append(article)
            else:
                # Article à enrichir
                to_enrich.append(article)
        
        logger.info(f"Enriching {len(to_enrich)} articles (using cache for {len(already_processed) - len([a for a in already_processed if a.get('skipped_enrichment')])}, skipping {len([a for a in already_processed if a.get('skipped_enrichment')])} old articles)")
        
        enriched = already_processed.copy()
        
        # Traitement en parallèle pour l'extraction de contenu (seulement les non-cachés)
        if to_enrich:
            with ThreadPoolExecutor(max_workers=8) as executor:
                future_to_article = {
                    executor.submit(self._enrich_single_article, article): article 
                    for article in to_enrich
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
        """Enrichit un article individuel avec cache"""
        try:
            # Créer une nouvelle session pour chaque thread
            from src.database import DatabaseManager
            thread_db = DatabaseManager()
            
            # Vérifier le cache en premier
            cached_content = thread_db.get_enriched_content_from_cache(article['url'])
            
            if cached_content:
                article['content'] = cached_content['content']
                article['extraction_quality'] = cached_content['extraction_quality']
                article['from_cache'] = True
                logger.debug(f"Content retrieved from cache for: {article['title'][:50]}")
                thread_db.close()
                return article
            
            # Extraire le contenu complet si pas dans le cache
            content = self._extract_full_content(article['url'])
            
            if content and len(content) > 200:
                article['content'] = content
                article['extraction_quality'] = 'full'
                # Sauvegarder dans le cache avec une nouvelle session
                try:
                    thread_db.save_enriched_content_to_cache(
                        url=article['url'],
                        content=content,
                        extraction_quality='full',
                        cache_hours=48  # Cache pour 48 heures
                    )
                except Exception as cache_error:
                    logger.debug(f"Cache save error for {article['url']}: {cache_error}")
            else:
                # Fallback sur le summary
                article['content'] = article.get('summary', '')
                article['extraction_quality'] = 'summary_only'
                # Sauvegarder aussi les échecs pour éviter de réessayer
                try:
                    thread_db.save_enriched_content_to_cache(
                        url=article['url'],
                        content=article['content'],
                        extraction_quality='summary_only',
                        cache_hours=24  # Cache plus court pour les échecs
                    )
                except Exception as cache_error:
                    logger.debug(f"Cache save error for {article['url']}: {cache_error}")
            
            article['from_cache'] = False
            thread_db.close()
            return article
            
        except Exception as e:
            logger.debug(f"Error enriching article {article.get('title', 'Unknown')}: {e}")
            article['content'] = article.get('summary', '')
            article['extraction_quality'] = 'error'
            article['from_cache'] = False
            return article
    
    def _get_optimized_headers(self, url: str) -> Dict[str, str]:
        """Retourne des headers optimisés selon le site"""
        base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Headers spécifiques pour certains sites
        if 'microsoft.com' in url or 'azure.microsoft.com' in url:
            base_headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            base_headers['Cache-Control'] = 'no-cache'
        elif 'github.com' in url:
            base_headers['Accept'] = 'application/vnd.github.v3+json'
        
        return base_headers
    
    def _extract_full_content(self, url: str) -> Optional[str]:
        """Extraction complète du contenu avec readability"""
        try:
            # Augmenter le timeout pour les sites lents comme Azure
            timeout = 30 if 'azure.microsoft.com' in url or 'microsoft.com' in url else self.request_timeout
            headers = self._get_optimized_headers(url)
            response = requests.get(url, headers=headers, timeout=timeout)
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
        
        # Supprimer toutes les URLs
        # Pattern pour matcher différents types d'URLs
        url_patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',  # URLs HTTP/HTTPS
            r'www\.[^\s<>"{}|\\^`\[\]]+',      # URLs commençant par www.
            r'[a-zA-Z0-9][a-zA-Z0-9-]*\.(?:com|org|net|edu|gov|mil|int|co|io|dev|app|ai|ml|xyz|tech|info|biz|name|pro|aero|museum|coop|travel|jobs|mobi|cat|tel|asia|post|test|bitnet|csnet|arpa|nato|example|invalid|localhost|localdomain|onion|local|internal|private|corp|home|host|lan|wan|web|root|mail|users|admin|oracle|ibm|apple|sony|nasa|mit|stanford|oxford|cambridge|harvard|yale|princeton|berkeley|ucla|nyu|columbia|cornell|duke|rice|cmu|gatech|purdue|umich|unc|uw|ut|osu|psu|umd|rutgers|indiana|uiuc|wisc|iowa|msu|umn|missouri|arizona|colorado|oregon|washington|nevada|utah|idaho|montana|wyoming|alaska|hawaii|maine|vermont|newhampshire|massachusetts|rhodeisland|connecticut|newyork|newjersey|pennsylvania|delaware|maryland|virginia|westvirginia|northcarolina|southcarolina|georgia|florida|alabama|mississippi|tennessee|kentucky|ohio|michigan|indiana|illinois|wisconsin|minnesota|iowa|missouri|arkansas|louisiana|texas|oklahoma|kansas|nebraska|southdakota|northdakota|colorado|newmexico|arizona|utah|nevada|idaho|montana|wyoming|california|oregon|washington|alaska|hawaii)(?:[/\s,.:;!?)}\]"]|$)',  # Domaines isolés
            r'(?:ftp|ftps|ssh|telnet|gopher|file|mailto|news|nntp|prospero|aim|webcal|xmpp|tel|sms|bitcoin|geo|magnet|urn|spotify|lastfm|skype|facetime|callto|discord|slack|zoom|teams|meet):[^\s<>"{}|\\^`\[\]]+',  # Autres protocoles
            r'\[link\]|\[url\]|\[Link\]|\[URL\]|\(link\)|\(url\)',  # Marqueurs de liens
            r'<a\s+[^>]*>.*?</a>',  # Balises HTML de liens qui pourraient rester
        ]
        
        for pattern in url_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Normaliser les espaces après suppression des URLs
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Nettoyer les espaces multiples qui pourraient rester après suppression d'URLs
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)
        
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