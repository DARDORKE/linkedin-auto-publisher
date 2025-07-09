from google import genai
from typing import List, Dict
import os
from loguru import logger
import json
from datetime import datetime

class WebDevPostGenerator:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"
        
    def generate_webdev_synthesis(self, articles: List[Dict]) -> Dict:
        """Génère une synthèse journalistique spécialisée développement web"""
        
        if not articles:
            return None
            
        # Organiser les articles par catégorie
        categorized = self._categorize_articles(articles)
        
        # Créer le prompt spécialisé webdev
        prompt = self._create_webdev_prompt(categorized, articles[:15])
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            content = response.text
            
            # Générer la section sources
            sources_section = self._generate_sources_section(articles[:15])
            
            # Combiner l'article et les sources
            full_content = content + "\n\n" + sources_section
            
            return {
                'content': full_content,
                'type': 'webdev_synthesis',
                'source_articles': articles[:15],
                'categories_covered': list(categorized.keys()),
                'sources_count': len(set(article['source'] for article in articles[:15])),
                'trending_topics': self._extract_trending_topics(articles),
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error generating webdev post: {e}")
            return None
    
    def _categorize_articles(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Organise les articles par catégorie webdev"""
        categories = {}
        for article in articles:
            category = article.get('category', 'general')
            if category not in categories:
                categories[category] = []
            categories[category].append(article)
        return categories
    
    def _create_webdev_prompt(self, categorized: Dict, top_articles: List[Dict]) -> str:
        """Crée un prompt spécialisé pour le développement web"""
        
        sources_summary = self._build_webdev_sources_summary(top_articles)
        category_analysis = self._build_webdev_category_analysis(categorized)
        trending_tech = self._extract_trending_topics(top_articles)
        
        prompt = f"""
Tu es un journaliste spécialisé en développement web. Rédige un article de synthèse informatif sur les actualités récentes du développement web.

SOURCES ANALYSÉES ({len(top_articles)} articles):
{sources_summary}

RÉPARTITION PAR DOMAINE:
{category_analysis}

TECHNOLOGIES TENDANCES: {', '.join(trending_tech[:8])}

CONSIGNES STRICTES:
1. Ton journalistique professionnel et factuel
2. Focus exclusif sur le développement web (frontend, backend, frameworks, outils)
3. Structure en pyramide inversée
4. Citer systématiquement les sources entre parenthèses : (Source)
5. Aucune opinion personnelle, seulement des faits
6. Longueur: 400-500 mots
7. Vocabulaire technique précis mais accessible

STRUCTURE OBLIGATOIRE:
- Titre informatif sur les tendances webdev
- Lead: 2-3 informations principales (frameworks, outils, standards)
- Développement par ordre d'importance :
  * Nouveautés frameworks/libraries
  * Évolutions des standards web
  * Outils et workflow
  * Performance et bonnes pratiques
- Conclusion sur l'impact pour les développeurs

STYLE REQUIS:
- Présent de vérité générale pour les faits établis
- Citations précises des sources
- Transitions fluides entre technologies
- Éviter le jargon inaccessible
- Privilégier les implications pratiques pour les développeurs

NE PAS inclure de section sources à la fin - elle sera ajoutée automatiquement.

Rédige maintenant l'article de synthèse développement web:
"""
        
        return prompt
    
    def _build_webdev_sources_summary(self, articles: List[Dict]) -> str:
        """Construit un résumé des sources spécialisé webdev"""
        summary_lines = []
        
        for i, article in enumerate(articles, 1):
            source = article.get('source', 'Source inconnue')
            title = article.get('title', 'Titre indisponible')
            category = article.get('category', 'general')
            
            # Raccourcir les titres
            if len(title) > 70:
                title = title[:67] + "..."
            
            # Ajouter la catégorie pour le contexte
            category_label = {
                'frontend': '[Frontend]',
                'backend': '[Backend]', 
                'javascript': '[JavaScript]',
                'frameworks': '[Frameworks]',
                'webdev': '[WebDev]',
                'community': '[Community]',
                'webdev_fr': '[WebDev FR]'
            }.get(category, f'[{category.title()}]')
            
            summary_lines.append(f"{i}. {source} {category_label}: \"{title}\"")
        
        return "\n".join(summary_lines)
    
    def _build_webdev_category_analysis(self, categorized: Dict) -> str:
        """Analyse par catégorie webdev"""
        category_names = {
            'webdev_fr': 'Développement Web Français',
            'frontend': 'Frontend & UI/UX',
            'backend': 'Backend & APIs',
            'javascript': 'JavaScript & TypeScript',
            'frameworks': 'Frameworks & Libraries',
            'webdev': 'Standards & Bonnes Pratiques',
            'community': 'Communauté & Tutoriels',
            'news': 'Actualités Tech Web'
        }
        
        analysis_lines = []
        for category, articles in categorized.items():
            category_name = category_names.get(category, category.title())
            count = len(articles)
            
            if count > 0:
                # Technologies mentionnées
                technologies = set()
                for article in articles[:3]:
                    text = (article['title'] + ' ' + article.get('summary', '')).lower()
                    tech_keywords = ['react', 'vue', 'angular', 'svelte', 'nextjs', 'nuxtjs', 'typescript', 'javascript', 'css', 'html', 'nodejs', 'express', 'fastify']
                    for tech in tech_keywords:
                        if tech in text:
                            technologies.add(tech.capitalize())
                
                analysis_lines.append(f"• {category_name}: {count} article(s)")
                if technologies:
                    analysis_lines.append(f"  Technologies: {', '.join(list(technologies)[:4])}")
        
        return "\n".join(analysis_lines)
    
    def _extract_trending_topics(self, articles: List[Dict]) -> List[str]:
        """Extrait les technologies tendances"""
        tech_mentions = {}
        
        webdev_techs = [
            'react', 'vue', 'angular', 'svelte', 'solid', 'nextjs', 'nuxtjs', 'remix',
            'typescript', 'javascript', 'nodejs', 'express', 'fastify', 'nestjs',
            'css', 'sass', 'tailwind', 'styled-components', 'emotion',
            'webpack', 'vite', 'rollup', 'esbuild', 'turbopack',
            'jest', 'vitest', 'cypress', 'playwright', 'testing-library'
        ]
        
        for article in articles:
            text = (article['title'] + ' ' + article.get('summary', '')).lower()
            for tech in webdev_techs:
                if tech in text:
                    tech_mentions[tech] = tech_mentions.get(tech, 0) + article.get('relevance_score', 1)
        
        # Retourner les 10 technologies les plus mentionnées
        trending = sorted(tech_mentions.items(), key=lambda x: x[1], reverse=True)[:10]
        return [tech for tech, _ in trending]
    
    def _generate_sources_section(self, articles: List[Dict]) -> str:
        """Génère une section sources détaillée"""
        sources_by_category = {}
        
        for article in articles:
            category = article.get('category', 'general')
            if category not in sources_by_category:
                sources_by_category[category] = []
            
            source_info = {
                'source': article['source'],
                'title': article['title'],
                'url': article['url']
            }
            sources_by_category[category].append(source_info)
        
        # Construire la section sources
        sources_section = "**SOURCES :**\n\n"
        
        category_names = {
            'webdev_fr': 'Développement Web Français',
            'frontend': 'Frontend & UI/UX', 
            'backend': 'Backend & APIs',
            'javascript': 'JavaScript & TypeScript',
            'frameworks': 'Frameworks & Libraries',
            'webdev': 'Standards Web',
            'community': 'Communauté',
            'news': 'Actualités'
        }
        
        for category, sources in sources_by_category.items():
            if sources:
                category_name = category_names.get(category, category.title())
                sources_section += f"**{category_name} :**\n"
                
                for i, source in enumerate(sources[:5], 1):  # Max 5 sources par catégorie
                    title = source['title']
                    if len(title) > 60:
                        title = title[:57] + "..."
                    sources_section += f"{i}. {source['source']} - \"{title}\"\n"
                
                sources_section += "\n"
        
        return sources_section.strip()
    
    def generate_article_variations(self, articles: List[Dict], count: int = 1) -> List[Dict]:
        """Génère une synthèse webdev (compatibilité avec l'interface existante)"""
        variations = []
        
        article = self.generate_webdev_synthesis(articles)
        if article:
            article['variation_index'] = 1
            variations.append(article)
        
        return variations