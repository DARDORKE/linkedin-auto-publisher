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
        return {
            'id': self.id,
            'content': self.content,
            'style': self.style,
            'hashtags': json.loads(self.hashtags) if self.hashtags else [],
            'source_articles': json.loads(self.source_articles) if self.source_articles else [],
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
        post = Post(
            content=post_data['content'],
            style=post_data.get('style'),
            hashtags=json.dumps(post_data.get('hashtags', [])),
            source_articles=json.dumps(post_data.get('source_articles', [])),
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