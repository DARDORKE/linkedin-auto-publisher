from google import genai
from typing import List, Dict
import os
from loguru import logger
import json
from datetime import datetime

class SpecializedPostGenerator:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"
        
        # Définir les domaines et leurs spécialités
        self.domains = {
            'frontend': {
                'name': 'Développement Frontend',
                'focus': 'interfaces utilisateur, frameworks JavaScript, CSS, expérience utilisateur',
                'keywords': ['react', 'vue', 'angular', 'svelte', 'typescript', 'javascript', 'css', 'html', 'nextjs', 'nuxtjs']
            },
            'backend': {
                'name': 'Développement Backend',
                'focus': 'serveurs, APIs, bases de données, architecture logicielle',
                'keywords': ['nodejs', 'python', 'java', 'go', 'rust', 'php', 'django', 'fastapi', 'spring', 'api', 'database']
            },
            'ai': {
                'name': 'Intelligence Artificielle',
                'focus': 'machine learning, IA générative, modèles de langage, outils IA',
                'keywords': ['ai', 'ml', 'llm', 'gpt', 'claude', 'gemini', 'pytorch', 'tensorflow', 'openai', 'anthropic']
            },
            'general': {
                'name': 'Actualités Générales Tech',
                'focus': 'outils de développement, DevOps, nouvelles technologies, industrie tech',
                'keywords': ['github', 'docker', 'kubernetes', 'devops', 'security', 'startup', 'tech industry']
            }
        }
        
    def generate_specialized_posts(self, articles: List[Dict]) -> List[Dict]:
        """Génère des posts spécialisés pour chaque domaine ayant suffisamment d'articles"""
        specialized_posts = []
        
        # Organiser les articles par domaine
        articles_by_domain = self._organize_articles_by_domain(articles)
        
        for domain_key, domain_articles in articles_by_domain.items():
            # Générer un post seulement si on a au moins 3 articles dans le domaine
            if len(domain_articles) >= 3:
                post = self._generate_domain_post(domain_key, domain_articles)
                if post:
                    specialized_posts.append(post)
                    logger.info(f"Generated specialized post for {domain_key} with {len(domain_articles)} articles")
            else:
                logger.info(f"Skipped {domain_key} - only {len(domain_articles)} articles (minimum 3 required)")
        
        return specialized_posts
    
    def _organize_articles_by_domain(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Organise les articles par domaine technique"""
        by_domain = {domain: [] for domain in self.domains.keys()}
        
        for article in articles:
            assigned_domain = self._determine_article_domain(article)
            by_domain[assigned_domain].append(article)
        
        # Trier chaque domaine par score de pertinence
        for domain in by_domain:
            by_domain[domain] = sorted(by_domain[domain], key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return by_domain
    
    def _determine_article_domain(self, article: Dict) -> str:
        """Détermine le domaine principal d'un article"""
        text_content = (article['title'] + ' ' + article.get('summary', '')).lower()
        category = article.get('category', 'general')
        
        # Scoring par domaine
        domain_scores = {}
        
        for domain_key, domain_info in self.domains.items():
            score = 0
            
            # Score basé sur les mots-clés
            for keyword in domain_info['keywords']:
                if keyword in text_content:
                    score += 10
            
            # Score basé sur la catégorie de la source
            if domain_key == 'ai' and category == 'ai':
                score += 20
            elif domain_key == 'backend' and category == 'backend':
                score += 20
            elif domain_key == 'frontend' and category == 'frontend':
                score += 20
            elif domain_key == 'general' and category in ['devtools', 'enterprise', 'devops']:
                score += 15
            
            domain_scores[domain_key] = score
        
        # Retourner le domaine avec le score le plus élevé
        best_domain = max(domain_scores, key=domain_scores.get)
        
        # Si aucun domaine n'a de score significatif, classer en général
        if domain_scores[best_domain] == 0:
            return 'general'
        
        return best_domain
    
    def _generate_domain_post(self, domain_key: str, articles: List[Dict]) -> Dict:
        """Génère un post spécialisé pour un domaine donné"""
        domain_info = self.domains[domain_key]
        
        # Limiter aux 8 meilleurs articles du domaine
        top_articles = articles[:8]
        
        # Créer le prompt spécialisé
        prompt = self._create_specialized_prompt(domain_key, domain_info, top_articles)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            content = response.text
            
            # Générer la section sources
            sources_section = self._generate_domain_sources(domain_key, top_articles)
            
            # Combiner l'article et les sources
            full_content = content + "\n\n" + sources_section
            
            return {
                'content': full_content,
                'type': f'{domain_key}_specialized',
                'domain': domain_key,
                'domain_name': domain_info['name'],
                'source_articles': top_articles,
                'sources_count': len(set(article['source'] for article in top_articles)),
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error generating {domain_key} post: {e}")
            return None
    
    def _create_specialized_prompt(self, domain_key: str, domain_info: Dict, articles: List[Dict]) -> str:
        """Crée un prompt spécialisé pour un domaine spécifique"""
        
        articles_summary = "\n".join([
            f"{i+1}. {article['source']}: \"{article['title']}\""
            for i, article in enumerate(articles)
        ])
        
        # Technologies mentionnées dans les articles
        mentioned_techs = set()
        for article in articles:
            text = (article['title'] + ' ' + article.get('summary', '')).lower()
            for keyword in domain_info['keywords']:
                if keyword in text:
                    mentioned_techs.add(keyword.capitalize())
        
        tech_context = ', '.join(list(mentioned_techs)[:6]) if mentioned_techs else 'diverses technologies'
        
        # Prompt spécialisé par domaine
        domain_prompts = {
            'frontend': f"""
Tu es un journaliste spécialisé en développement frontend. Rédige un article de synthèse sur les dernières actualités du développement d'interfaces utilisateur.

FOCUS: {domain_info['focus']}
TECHNOLOGIES ABORDÉES: {tech_context}

SOURCES ({len(articles)} articles):
{articles_summary}

CONSIGNES:
1. Ton journalistique spécialisé frontend
2. Focus sur les frameworks, outils UI, performance côté client
3. Analyser l'impact pour les développeurs frontend
4. Citer les sources entre parenthèses
5. 300-400 mots maximum
6. Aucune opinion, seulement des faits

STRUCTURE:
- Titre accrocheur sur les tendances frontend
- Lead: 1-2 développements majeurs
- Analyse technique des évolutions
- Implications pour les développeurs frontend
- Conclusion sur l'écosystème frontend

Rédige l'article spécialisé frontend:
""",
            'backend': f"""
Tu es un journaliste spécialisé en développement backend. Rédige un article de synthèse sur les dernières actualités du développement côté serveur.

FOCUS: {domain_info['focus']}
TECHNOLOGIES ABORDÉES: {tech_context}

SOURCES ({len(articles)} articles):
{articles_summary}

CONSIGNES:
1. Ton journalistique spécialisé backend
2. Focus sur les APIs, bases de données, architecture serveur
3. Analyser l'impact pour les développeurs backend
4. Citer les sources entre parenthèses
5. 300-400 mots maximum
6. Aucune opinion, seulement des faits

STRUCTURE:
- Titre accrocheur sur les évolutions backend
- Lead: 1-2 développements techniques majeurs
- Analyse des nouvelles approches/outils
- Implications pour l'architecture et les performances
- Conclusion sur l'écosystème backend

Rédige l'article spécialisé backend:
""",
            'ai': f"""
Tu es un journaliste spécialisé en intelligence artificielle. Rédige un article de synthèse sur les dernières actualités en IA et machine learning.

FOCUS: {domain_info['focus']}
TECHNOLOGIES ABORDÉES: {tech_context}

SOURCES ({len(articles)} articles):
{articles_summary}

CONSIGNES:
1. Ton journalistique spécialisé IA
2. Focus sur les modèles, outils IA, applications pratiques
3. Analyser l'impact pour les développeurs et l'industrie
4. Citer les sources entre parenthèses
5. 300-400 mots maximum
6. Aucune opinion, seulement des faits

STRUCTURE:
- Titre accrocheur sur les avancées IA
- Lead: 1-2 développements majeurs en IA
- Analyse des nouvelles capacités/modèles
- Implications pour les développeurs et les entreprises
- Conclusion sur l'évolution de l'écosystème IA

Rédige l'article spécialisé IA:
""",
            'general': f"""
Tu es un journaliste spécialisé en actualités technologiques. Rédige un article de synthèse sur les dernières actualités générales du monde tech.

FOCUS: {domain_info['focus']}
DOMAINES COUVERTS: {tech_context}

SOURCES ({len(articles)} articles):
{articles_summary}

CONSIGNES:
1. Ton journalistique généraliste tech
2. Focus sur les outils, tendances industrie, innovations
3. Analyser l'impact pour l'écosystème de développement
4. Citer les sources entre parenthèses
5. 300-400 mots maximum
6. Aucune opinion, seulement des faits

STRUCTURE:
- Titre accrocheur sur les tendances tech générales
- Lead: 1-2 développements significatifs
- Analyse des nouvelles approches/outils
- Implications pour les développeurs et l'industrie
- Conclusion sur l'évolution du secteur tech

Rédige l'article généraliste tech:
"""
        }
        
        return domain_prompts.get(domain_key, domain_prompts['general'])
    
    def _generate_domain_sources(self, domain_key: str, articles: List[Dict]) -> str:
        """Génère une section sources pour un domaine spécifique"""
        domain_name = self.domains[domain_key]['name']
        
        sources_section = f"**SOURCES {domain_name.upper()} :**\n\n"
        
        for i, article in enumerate(articles, 1):
            title = article['title']
            if len(title) > 60:
                title = title[:57] + "..."
            sources_section += f"{i}. {article['source']} - \"{title}\"\n"
        
        return sources_section.strip()
    
    def get_domain_distribution(self, articles: List[Dict]) -> Dict:
        """Retourne la distribution des articles par domaine"""
        by_domain = self._organize_articles_by_domain(articles)
        
        distribution = {}
        total = len(articles)
        
        for domain_key, domain_articles in by_domain.items():
            count = len(domain_articles)
            percentage = round((count / total) * 100, 1) if total > 0 else 0
            
            distribution[domain_key] = {
                'name': self.domains[domain_key]['name'],
                'count': count,
                'percentage': percentage,
                'can_generate': count >= 3
            }
        
        return distribution
    
    def generate_article_variations(self, articles: List[Dict], count: int = 1) -> List[Dict]:
        """Interface de compatibilité avec l'ancien système"""
        return self.generate_specialized_posts(articles)