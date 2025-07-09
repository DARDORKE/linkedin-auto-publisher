from google import genai
from typing import List, Dict
import os
from loguru import logger
import json
from datetime import datetime

class LinkedInPostGenerator:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"
        
        self.post_styles = [
            "professionnel et informatif",
            "inspirant et motivant", 
            "analytique et perspicace",
            "conversationnel et engageant"
        ]
        
    def generate_post(self, articles: List[Dict], style: str = None) -> Dict:
        if not style:
            import random
            style = random.choice(self.post_styles)
            
        prompt = self._create_prompt(articles, style)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            post_content = response.text
            
            return {
                'content': post_content,
                'style': style,
                'source_articles': articles,
                'hashtags': self._extract_hashtags(post_content),
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error generating post: {e}")
            return None
    
    def _create_prompt(self, articles: List[Dict], style: str) -> str:
        articles_summary = "\n".join([
            f"- {article['title']} (Source: {article['source']})"
            for article in articles[:5]
        ])
        
        prompt = f"""
        Tu es un expert en création de contenu LinkedIn dans le domaine de la tech.
        
        Voici les dernières actualités tech du jour :
        {articles_summary}
        
        Crée un post LinkedIn en français, style {style}, qui :
        1. Résume les tendances principales de ces actualités
        2. Apporte une analyse ou perspective unique
        3. Engage la communauté avec une question ou réflexion
        4. Reste concis (max 300 mots)
        5. Inclut 3-5 hashtags pertinents en fin de post
        
        Le post doit être authentique, apporter de la valeur et encourager l'engagement.
        
        Format souhaité :
        [Accroche captivante]
        
        [Corps du message avec insights]
        
        [Question ou appel à l'action]
        
        #hashtag1 #hashtag2 #hashtag3
        """
        
        return prompt
    
    def _extract_hashtags(self, content: str) -> List[str]:
        import re
        hashtags = re.findall(r'#\w+', content)
        return [tag.lower() for tag in hashtags]
    
    def generate_variations(self, articles: List[Dict], count: int = 3) -> List[Dict]:
        variations = []
        used_styles = []
        
        for i in range(count):
            available_styles = [s for s in self.post_styles if s not in used_styles]
            if not available_styles:
                used_styles = []
                available_styles = self.post_styles
                
            style = available_styles[0]
            used_styles.append(style)
            
            post = self.generate_post(articles, style)
            if post:
                post['variation_index'] = i + 1
                variations.append(post)
                
        return variations
    
    def enhance_with_emojis(self, content: str) -> str:
        emoji_map = {
            'innovation': '💡',
            'AI': '🤖',
            'intelligence artificielle': '🤖',
            'startup': '🚀',
            'croissance': '📈',
            'technologie': '💻',
            'développement': '⚡',
            'futur': '🔮',
            'data': '📊',
            'sécurité': '🔒',
            'cloud': '☁️',
            'mobile': '📱'
        }
        
        enhanced_content = content
        for keyword, emoji in emoji_map.items():
            enhanced_content = enhanced_content.replace(keyword, f"{keyword} {emoji}")
            
        return enhanced_content