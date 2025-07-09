import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from loguru import logger
import time
from typing import List, Dict
import re

class TechNewsScraper:
    def __init__(self):
        self.sources = [
            {
                "name": "HackerNews",
                "url": "https://news.ycombinator.com/",
                "selector": ".athing",
                "title_selector": ".titleline > a",
                "score_selector": ".score"
            },
            {
                "name": "TechCrunch", 
                "url": "https://techcrunch.com/",
                "selector": "article",
                "title_selector": "h2 a",
                "date_selector": "time"
            },
            {
                "name": "TheVerge",
                "url": "https://www.theverge.com/tech",
                "selector": "article",
                "title_selector": "h2 a",
                "date_selector": "time"
            }
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def scrape_all_sources(self, max_articles: int = 10) -> List[Dict]:
        all_articles = []
        
        for source in self.sources:
            try:
                articles = self._scrape_source(source, max_articles)
                all_articles.extend(articles)
                logger.info(f"Scraped {len(articles)} articles from {source['name']}")
                time.sleep(2)  # Be respectful
            except Exception as e:
                logger.error(f"Error scraping {source['name']}: {e}")
                
        return self._filter_recent_articles(all_articles, max_articles)
    
    def _scrape_source(self, source: Dict, limit: int) -> List[Dict]:
        response = requests.get(source['url'], headers=self.headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        items = soup.select(source['selector'])[:limit]
        
        for item in items:
            article = self._extract_article_data(item, source)
            if article:
                articles.append(article)
                
        return articles
    
    def _extract_article_data(self, item, source: Dict) -> Dict:
        try:
            title_elem = item.select_one(source['title_selector'])
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')
            
            if not url.startswith('http'):
                url = source['url'].rstrip('/') + '/' + url.lstrip('/')
            
            article = {
                'title': title,
                'url': url,
                'source': source['name'],
                'scraped_at': datetime.now(),
                'score': None,
                'date': None
            }
            
            if 'score_selector' in source:
                score_elem = item.find_next_sibling().select_one(source['score_selector'])
                if score_elem:
                    score_text = score_elem.get_text()
                    article['score'] = int(re.findall(r'\d+', score_text)[0])
            
            if 'date_selector' in source:
                date_elem = item.select_one(source['date_selector'])
                if date_elem:
                    article['date'] = date_elem.get('datetime', date_elem.get_text())
                    
            return article
            
        except Exception as e:
            logger.debug(f"Error extracting article: {e}")
            return None
    
    def _filter_recent_articles(self, articles: List[Dict], limit: int) -> List[Dict]:
        sorted_articles = sorted(
            articles, 
            key=lambda x: x.get('score', 0) if x.get('score') else 0, 
            reverse=True
        )
        
        return sorted_articles[:limit]
    
    def get_trending_topics(self, articles: List[Dict]) -> List[str]:
        all_words = []
        for article in articles:
            words = re.findall(r'\b[A-Za-z]+\b', article['title'].lower())
            all_words.extend(words)
        
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'been'}
        
        word_freq = {}
        for word in all_words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        trending = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        return [word for word, _ in trending]