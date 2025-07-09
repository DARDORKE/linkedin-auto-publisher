import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from loguru import logger
import time
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin, urlparse
import feedparser

class FullStackDevScraper:
    def __init__(self):
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
                "name": "PHP Weekly",
                "type": "rss",
                "url": "http://www.phpweekly.com/feed.xml",
                "category": "backend",
                "reliability": 8,
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
                "name": "Python Weekly",
                "type": "rss",
                "url": "https://www.pythonweekly.com/rss.xml",
                "category": "backend",
                "reliability": 8,
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
                "url": "https://cloud.google.com/blog/rss/",
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
                "url": "https://openai.com/blog/rss/",
                "category": "ai",
                "reliability": 10,
                "domains": ["ai"]
            },
            {
                "name": "Google AI Blog",
                "type": "rss",
                "url": "https://ai.googleblog.com/feeds/posts/default",
                "category": "ai",
                "reliability": 10,
                "domains": ["ai"]
            },
            {
                "name": "Anthropic News",
                "type": "rss",
                "url": "https://www.anthropic.com/news/rss.xml",
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
                "name": "Papers With Code",
                "type": "rss",
                "url": "https://paperswithcode.com/feed.xml",
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
                "url": "https://ai.meta.com/blog/rss/",
                "category": "ai",
                "reliability": 9,
                "domains": ["ai"]
            },
            {
                "name": "MIT CSAIL News",
                "type": "rss",
                "url": "https://www.csail.mit.edu/news/rss.xml",
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
                "url": "https://ai.googleblog.com/feeds/posts/default?alt=rss",
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
                "name": "Wired Tech",
                "type": "rss",
                "url": "https://www.wired.com/feed/category/business/tech/rss",
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
        
    def scrape_all_sources(self, max_articles: int = 40) -> List[Dict]:
        all_articles = []
        
        for source in self.sources:
            try:
                if source['type'] == 'rss':
                    articles = self._scrape_rss(source)
                else:
                    articles = self._scrape_web(source)
                    
                # Filtrer par pertinence technologique
                relevant_articles = self._filter_tech_articles(articles)
                all_articles.extend(relevant_articles)
                logger.info(f"Scraped {len(relevant_articles)} tech articles from {source['name']}")
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping {source['name']}: {e}")
        
        # Filtrer par fraîcheur (articles de moins de 3 jours)
        fresh_articles = self._filter_by_freshness(all_articles, max_days=3)
        logger.info(f"Kept {len(fresh_articles)} articles after freshness filter (< 3 days)")
        
        # Dédupliquer et scorer
        unique_articles = self._deduplicate_articles(fresh_articles)
        scored_articles = self._score_tech_articles(unique_articles)
        
        # Équilibrer les domaines
        balanced_articles = self._balance_domains(scored_articles, max_articles)
        
        return sorted(balanced_articles, key=lambda x: x['relevance_score'], reverse=True)[:max_articles]
    
    def _scrape_rss(self, source: Dict) -> List[Dict]:
        articles = []
        feed = feedparser.parse(source['url'])
        
        for entry in feed.entries[:12]:  # Limiter par source
            try:
                article = {
                    'title': entry.title,
                    'url': entry.link,
                    'source': source['name'],
                    'category': source['category'],
                    'reliability': source['reliability'],
                    'domains': source['domains'],
                    'published': self._parse_date(entry.get('published', '')),
                    'summary': BeautifulSoup(entry.get('summary', ''), 'html.parser').get_text()[:400],
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
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            normalized_title = re.sub(r'[^\w\s]', '', article['title'].lower())
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_articles.append(article)
                
        return unique_articles
    
    def _score_tech_articles(self, articles: List[Dict]) -> List[Dict]:
        """Score adapté pour frontend + backend + IA"""
        for article in articles:
            score = 0
            
            # Score de base par fiabilité
            score += article['reliability'] * 6
            
            # Score par fraîcheur (privilégier fortement les articles récents)
            age_hours = (datetime.now() - article.get('published', datetime.now())).total_seconds() / 3600
            if age_hours < 6:  # Moins de 6 heures
                score += 35
            elif age_hours < 24:  # Moins de 24 heures
                score += 25
            elif age_hours < 48:  # Moins de 2 jours
                score += 15
            elif age_hours < 72:  # Moins de 3 jours
                score += 8
            else:  # Plus de 3 jours (ne devrait pas arriver avec le filtre)
                score += 0
            
            # Score par domaines techniques
            text_content = (article['title'] + ' ' + article.get('summary', '')).lower()
            
            for domain, keywords in self.tech_keywords.items():
                domain_score = 0
                for keyword in keywords['high']:
                    if keyword in text_content:
                        domain_score += 15
                for keyword in keywords['medium']:
                    if keyword in text_content:
                        domain_score += 10
                for keyword in keywords['tools']:
                    if keyword in text_content:
                        domain_score += 5
                
                # Limiter le score par domaine pour éviter la sur-pondération
                score += min(domain_score, 30)
            
            # Bonus pour sources officielles
            official_sources = ['OpenAI Blog', 'Google AI Blog', 'React Blog', 'Node.js Blog', 'Go Dev Blog', 'Rust Blog']
            if article['source'] in official_sources:
                score += 25
            
            # Bonus pour multi-domaines
            if len(article.get('relevant_domains', [])) > 1:
                score += 10
            
            # Bonus HackerNews
            if 'hn_score' in article:
                score += min(article['hn_score'] / 5, 20)
            
            article['relevance_score'] = max(0, score)
            
        return articles
    
    def _balance_domains(self, articles: List[Dict], max_articles: int) -> List[Dict]:
        """Équilibre la représentation des trois domaines"""
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
                # Assigner selon la catégorie de la source
                source_category = article.get('category', '')
                if source_category in ['ai']:
                    articles_by_domain['ai'].append(article)
                elif source_category in ['backend']:
                    articles_by_domain['backend'].append(article)
                else:
                    articles_by_domain['frontend'].append(article)
        
        # Équilibrer : 30% frontend, 30% backend, 25% IA, 15% multi-domaines
        balanced = []
        target_frontend = max(1, int(max_articles * 0.30))
        target_backend = max(1, int(max_articles * 0.30))
        target_ai = max(1, int(max_articles * 0.25))
        target_multi = max(1, max_articles - target_frontend - target_backend - target_ai)
        
        # Trier chaque domaine par score
        for domain in articles_by_domain:
            articles_by_domain[domain].sort(key=lambda x: x['relevance_score'], reverse=True)
        
        balanced.extend(articles_by_domain['frontend'][:target_frontend])
        balanced.extend(articles_by_domain['backend'][:target_backend])
        balanced.extend(articles_by_domain['ai'][:target_ai])
        balanced.extend(articles_by_domain['multi'][:target_multi])
        
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
                            tech_counts[domain][keyword] += article.get('relevance_score', 1)
        
        # Top 5 par domaine
        trending = {}
        for domain, counts in tech_counts.items():
            sorted_techs = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
            trending[domain] = [tech for tech, _ in sorted_techs]
            
        return trending