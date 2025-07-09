import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from loguru import logger
import time
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin, urlparse
import feedparser

class JournalisticNewsScraper:
    def __init__(self):
        self.sources = [
            # Sources tech françaises
            {
                "name": "Le Monde Tech",
                "type": "rss",
                "url": "https://www.lemonde.fr/technologies/rss_full.xml",
                "category": "tech_fr",
                "reliability": 10
            },
            {
                "name": "01net",
                "type": "rss", 
                "url": "https://www.01net.com/actualites/feed/",
                "category": "tech_fr",
                "reliability": 8
            },
            {
                "name": "Numerama",
                "type": "rss",
                "url": "https://www.numerama.com/feed/",
                "category": "tech_fr",
                "reliability": 8
            },
            {
                "name": "NextINpact",
                "type": "rss",
                "url": "https://www.nextinpact.com/rss/news.xml",
                "category": "tech_fr",
                "reliability": 9
            },
            
            # Sources tech internationales
            {
                "name": "Ars Technica",
                "type": "rss",
                "url": "https://feeds.arstechnica.com/arstechnica/index",
                "category": "tech_intl",
                "reliability": 9
            },
            {
                "name": "The Register",
                "type": "rss",
                "url": "https://www.theregister.com/headlines.atom",
                "category": "tech_intl",
                "reliability": 8
            },
            {
                "name": "Wired",
                "type": "rss",
                "url": "https://www.wired.com/feed/rss",
                "category": "tech_intl",
                "reliability": 9
            },
            {
                "name": "MIT Technology Review",
                "type": "rss",
                "url": "https://www.technologyreview.com/feed/",
                "category": "tech_research",
                "reliability": 10
            },
            
            # Sources business/startup
            {
                "name": "TechCrunch",
                "type": "rss",
                "url": "https://techcrunch.com/feed/",
                "category": "startup",
                "reliability": 8
            },
            {
                "name": "VentureBeat",
                "type": "rss",
                "url": "https://feeds.feedburner.com/venturebeat/SZYF",
                "category": "startup",
                "reliability": 8
            },
            
            # Sources cybersécurité
            {
                "name": "The Hacker News",
                "type": "rss",
                "url": "https://feeds.feedburner.com/TheHackersNews",
                "category": "security",
                "reliability": 9
            },
            {
                "name": "BleepingComputer",
                "type": "rss",
                "url": "https://www.bleepingcomputer.com/feed/",
                "category": "security",
                "reliability": 9
            },
            
            # Sources développement
            {
                "name": "Dev.to",
                "type": "rss",
                "url": "https://dev.to/feed",
                "category": "dev",
                "reliability": 7
            },
            {
                "name": "Hacker News",
                "type": "web",
                "url": "https://news.ycombinator.com/",
                "selector": ".athing",
                "title_selector": ".titleline > a",
                "score_selector": ".score",
                "category": "dev",
                "reliability": 8
            }
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Mots-clés pour évaluer la pertinence
        self.relevance_keywords = {
            'high': ['breaking', 'major', 'critical', 'vulnerability', 'breach', 'acquisition', 
                    'ipo', 'funding', 'ai', 'intelligence artificielle', 'quantum', 'révolution'],
            'medium': ['update', 'release', 'launch', 'announces', 'partnership', 'nouvelle version',
                      'mise à jour', 'partenariat', 'étude', 'rapport'],
            'low': ['opinion', 'review', 'test', 'rumor', 'speculation', 'might', 'could']
        }
        
    def scrape_all_sources(self, max_articles: int = 50) -> List[Dict]:
        all_articles = []
        
        for source in self.sources:
            try:
                if source['type'] == 'rss':
                    articles = self._scrape_rss(source)
                else:
                    articles = self._scrape_web(source)
                    
                all_articles.extend(articles)
                logger.info(f"Scraped {len(articles)} articles from {source['name']}")
                time.sleep(1)  # Respectful scraping
                
            except Exception as e:
                logger.error(f"Error scraping {source['name']}: {e}")
        
        # Dédupliquer et scorer les articles
        unique_articles = self._deduplicate_articles(all_articles)
        scored_articles = self._score_articles(unique_articles)
        
        # Retourner les meilleurs articles
        return sorted(scored_articles, key=lambda x: x['relevance_score'], reverse=True)[:max_articles]
    
    def _scrape_rss(self, source: Dict) -> List[Dict]:
        articles = []
        feed = feedparser.parse(source['url'])
        
        for entry in feed.entries[:20]:  # Limiter à 20 articles par source
            try:
                article = {
                    'title': entry.title,
                    'url': entry.link,
                    'source': source['name'],
                    'category': source['category'],
                    'reliability': source['reliability'],
                    'published': self._parse_date(entry.get('published', '')),
                    'summary': BeautifulSoup(entry.get('summary', ''), 'html.parser').get_text()[:300],
                    'scraped_at': datetime.now()
                }
                articles.append(article)
            except Exception as e:
                logger.debug(f"Error parsing RSS entry: {e}")
                
        return articles
    
    def _scrape_web(self, source: Dict) -> List[Dict]:
        articles = []
        response = requests.get(source['url'], headers=self.headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.select(source['selector'])[:20]
        
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
                    'published': datetime.now() - timedelta(hours=1),  # Estimation
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
    
    def _parse_date(self, date_str: str) -> datetime:
        try:
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            # Assurer que toutes les dates sont timezone-naive pour cohérence
            if parsed_date.tzinfo is not None:
                parsed_date = parsed_date.replace(tzinfo=None)
            return parsed_date
        except:
            return datetime.now()
    
    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            # Normaliser le titre pour la comparaison
            normalized_title = re.sub(r'[^\w\s]', '', article['title'].lower())
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_articles.append(article)
                
        return unique_articles
    
    def _score_articles(self, articles: List[Dict]) -> List[Dict]:
        for article in articles:
            score = 0
            
            # Score basé sur la fiabilité de la source
            score += article['reliability'] * 10
            
            # Score basé sur la fraîcheur
            age_hours = (datetime.now() - article.get('published', datetime.now())).total_seconds() / 3600
            if age_hours < 6:
                score += 20
            elif age_hours < 24:
                score += 10
            elif age_hours < 48:
                score += 5
            
            # Score basé sur les mots-clés
            title_lower = article['title'].lower()
            summary_lower = article.get('summary', '').lower()
            combined_text = title_lower + ' ' + summary_lower
            
            for keyword in self.relevance_keywords['high']:
                if keyword in combined_text:
                    score += 15
                    
            for keyword in self.relevance_keywords['medium']:
                if keyword in combined_text:
                    score += 8
                    
            for keyword in self.relevance_keywords['low']:
                if keyword in combined_text:
                    score -= 5
            
            # Bonus pour HackerNews score
            if 'hn_score' in article:
                score += min(article['hn_score'] / 10, 30)
            
            # Catégories prioritaires
            priority_categories = ['security', 'tech_research', 'tech_fr']
            if article['category'] in priority_categories:
                score += 10
            
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
    
    def get_trending_topics(self, articles: List[Dict]) -> List[str]:
        # Extraction plus sophistiquée des tendances
        all_words = []
        for article in articles:
            # Combiner titre et résumé
            text = article['title'] + ' ' + article.get('summary', '')
            # Extraire les mots significatifs (plus de 4 caractères)
            words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
            all_words.extend(words)
        
        # Stop words étendus
        stop_words = {
            'the', 'and', 'for', 'with', 'from', 'that', 'this', 'will', 'your',
            'have', 'more', 'been', 'what', 'when', 'where', 'which', 'their',
            'would', 'there', 'could', 'about', 'after', 'before', 'dans', 'pour',
            'avec', 'plus', 'être', 'avoir', 'faire', 'tout', 'nous', 'vous'
        }
        
        word_freq = {}
        for word in all_words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Retourner les 15 mots les plus fréquents
        trending = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]
        return [word for word, _ in trending]