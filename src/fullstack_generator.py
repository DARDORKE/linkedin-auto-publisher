from google import genai
from typing import List, Dict
import os
from loguru import logger
import json
from datetime import datetime

class FullStackPostGenerator:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"
        
    def generate_tech_synthesis(self, articles: List[Dict]) -> Dict:
        """Génère une synthèse technologique complète : Frontend + Backend + IA"""
        
        if not articles:
            return None
            
        # Organiser les articles par domaine
        by_domain = self._organize_by_domain(articles)
        trending_tech = self._get_trending_technologies(articles)
        
        # Créer le prompt complet
        prompt = self._create_fullstack_prompt(by_domain, trending_tech, articles[:20])
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            content = response.text
            
            # Générer la section sources
            sources_section = self._generate_comprehensive_sources(articles[:20])
            
            # Combiner l'article et les sources
            full_content = content + "\n\n" + sources_section
            
            return {
                'content': full_content,
                'type': 'fullstack_synthesis',
                'source_articles': articles[:20],
                'domains_covered': list(by_domain.keys()),
                'sources_count': len(set(article['source'] for article in articles[:20])),
                'trending_tech': trending_tech,
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error generating fullstack post: {e}")
            return None
    
    def _organize_by_domain(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Organise les articles par domaine technologique"""
        domains = {'frontend': [], 'backend': [], 'ai': [], 'devtools': [], 'multi': []}
        
        for article in articles:
            relevant_domains = article.get('relevant_domains', [])
            category = article.get('category', 'general')
            
            if len(relevant_domains) > 1:
                domains['multi'].append(article)
            elif 'ai' in relevant_domains or category == 'ai':
                domains['ai'].append(article)
            elif 'backend' in relevant_domains or category == 'backend':
                domains['backend'].append(article)
            elif 'frontend' in relevant_domains or category == 'frontend':
                domains['frontend'].append(article)
            elif category in ['devtools', 'enterprise', 'devops']:
                domains['devtools'].append(article)
            else:
                domains['multi'].append(article)
                
        return {k: v for k, v in domains.items() if v}  # Supprimer les domaines vides
    
    def _get_trending_technologies(self, articles: List[Dict]) -> Dict[str, List[str]]:
        """Extrait les technologies tendances par domaine"""
        tech_keywords = {
            'frontend': ['react', 'vue', 'angular', 'svelte', 'nextjs', 'typescript', 'css', 'html', 'webcomponents'],
            'backend': ['nodejs', 'python', 'go', 'rust', 'java', 'django', 'fastapi', 'spring', 'kubernetes', 'docker'],
            'ai': ['llm', 'gpt', 'claude', 'gemini', 'pytorch', 'tensorflow', 'transformers', 'langchain', 'openai']
        }
        
        domain_trends = {}
        
        for domain, keywords in tech_keywords.items():
            tech_mentions = {}
            
            for article in articles:
                text = (article['title'] + ' ' + article.get('summary', '')).lower()
                domains = article.get('relevant_domains', [])
                
                if domain in domains or domain in article.get('domains', []):
                    for tech in keywords:
                        if tech in text:
                            score = article.get('relevance_score', 1)
                            tech_mentions[tech] = tech_mentions.get(tech, 0) + score
            
            # Top 5 par domaine
            sorted_techs = sorted(tech_mentions.items(), key=lambda x: x[1], reverse=True)[:5]
            domain_trends[domain] = [tech for tech, _ in sorted_techs]
            
        return domain_trends
    
    def _create_fullstack_prompt(self, by_domain: Dict, trending_tech: Dict, articles: List[Dict]) -> str:
        """Prompt complet pour couvrir frontend, backend et IA"""
        
        sources_summary = self._build_domain_sources_summary(by_domain, articles)
        domain_analysis = self._build_comprehensive_analysis(by_domain, trending_tech)
        
        prompt = f"""
Tu es un journaliste spécialisé en technologies de développement. Rédige un article de synthèse couvrant les trois piliers du développement moderne : Frontend, Backend et Intelligence Artificielle.

SOURCES ANALYSÉES ({len(articles)} articles):
{sources_summary}

ANALYSE PAR DOMAINE:
{domain_analysis}

TECHNOLOGIES TENDANCES:
• Frontend: {', '.join(trending_tech.get('frontend', [])[:5])}
• Backend: {', '.join(trending_tech.get('backend', [])[:5])}
• IA: {', '.join(trending_tech.get('ai', [])[:5])}

CONSIGNES STRICTES:
1. Ton journalistique professionnel et factuel
2. Couvrir ÉQUITABLEMENT les trois domaines : Frontend, Backend, IA
3. Structure en pyramide inversée avec analyse transversale
4. Citer systématiquement les sources : (Source)
5. Focus sur l'impact pour les développeurs
6. Longueur: 500-600 mots
7. Aucune opinion, seulement des faits

STRUCTURE OBLIGATOIRE:
- Titre évoquant l'écosystème de développement complet
- Lead: 2-3 tendances majeures touchant les trois domaines
- Section Frontend: frameworks, outils, standards web
- Section Backend: langages, architectures, infrastructure
- Section IA: modèles, intégrations, outils pour développeurs
- Conclusion: convergence et implications pour l'écosystème dev

STYLE TECHNIQUE:
- Terminologie précise mais accessible
- Exemples concrets de technologies
- Implications pratiques pour les équipes de développement
- Éviter le jargon marketing
- Transitions fluides entre domaines

NE PAS inclure de section sources - elle sera ajoutée automatiquement.

Rédige l'article de synthèse technologique complète:
"""
        
        return prompt
    
    def _build_domain_sources_summary(self, by_domain: Dict, articles: List[Dict]) -> str:
        """Résumé des sources organisé par domaine"""
        summary_lines = []
        
        domain_names = {
            'frontend': '[Frontend]',
            'backend': '[Backend]',
            'ai': '[IA]',
            'devtools': '[DevTools]',
            'multi': '[Multi-domaines]'
        }
        
        for i, article in enumerate(articles, 1):
            source = article.get('source', 'Source inconnue')
            title = article.get('title', 'Titre indisponible')
            
            # Déterminer le domaine principal
            domains = article.get('relevant_domains', [])
            category = article.get('category', 'general')
            
            if len(domains) > 1:
                domain_label = '[Multi]'
            elif 'ai' in domains or category == 'ai':
                domain_label = '[IA]'
            elif 'backend' in domains or category == 'backend':
                domain_label = '[Backend]'
            elif 'frontend' in domains or category == 'frontend':
                domain_label = '[Frontend]'
            else:
                domain_label = '[Dev]'
            
            if len(title) > 65:
                title = title[:62] + "..."
            
            summary_lines.append(f"{i}. {source} {domain_label}: \"{title}\"")
        
        return "\n".join(summary_lines)
    
    def _build_comprehensive_analysis(self, by_domain: Dict, trending_tech: Dict) -> str:
        """Analyse complète par domaine"""
        domain_names = {
            'frontend': 'Développement Frontend',
            'backend': 'Développement Backend',
            'ai': 'Intelligence Artificielle',
            'devtools': 'Outils de Développement',
            'multi': 'Approches Multi-domaines'
        }
        
        analysis_lines = []
        
        for domain, articles in by_domain.items():
            domain_name = domain_names.get(domain, domain.title())
            count = len(articles)
            
            if count > 0:
                analysis_lines.append(f"• {domain_name}: {count} article(s)")
                
                # Extraire les technologies mentionnées
                technologies = set()
                for article in articles[:3]:
                    text = (article['title'] + ' ' + article.get('summary', '')).lower()
                    
                    # Technologies spécifiques par domaine
                    if domain == 'frontend':
                        techs = ['react', 'vue', 'angular', 'svelte', 'nextjs', 'typescript', 'css', 'html']
                    elif domain == 'backend':
                        techs = ['nodejs', 'python', 'go', 'rust', 'java', 'kubernetes', 'docker', 'api']
                    elif domain == 'ai':
                        techs = ['llm', 'gpt', 'claude', 'pytorch', 'tensorflow', 'openai', 'anthropic']
                    else:
                        techs = ['git', 'github', 'docker', 'ci/cd', 'testing']
                    
                    for tech in techs:
                        if tech in text:
                            technologies.add(tech.capitalize())
                
                if technologies:
                    analysis_lines.append(f"  Technologies: {', '.join(list(technologies)[:4])}")
        
        return "\n".join(analysis_lines)
    
    def _generate_comprehensive_sources(self, articles: List[Dict]) -> str:
        """Section sources complète organisée par domaine"""
        sources_by_domain = {}
        
        for article in articles:
            # Déterminer le domaine principal
            domains = article.get('relevant_domains', [])
            category = article.get('category', 'general')
            
            if len(domains) > 1:
                domain = 'multi-domaines'
            elif 'ai' in domains or category == 'ai':
                domain = 'ai'
            elif 'backend' in domains or category == 'backend':
                domain = 'backend'
            elif 'frontend' in domains or category == 'frontend':
                domain = 'frontend'
            elif category in ['devtools', 'enterprise', 'devops']:
                domain = 'devtools'
            else:
                domain = 'general'
            
            if domain not in sources_by_domain:
                sources_by_domain[domain] = []
            
            sources_by_domain[domain].append({
                'source': article['source'],
                'title': article['title'],
                'url': article['url']
            })
        
        # Construire la section sources
        sources_section = "**SOURCES :**\n\n"
        
        domain_names = {
            'frontend': 'Développement Frontend',
            'backend': 'Développement Backend',
            'ai': 'Intelligence Artificielle',
            'devtools': 'Outils & Infrastructure',
            'multi-domaines': 'Approches Transversales',
            'general': 'Actualités Générales'
        }
        
        # Ordre de priorité pour l'affichage
        domain_order = ['frontend', 'backend', 'ai', 'devtools', 'multi-domaines', 'general']
        
        for domain in domain_order:
            if domain in sources_by_domain:
                sources = sources_by_domain[domain]
                if sources:
                    domain_name = domain_names.get(domain, domain.title())
                    sources_section += f"**{domain_name} :**\n"
                    
                    for i, source in enumerate(sources[:4], 1):  # Max 4 sources par domaine
                        title = source['title']
                        if len(title) > 55:
                            title = title[:52] + "..."
                        sources_section += f"{i}. {source['source']} - \"{title}\"\n"
                    
                    sources_section += "\n"
        
        return sources_section.strip()
    
    def generate_article_variations(self, articles: List[Dict], count: int = 1) -> List[Dict]:
        """Génère une synthèse fullstack (compatibilité)"""
        variations = []
        
        article = self.generate_tech_synthesis(articles)
        if article:
            article['variation_index'] = 1
            variations.append(article)
        
        return variations
    
    def get_domain_statistics(self, articles: List[Dict]) -> Dict:
        """Statistiques de répartition par domaine"""
        by_domain = self._organize_by_domain(articles)
        
        stats = {}
        total = len(articles)
        
        for domain, domain_articles in by_domain.items():
            count = len(domain_articles)
            percentage = round((count / total) * 100, 1) if total > 0 else 0
            
            stats[domain] = {
                'count': count,
                'percentage': percentage,
                'top_sources': list(set(a['source'] for a in domain_articles[:3]))
            }
        
        return stats