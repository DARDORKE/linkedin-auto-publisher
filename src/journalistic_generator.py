from google import genai
from typing import List, Dict
import os
from loguru import logger
import json
from datetime import datetime

class JournalisticPostGenerator:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"
        
    def generate_news_synthesis(self, articles: List[Dict]) -> Dict:
        """Génère une synthèse journalistique des actualités"""
        
        if not articles:
            return None
            
        # Organiser les articles par catégorie
        categorized = self._categorize_articles(articles)
        
        # Créer le prompt journalistique
        prompt = self._create_journalistic_prompt(categorized, articles[:10])
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            content = response.text
            
            return {
                'content': content,
                'type': 'journalistic_synthesis',
                'source_articles': articles[:10],  # Top 10 articles
                'categories_covered': list(categorized.keys()),
                'sources_count': len(set(article['source'] for article in articles[:10])),
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error generating journalistic post: {e}")
            return None
    
    def _categorize_articles(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Organise les articles par catégorie"""
        categories = {}
        for article in articles:
            category = article.get('category', 'general')
            if category not in categories:
                categories[category] = []
            categories[category].append(article)
        return categories
    
    def _create_journalistic_prompt(self, categorized: Dict, top_articles: List[Dict]) -> str:
        """Crée un prompt pour générer un article journalistique"""
        
        # Construire le résumé des sources
        sources_summary = self._build_sources_summary(top_articles)
        
        # Construire l'analyse par catégorie
        category_analysis = self._build_category_analysis(categorized)
        
        prompt = f"""
Tu es un journaliste tech professionnel. Rédige un article de synthèse factuel et informatif basé sur les actualités suivantes.

SOURCES ANALYSÉES ({len(top_articles)} articles principaux):
{sources_summary}

RÉPARTITION PAR SECTEUR:
{category_analysis}

CONSIGNES STRICTES:
1. Ton strictement journalistique et factuel
2. Structure en pyramide inversée (info principale d'abord)
3. Pas d'opinion personnelle, seulement des faits
4. Citer les sources entre parenthèses
5. Éviter les superlatifs et émotions
6. Longueur: 400-500 mots maximum
7. Une seule synthèse cohérente, pas de bullet points

STRUCTURE DEMANDÉE:
- Titre informatif (1 ligne)
- Lead: résumé des 2-3 infos principales (1 paragraphe)
- Développement par ordre d'importance décroissante
- Conclusion factuelle sur les implications

STYLE:
- Phrases courtes et claires
- Présent de vérité générale ou passé composé
- Vocabulaire technique précis mais accessible
- Transitions fluides entre les sujets

Rédige maintenant l'article de synthèse:
"""
        
        return prompt
    
    def _build_sources_summary(self, articles: List[Dict]) -> str:
        """Construit un résumé des sources avec leurs titres"""
        summary_lines = []
        
        for i, article in enumerate(articles, 1):
            source = article.get('source', 'Source inconnue')
            title = article.get('title', 'Titre indisponible')
            url = article.get('url', '')
            
            # Raccourcir les titres trop longs
            if len(title) > 80:
                title = title[:77] + "..."
            
            summary_lines.append(f"{i}. {source}: \"{title}\"")
        
        return "\n".join(summary_lines)
    
    def _build_category_analysis(self, categorized: Dict) -> str:
        """Construit l'analyse par catégorie"""
        category_names = {
            'tech_fr': 'Tech française',
            'tech_intl': 'Tech internationale', 
            'security': 'Cybersécurité',
            'startup': 'Startups & Business',
            'dev': 'Développement',
            'tech_research': 'Recherche & Innovation'
        }
        
        analysis_lines = []
        for category, articles in categorized.items():
            category_name = category_names.get(category, category.title())
            count = len(articles)
            
            if count > 0:
                # Prendre les 2 titres les plus pertinents
                top_titles = [article['title'][:50] + "..." if len(article['title']) > 50 
                             else article['title'] for article in articles[:2]]
                
                analysis_lines.append(f"• {category_name}: {count} article(s)")
                for title in top_titles:
                    analysis_lines.append(f"  - {title}")
        
        return "\n".join(analysis_lines)
    
    def generate_article_variations(self, articles: List[Dict], count: int = 1) -> List[Dict]:
        """Génère plusieurs variations d'articles (pour compatibilité)"""
        variations = []
        
        # Pour l'instant, on génère une seule synthèse journalistique
        article = self.generate_news_synthesis(articles)
        if article:
            article['variation_index'] = 1
            variations.append(article)
        
        return variations
    
    def get_article_metadata(self, content: str, articles: List[Dict]) -> Dict:
        """Extrait les métadonnées de l'article généré"""
        lines = content.split('\n')
        title = lines[0].strip() if lines else "Article de synthèse tech"
        
        # Compter les mots
        word_count = len(content.split())
        
        # Identifier les sources citées
        sources_mentioned = set()
        for article in articles:
            if article['source'] in content:
                sources_mentioned.add(article['source'])
        
        return {
            'title': title,
            'word_count': word_count,
            'sources_mentioned': list(sources_mentioned),
            'categories_count': len(set(article.get('category', 'general') for article in articles))
        }