from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
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