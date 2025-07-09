from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json

Base = declarative_base()

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    style = Column(String(50))
    hashtags = Column(Text)  # JSON string
    source_articles = Column(Text)  # JSON string
    generated_at = Column(DateTime, default=datetime.now)
    approved = Column(Boolean, default=False)
    published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    variation_index = Column(Integer)
    
    def to_dict(self):
        source_articles = json.loads(self.source_articles) if self.source_articles else []
        hashtags_list = json.loads(self.hashtags) if self.hashtags else []
        
        return {
            'id': self.id,
            'content': self.content,
            'style': self.style,
            'domain_name': self.style,  # Compatibilité avec nouveau format
            'hashtags': hashtags_list,
            'source_articles': source_articles,
            'sources_count': len(set(article.get('source', '') for article in source_articles)) if source_articles else 0,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'approved': self.approved,
            'published': self.published,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'variation_index': self.variation_index
        }

class CachedArticle(Base):
    __tablename__ = 'cached_articles'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    source = Column(String(200), nullable=False)
    source_category = Column(String(100))
    source_reliability = Column(Integer)
    source_domains = Column(Text)  # JSON array of domains
    published = Column(DateTime)
    summary = Column(Text)
    relevance_score = Column(Float)
    domain_matches = Column(Integer)
    scraped_at = Column(DateTime, nullable=False)
    cache_expires_at = Column(DateTime, nullable=False)
    
    # Index pour améliorer les performances de recherche
    __table_args__ = (
        Index('idx_cache_expires', 'cache_expires_at'),
        Index('idx_source_scraped', 'source', 'scraped_at'),
    )
    
    def to_dict(self):
        return {
            'title': self.title,
            'url': self.url,
            'source': self.source,
            'category': self.source_category,
            'reliability': self.source_reliability,
            'domains': json.loads(self.source_domains) if self.source_domains else [],
            'published': self.published,
            'summary': self.summary,
            'relevance_score': self.relevance_score,
            'domain_matches': self.domain_matches,
            'scraped_at': self.scraped_at
        }

class DatabaseManager:
    def __init__(self, db_path='data/linkedin_posts.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def save_post(self, post_data: dict):
        # Convert source_articles to a simpler format for JSON serialization
        source_articles = post_data.get('source_articles', [])
        serializable_articles = []
        for article in source_articles:
            serializable_article = {
                'title': article.get('title'),
                'url': article.get('url'),
                'source': article.get('source')
            }
            serializable_articles.append(serializable_article)
        
        # Gérer les hashtags en string ou en array
        hashtags = post_data.get('hashtags', [])
        if isinstance(hashtags, str):
            # Nouveau format: string avec hashtags séparés par espaces
            hashtags_list = [tag.strip() for tag in hashtags.split() if tag.strip().startswith('#')]
        else:
            # Ancien format: array
            hashtags_list = hashtags
        
        post = Post(
            content=post_data['content'],
            style=post_data.get('style') or post_data.get('domain_name'),
            hashtags=json.dumps(hashtags_list),
            source_articles=json.dumps(serializable_articles),
            generated_at=post_data.get('generated_at', datetime.now()),
            variation_index=post_data.get('variation_index')
        )
        self.session.add(post)
        self.session.commit()
        return post.id
    
    def get_pending_posts(self):
        posts = self.session.query(Post).filter_by(approved=False, published=False).all()
        return [post.to_dict() for post in posts]
    
    def get_approved_posts(self):
        posts = self.session.query(Post).filter_by(approved=True, published=False).all()
        return [post.to_dict() for post in posts]
    
    def approve_post(self, post_id: int):
        post = self.session.query(Post).filter_by(id=post_id).first()
        if post:
            post.approved = True
            self.session.commit()
            return True
        return False
    
    def mark_as_published(self, post_id: int):
        post = self.session.query(Post).filter_by(id=post_id).first()
        if post:
            post.published = True
            post.published_at = datetime.now()
            self.session.commit()
            return True
        return False
    
    def delete_post(self, post_id: int):
        post = self.session.query(Post).filter_by(id=post_id).first()
        if post:
            self.session.delete(post)
            self.session.commit()
            return True
        return False
    
    def update_post_content(self, post_id: int, new_content: str):
        post = self.session.query(Post).filter_by(id=post_id).first()
        if post:
            post.content = new_content
            self.session.commit()
            return True
        return False
    
    # Cache management methods
    def get_cached_articles(self, source_names: list = None, hours_fresh: int = 6):
        """Récupère les articles en cache qui sont encore frais"""
        query = self.session.query(CachedArticle).filter(
            CachedArticle.cache_expires_at > datetime.now()
        )
        
        if source_names:
            query = query.filter(CachedArticle.source.in_(source_names))
        
        # Filtrer par fraîcheur de publication (3 jours max)
        three_days_ago = datetime.now() - timedelta(days=3)
        query = query.filter(CachedArticle.published >= three_days_ago)
        
        articles = query.all()
        return [article.to_dict() for article in articles]
    
    def save_articles_to_cache(self, articles: list, cache_duration_hours: int = 6):
        """Sauvegarde une liste d'articles dans le cache"""
        cache_expiry = datetime.now() + timedelta(hours=cache_duration_hours)
        
        for article in articles:
            # Vérifier si l'article existe déjà
            existing = self.session.query(CachedArticle).filter_by(url=article['url']).first()
            
            if existing:
                # Mettre à jour l'article existant
                existing.title = article['title']
                existing.summary = article.get('summary', '')
                existing.relevance_score = article.get('relevance_score', 0)
                existing.domain_matches = article.get('domain_matches', 0)
                existing.scraped_at = article.get('scraped_at', datetime.now())
                existing.cache_expires_at = cache_expiry
            else:
                # Créer un nouvel article en cache
                cached_article = CachedArticle(
                    url=article['url'],
                    title=article['title'],
                    source=article['source'],
                    source_category=article.get('category'),
                    source_reliability=article.get('reliability'),
                    source_domains=json.dumps(article.get('domains', [])),
                    published=article.get('published'),
                    summary=article.get('summary', ''),
                    relevance_score=article.get('relevance_score', 0),
                    domain_matches=article.get('domain_matches', 0),
                    scraped_at=article.get('scraped_at', datetime.now()),
                    cache_expires_at=cache_expiry
                )
                self.session.add(cached_article)
        
        self.session.commit()
    
    def clear_expired_cache(self):
        """Nettoie les articles expirés du cache"""
        self.session.query(CachedArticle).filter(
            CachedArticle.cache_expires_at < datetime.now()
        ).delete()
        self.session.commit()
    
    def get_cache_stats(self):
        """Retourne des statistiques sur le cache"""
        total_cached = self.session.query(CachedArticle).count()
        fresh_cached = self.session.query(CachedArticle).filter(
            CachedArticle.cache_expires_at > datetime.now()
        ).count()
        
        return {
            'total_articles': total_cached,
            'fresh_articles': fresh_cached,
            'expired_articles': total_cached - fresh_cached
        }