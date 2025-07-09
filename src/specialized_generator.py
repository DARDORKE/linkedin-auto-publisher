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
        self.model_id = "gemini-2.5-pro"
        
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
    
    def generate_domain_post(self, articles: List[Dict], domain: str) -> Dict:
        """Génère un post pour un domaine spécifique à partir d'articles sélectionnés"""
        try:
            # Valider le domaine
            if domain not in self.domains:
                logger.error(f"Invalid domain: {domain}")
                return None
            
            # Vérifier qu'on a au moins 2 articles
            if len(articles) < 2:
                logger.error(f"Not enough articles for generation: {len(articles)}")
                return None
            
            logger.info(f"Generating post for domain {domain} with {len(articles)} articles")
            
            # Utiliser la méthode privée existante
            return self._generate_domain_post(domain, articles)
            
        except Exception as e:
            logger.error(f"Error in generate_domain_post: {e}")
            return None
    
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
        # Utiliser le contenu complet si disponible, sinon le summary
        content = article.get('content', '') or article.get('summary', '')
        text_content = (article['title'] + ' ' + content).lower()
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
    
    def _select_optimal_articles(self, articles: List[Dict], max_count: int = 10) -> List[Dict]:
        """Sélectionne les articles optimaux pour génération de contenu de qualité"""
        if not articles:
            return []
        
        # Score de qualité pour la génération de contenu
        scored_articles = []
        
        for article in articles:
            content_score = 0
            
            # Score de base (pertinence technique)
            content_score += article.get('relevance_score', 0) * 0.6
            
            # Bonus pour diversité des sources
            content_score += self._calculate_source_diversity_bonus(article, articles)
            
            # Bonus pour contenu substantiel
            title_quality = self._evaluate_title_quality(article['title'])
            content_score += title_quality
            
            # Bonus pour résumé informatif
            # Utiliser le contenu complet pour évaluer la qualité
            content = article.get('content', '') or article.get('summary', '')
            summary_quality = self._evaluate_summary_quality(content)
            content_score += summary_quality
            
            # Malus pour redondance technologique
            tech_redundancy = self._calculate_tech_redundancy(article, scored_articles)
            content_score -= tech_redundancy
            
            scored_articles.append({
                **article,
                'content_generation_score': content_score
            })
        
        # Trier par score de génération
        scored_articles.sort(key=lambda x: x['content_generation_score'], reverse=True)
        
        # Sélection finale avec diversité
        selected = []
        used_sources = set()
        covered_technologies = set()
        
        for article in scored_articles:
            if len(selected) >= max_count:
                break
                
            source = article['source']
            
            # Éviter trop d'articles de la même source
            if source in used_sources and len([a for a in selected if a['source'] == source]) >= 2:
                continue
            
            # Privilégier la diversité technologique
            article_techs = self._extract_technologies(article)
            if not article_techs.issubset(covered_technologies):
                selected.append(article)
                used_sources.add(source)
                covered_technologies.update(article_techs)
            elif len(selected) < max_count // 2:  # Autoriser quelques doublons au début
                selected.append(article)
                used_sources.add(source)
        
        return selected[:max_count]
    
    def _calculate_source_diversity_bonus(self, article: Dict, all_articles: List[Dict]) -> float:
        """Calcule un bonus pour la diversité des sources"""
        source = article['source']
        same_source_count = len([a for a in all_articles if a['source'] == source])
        total_articles = len(all_articles)
        
        # Plus la source est rare, plus le bonus est élevé
        rarity_bonus = max(0, 20 - (same_source_count / total_articles) * 40)
        return rarity_bonus
    
    def _evaluate_title_quality(self, title: str) -> float:
        """Évalue la qualité d'un titre pour la génération"""
        score = 0
        
        # Longueur optimale
        length = len(title)
        if 30 <= length <= 80:
            score += 15
        elif 20 <= length <= 100:
            score += 10
        elif length < 15:
            score -= 10
        
        # Présence de mots-clés techniques
        tech_indicators = ['api', 'framework', 'tool', 'new', 'update', 'release', 'feature', 'bug', 'fix', 'performance', 'security']
        for indicator in tech_indicators:
            if indicator.lower() in title.lower():
                score += 3
        
        # Éviter les titres clickbait
        clickbait_words = ['you won\'t believe', 'shocking', 'amazing', 'incredible', 'mind-blowing']
        for word in clickbait_words:
            if word.lower() in title.lower():
                score -= 5
        
        return score
    
    def _evaluate_summary_quality(self, summary: str) -> float:
        """Évalue la qualité d'un résumé"""
        if not summary:
            return 0
        
        score = 0
        length = len(summary)
        
        # Longueur optimale pour résumé
        if 100 <= length <= 400:
            score += 10
        elif 50 <= length <= 500:
            score += 5
        elif length < 30:
            score -= 5
        
        # Présence d'informations techniques
        sentences = summary.split('.')
        if len(sentences) >= 2:
            score += 5
        
        return score
    
    def _calculate_tech_redundancy(self, article: Dict, existing_articles: List[Dict]) -> float:
        """Calcule la redondance technologique"""
        if not existing_articles:
            return 0
        
        article_techs = self._extract_technologies(article)
        
        redundancy = 0
        for existing in existing_articles:
            existing_techs = self._extract_technologies(existing)
            overlap = len(article_techs & existing_techs)
            
            if overlap > 0:
                redundancy += overlap * 2
        
        return min(redundancy, 20)  # Limiter le malus
    
    def _extract_technologies(self, article: Dict) -> set:
        """Extrait les technologies mentionnées dans un article"""
        # Utiliser le contenu complet si disponible
        content = article.get('content', '') or article.get('summary', '')
        text = (article['title'] + ' ' + content).lower()
        technologies = set()
        
        # Technologies communes
        all_techs = []
        for domain_info in self.domains.values():
            all_techs.extend(domain_info['keywords'])
        
        for tech in all_techs:
            if tech.lower() in text:
                technologies.add(tech.lower())
        
        return technologies
    
    def _generate_domain_sources(self, domain_key: str, articles: List[Dict]) -> str:
        """Génère une section sources pour un domaine spécifique avec URLs (legacy)"""
        return self._generate_enhanced_sources(domain_key, articles)
    
    def _generate_domain_post(self, domain_key: str, articles: List[Dict]) -> Dict:
        """Génère un post spécialisé optimisé pour LinkedIn"""
        domain_info = self.domains[domain_key]
        
        # Sélection intelligente des articles pour génération optimale
        top_articles = self._select_optimal_articles(articles, max_count=10)
        
        # Analyser le contexte des articles pour un prompt adaptatif
        article_context = self._analyze_article_context(top_articles, domain_key)
        
        # Créer le prompt optimisé
        prompt = self._create_optimized_prompt(domain_key, domain_info, top_articles, article_context)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            content = response.text
            
            # Post-traitement pour LinkedIn
            optimized_content = self._optimize_for_linkedin(content, domain_key)
            
            # Générer hashtags intelligents
            hashtags_str = self._generate_smart_hashtags(top_articles, domain_key)
            hashtags_list = hashtags_str.split() if hashtags_str else []
            
            # Générer la section sources améliorée
            sources_section = self._generate_enhanced_sources(domain_key, top_articles)
            
            # Combiner tous les éléments
            full_content = optimized_content + "\n\n" + hashtags_str + "\n\n" + sources_section
            
            return {
                'content': full_content,
                'type': f'{domain_key}_specialized',
                'domain': domain_key,
                'domain_name': domain_info['name'],
                'source_articles': top_articles,
                'sources_count': len(set(article['source'] for article in top_articles)),
                'hashtags': hashtags_list,
                'article_context': article_context,
                'generated_at': datetime.now().isoformat()
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
            # Utiliser le contenu complet si disponible
            content = article.get('content', '') or article.get('summary', '')
            text = (article['title'] + ' ' + content).lower()
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
    
    def _analyze_article_context(self, articles: List[Dict], domain_key: str) -> Dict:
        """Analyse le contexte des articles pour adapter le prompt"""
        context = {
            'trending_technologies': [],
            'key_companies': [],
            'article_types': [],
            'urgency_level': 'normal',
            'technical_depth': 'medium',
            'content_insights': [],
            'temporal_context': 'current',
            'key_themes': []
        }
        
        # Analyser les technologies tendances
        tech_mentions = {}
        company_mentions = {}
        theme_mentions = {}
        
        companies = ['google', 'microsoft', 'openai', 'anthropic', 'meta', 'apple', 'amazon', 'netflix', 'uber', 'spotify', 'github', 'docker']
        
        # Thèmes techniques importants
        themes = {
            'performance': ['performance', 'speed', 'optimization', 'faster', 'efficient'],
            'security': ['security', 'vulnerability', 'breach', 'attack', 'protection'],
            'scalability': ['scale', 'scalable', 'scalability', 'distributed', 'microservices'],
            'ai_integration': ['ai', 'ml', 'machine learning', 'artificial intelligence', 'llm'],
            'developer_experience': ['developer experience', 'dx', 'productivity', 'workflow', 'tools'],
            'open_source': ['open source', 'opensource', 'community', 'contribution', 'maintainer']
        }
        
        insights = []
        
        for article in articles:
            # Utiliser le contenu complet si disponible
            content = article.get('content', '') or article.get('summary', '')
            text = (article['title'] + ' ' + content).lower()
            
            # Extraire des insights clés du contenu
            article_insights = self._extract_content_insights(content, article['title'])
            insights.extend(article_insights)
            
            # Technologies
            for tech in self.domains[domain_key]['keywords']:
                if tech.lower() in text:
                    tech_mentions[tech] = tech_mentions.get(tech, 0) + 1
            
            # Entreprises
            for company in companies:
                if company in text:
                    company_mentions[company] = company_mentions.get(company, 0) + 1
            
            # Thèmes
            for theme_name, theme_keywords in themes.items():
                for keyword in theme_keywords:
                    if keyword in text:
                        theme_mentions[theme_name] = theme_mentions.get(theme_name, 0) + 1
            
            # Types d'articles avec plus de nuances
            if any(word in text for word in ['release', 'launch', 'announce', 'introduce']):
                context['article_types'].append('release')
            elif any(word in text for word in ['update', 'upgrade', 'improve', 'enhance']):
                context['article_types'].append('update')
            elif any(word in text for word in ['security', 'vulnerability', 'breach', 'exploit']):
                context['article_types'].append('security')
                context['urgency_level'] = 'high'
            elif any(word in text for word in ['breaking', 'urgent', 'critical', 'emergency']):
                context['urgency_level'] = 'high'
            elif any(word in text for word in ['tutorial', 'guide', 'how-to', 'getting started']):
                context['article_types'].append('educational')
            elif any(word in text for word in ['analysis', 'deep dive', 'investigation']):
                context['article_types'].append('analytical')
        
        # Analyse temporelle
        if any(word in ' '.join([a.get('content', '') + a['title'] for a in articles]).lower() 
               for word in ['today', 'this week', 'breaking', 'just announced']):
            context['temporal_context'] = 'breaking'
        elif any(word in ' '.join([a.get('content', '') + a['title'] for a in articles]).lower() 
                 for word in ['trend', 'evolution', 'future', 'upcoming']):
            context['temporal_context'] = 'trending'
        
        # Compilation des résultats
        context['trending_technologies'] = sorted(tech_mentions.items(), key=lambda x: x[1], reverse=True)[:5]
        context['key_companies'] = sorted(company_mentions.items(), key=lambda x: x[1], reverse=True)[:3]
        context['key_themes'] = sorted(theme_mentions.items(), key=lambda x: x[1], reverse=True)[:4]
        context['content_insights'] = insights[:6]  # Top 6 insights
        
        # Niveau technique basé sur les sources et le contenu
        academic_sources = ['MIT CSAIL News', 'Stanford AI Lab', 'Papers With Code', 'IEEE Spectrum']
        technical_sources = ['Go Dev Blog', 'React Blog', 'Rust Blog', 'Python Official Blog']
        
        if any(article['source'] in academic_sources for article in articles):
            context['technical_depth'] = 'high'
        elif any(article['source'] in technical_sources for article in articles):
            context['technical_depth'] = 'technical'
        elif any(article['source'] in ['TechCrunch', 'VentureBeat'] for article in articles):
            context['technical_depth'] = 'accessible'
        
        return context
    
    def _extract_content_insights(self, content: str, title: str) -> List[str]:
        """Extrait des insights clés du contenu complet"""
        if not content or len(content) < 200:
            return []
        
        insights = []
        
        # Patterns d'insights importants
        insight_patterns = [
            r'(\d+(?:\.\d+)?%)\s+(?:improvement|increase|decrease|faster|slower)',
            r'(?:new|latest|upcoming)\s+([a-zA-Z\s]+(?:version|release|update))',
            r'(?:supports?|introduces?|features?)\s+([a-zA-Z\s]+(?:API|framework|library|tool))',
            r'(?:significantly|dramatically|substantially)\s+([a-zA-Z\s]+)',
            r'(?:compared to|versus|vs\.?)\s+([a-zA-Z\s]+)',
        ]
        
        import re
        
        for pattern in insight_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:2]:  # Max 2 par pattern
                if isinstance(match, tuple):
                    match = ' '.join(match)
                if len(match) > 10 and len(match) < 80:
                    insights.append(match.strip())
        
        return insights[:3]  # Max 3 insights par article
    
    def _create_optimized_prompt(self, domain_key: str, domain_info: Dict, articles: List[Dict], context: Dict) -> str:
        """Crée un prompt optimisé basé sur le contexte des articles"""
        
        # Construction dynamique du résumé des articles
        articles_summary = self._build_contextual_summary(articles, context)
        
        # Technologies tendances pour ce batch
        trending_techs = [tech for tech, _ in context['trending_technologies']]
        tech_focus = ', '.join(trending_techs[:4]) if trending_techs else 'diverses technologies'
        
        # Entreprises clés
        key_companies = [comp for comp, _ in context['key_companies']]
        company_context = f" (notamment {', '.join(key_companies[:2])})" if key_companies else ""
        
        # Thèmes clés
        key_themes = [theme for theme, _ in context['key_themes']]
        themes_context = f"Thèmes dominants: {', '.join(key_themes[:3])}" if key_themes else ""
        
        # Insights du contenu
        content_insights = context.get('content_insights', [])
        insights_context = f"Insights clés: {' • '.join(content_insights[:3])}" if content_insights else ""
        
        # Adapter le ton selon l'urgence et le contexte temporel
        urgency_tone = {
            'high': 'URGENT - ',
            'normal': '',
            'low': ''
        }.get(context['urgency_level'], '')
        
        temporal_indicators = {
            'breaking': '🚨 BREAKING: ',
            'trending': '📈 TRENDING: ',
            'current': ''
        }.get(context.get('temporal_context', 'current'), '')
        
        # Prompts optimisés par domaine
        optimized_prompts = {
            'frontend': f"""
Tu es un expert en développement frontend reconnu sur LinkedIn. Rédige un post engageant sur les dernières actualités frontend.

🎯 CONTEXTE ENRICHI:
• Technologies tendances: {tech_focus}
• Entreprises actives: {', '.join(key_companies) if key_companies else 'écosystème global'}
• {themes_context}
• {insights_context}
• Niveau technique: {context['technical_depth']}
• Urgence: {context['urgency_level']} | Temporalité: {context.get('temporal_context', 'current')}

📰 SOURCES ANALYSÉES ({len(articles)} articles):
{articles_summary}

✅ CONSIGNES LINKEDIN OPTIMISÉES:
1. Ton professionnel mais accessible, adapté aux développeurs frontend
2. Utiliser des émojis de façon stratégique (2-3 maximum)
3. Structure avec des bullet points pour la lisibilité
4. Inclure une question engageante spécifique au contenu analysé
5. Mentionner l'impact concret pour les équipes frontend
6. Citer les sources avec élégance: "selon [Source]"
7. 280-350 mots pour optimiser l'engagement LinkedIn
8. Utiliser les insights extraits pour enrichir le contenu
9. Adapter le ton à la temporalité des news

🏗️ STRUCTURE OPTIMISÉE:
• {temporal_indicators}{urgency_tone}Accroche percutante basée sur les insights réels
• Context: Pourquoi c'est important maintenant (lien avec les thèmes identifiés)
• 🔥 Points clés (2-3 développements majeurs avec extraits concrets)
• 💡 Impact pratique pour les développeurs (basé sur les insights)
• ❓ Question d'engagement spécifique au contenu analysé

📝 STYLE LINKEDIN ADAPTATIF:
- Phrases courtes et percutantes
- Utiliser les insights extraits pour donner des exemples concrets
- Ton informatif mais enthousiasmant
- Focus sur la valeur ajoutée pour la communauté dev
- Adapter l'urgence du ton selon le contexte temporel

🎯 ÉLÉMENTS À INTÉGRER:
- Utiliser les insights extraits comme exemples concrets
- Mentionner les thèmes dominants identifiés
- Adapter le call-to-action selon le type d'articles analysés

Rédige le post LinkedIn frontend optimisé:
""",
            
            'backend': f"""
Tu es un architecte backend senior influent sur LinkedIn. Crée un post captivant sur l'actualité backend/infrastructure.

🎯 CONTEXTE TECHNIQUE ENRICHI:
• Technologies phares: {tech_focus}
• Acteurs majeurs: {', '.join(key_companies) if key_companies else 'écosystème complet'}{company_context}
• {themes_context}
• {insights_context}
• Complexité: {context['technical_depth']}
• Priorité: {context['urgency_level']} | Temporalité: {context.get('temporal_context', 'current')}

📊 SOURCES ANALYSÉES ({len(articles)} articles):
{articles_summary}

✅ CONSIGNES LINKEDIN PRO OPTIMISÉES:
1. Expertise technique mais accessible aux lead devs
2. Émojis techniques pertinents (⚡🔧🚀) avec parcimonie
3. Structure claire avec sections définies
4. Angle "impact business" pour toucher les décideurs
5. Implications concrètes pour l'architecture et les équipes
6. Citations élégantes: "d'après [Source]" ou "selon [Source]"
7. 300-380 mots pour maximiser l'engagement professionnel
8. Utiliser les insights extraits pour donner des métriques/exemples concrets
9. Adapter le ton à l'urgence et la temporalité des développements

🏛️ ARCHITECTURE DU POST:
• {temporal_indicators}{urgency_tone}Hook technique percutant basé sur les insights réels
• Contexte: Enjeux actuels pour les équipes backend (lien avec thèmes identifiés)
• ⚡ Développements clés (2-3 points avec impact technique et métriques)
• 🔧 Implications pratiques (performance, scalabilité, sécurité) avec exemples concrets
• 💭 Question stratégique spécifique au contenu analysé

📈 ANGLE LINKEDIN ADAPTATIF:
- Vocabulaire technique précis mais accessible
- Focus sur ROI et impact métier avec données concrètes
- Ton d'expert consultant adapté à la temporalité
- Valeur actionnable pour les professionnels
- Utiliser les insights pour donner des exemples chiffrés

🎯 ÉLÉMENTS TECHNIQUES À INTÉGRER:
- Utiliser les insights extraits pour donner des métriques de performance
- Mentionner les thèmes dominants avec implications architecturales
- Adapter le niveau d'urgence selon le contexte temporel
- Inclure des implications concrètes pour les équipes

Crée le post LinkedIn backend expert:
""",
            
            'ai': f"""
Tu es un expert IA/ML reconnu sur LinkedIn. Compose un post viral sur l'actualité intelligence artificielle.

🧠 CONTEXTE:
• Technologies IA: {tech_focus}
• Leaders du secteur: {', '.join(key_companies) if key_companies else 'écosystème IA global'}
• Niveau: {context['technical_depth']}
• Impact: {context['urgency_level']}

🤖 SOURCES EXPERT ({len(articles)} articles):
{articles_summary}

✅ OPTIMISATION LINKEDIN IA:
1. Ton visionnaire mais ancré dans le réel
2. Émojis IA stratégiques (🤖🧠⚡) pour l'identité visuelle
3. Structure narrative captivante
4. Équilibre technique/business pour audience mixte
5. Impact sur l'industrie ET les développeurs
6. Sources crédibles: "selon [Source]" avec autorité
7. 320-400 mots pour contenu premium IA
8. Éviter le hype, privilégier les faits

🚀 BLUEPRINT VIRAL:
• {urgency_tone}Accroche disruptive (évolution majeure + émoji)
• Vision: Ce que ça change pour l'industrie tech
• 🧠 Innovations clés (2-3 avancées concrètes)
• 💼 Impact métier (productivité, nouveaux usages)
• 🔮 Question prospective pour générer l'engagement

🎯 STYLE THOUGHT LEADER:
- Vocabulaire IA précis sans être hermétique
- Perspective industrie + implications pratiques
- Ton d'expert consultant en transformation
- Contenu référence pour la communauté IA

Produis le post LinkedIn IA thought leader:
""",
            
            'general': f"""
Tu es un tech leader influent sur LinkedIn. Crée un post engageant sur les tendances tech transversales.

💡 CONTEXTE MULTI-DOMAINES:
• Technologies émergentes: {tech_focus}
• Écosystème: {', '.join(key_companies) if key_companies else 'industrie tech globale'}
• Audience: {context['technical_depth']} (mixed technical/business)
• Momentum: {context['urgency_level']}

📡 SOURCES DIVERSIFIÉES ({len(articles)} articles):
{articles_summary}

✅ STRATÉGIE LINKEDIN CROSS-TECH:
1. Ton de tech leader accessible à tous profils
2. Émojis universels tech (💻🚀⚡) pour large audience
3. Structure claire pour professionnels occupés
4. Angle transformation digitale et innovation
5. Impact sur l'écosystème tech global
6. Crédibilité: "selon [Source]" avec expertise
7. 300-370 mots pour engagement optimal cross-audience
8. Vision holistique de l'évolution tech

🌟 TEMPLATE CROSS-IMPACT:
• {urgency_tone}Vision macro (tendance industry-wide)
• Contexte: Pourquoi c'est un tournant pour la tech
• 🚀 Évolutions marquantes (2-3 développements transversaux)
• 💼 Impact écosystème (startups, scale-ups, enterprise)
• 🤔 Question stratégique pour tous les profils tech

🎪 POSITIONNEMENT THOUGHT LEADER:
- Perspective 360° sur l'innovation tech
- Ton de guide pour les décisions stratégiques
- Contenu fédérateur pour la communauté tech
- Valeur ajoutée pour tous les métiers du numérique

Crée le post LinkedIn tech leader:
"""
        }
        
        return optimized_prompts.get(domain_key, optimized_prompts['general'])
    
    def _build_contextual_summary(self, articles: List[Dict], context: Dict) -> str:
        """Construit un résumé contextuel enrichi des articles avec LLM"""
        summary_lines = []
        
        # Générer tous les summaries en une fois pour optimiser les performances
        articles_with_summaries = self._generate_batch_summaries(articles)
        
        for i, article in enumerate(articles_with_summaries, 1):
            source = article['source']
            title = article['title']
            
            # Raccourcir le titre si nécessaire
            if len(title) > 70:
                title = title[:67] + "..."
            
            # Utiliser le summary AI généré
            ai_summary = article.get('ai_summary', '')
            
            # Ajouter des indicateurs de contexte améliorés
            indicators = []
            content = article.get('content', '') or article.get('summary', '')
            text = (title + ' ' + content).lower()
            
            if any(word in text for word in ['release', 'launch', 'announce']):
                indicators.append('🚀')
            elif any(word in text for word in ['update', 'security', 'vulnerability']):
                indicators.append('🔒')
            elif any(word in text for word in ['performance', 'speed', 'optimization']):
                indicators.append('⚡')
            elif any(word in text for word in ['breaking', 'urgent', 'critical']):
                indicators.append('🚨')
            elif any(word in text for word in ['tutorial', 'guide', 'how-to']):
                indicators.append('📚')
            
            indicator = ''.join(indicators[:1])  # Max 1 emoji
            
            # Format enrichi avec summary AI
            base_line = f"{i}. {indicator} {source}: \"{title}\""
            if ai_summary and len(ai_summary) > 20:
                base_line += f"\n   → {ai_summary}"
            
            summary_lines.append(base_line)
        
        return "\n".join(summary_lines)
    
    def _generate_batch_summaries(self, articles: List[Dict]) -> List[Dict]:
        """Génère des summaries pour tous les articles de manière optimisée"""
        enhanced_articles = []
        
        for article in articles:
            enhanced_article = article.copy()
            
            # Générer le summary AI
            content = article.get('content', '') or article.get('summary', '')
            ai_summary = self._generate_article_summary(content, article['title'], article['source'])
            enhanced_article['ai_summary'] = ai_summary
            
            enhanced_articles.append(enhanced_article)
            
            # Log du progrès
            logger.info(f"Generated summary for: {article['title'][:50]}...")
        
        return enhanced_articles
    
    def _generate_article_summary(self, content: str, title: str, source: str) -> str:
        """Génère un résumé intelligent d'un article avec le LLM"""
        if not content or len(content) < 100:
            return ""
        
        try:
            # Limiter le contenu pour éviter des coûts excessifs
            limited_content = content[:3000] if len(content) > 3000 else content
            
            summary_prompt = f"""
Analyse cet article technique et génère un résumé de 1-2 phrases (max 120 caractères) qui capture l'essentiel pour un développeur.

ARTICLE: "{title}"
SOURCE: {source}
CONTENU: {limited_content}

CONSIGNES:
- 1-2 phrases maximum
- Focus sur l'impact technique concret
- Langage accessible aux développeurs
- Éviter le jargon marketing
- Mettre l'accent sur ce qui change concrètement

RÉSUMÉ:"""

            response = self.client.models.generate_content(
                model=self.model_id,
                contents=summary_prompt
            )
            
            summary = response.text.strip()
            
            # Nettoyer et limiter la taille
            if len(summary) > 120:
                summary = summary[:117] + "..."
            
            # Supprimer les guillemets et autres caractères indésirables
            summary = summary.replace('"', '').replace('«', '').replace('»', '').strip()
            
            return summary
            
        except Exception as e:
            logger.debug(f"Error generating summary for article: {e}")
            # Fallback vers l'extraction manuelle
            return self._extract_key_excerpt(content, title)
    
    def _extract_key_excerpt(self, content: str, title: str) -> str:
        """Extrait un extrait clé pertinent du contenu"""
        if not content or len(content) < 100:
            return ""
        
        # Diviser en phrases
        sentences = content.split('.')
        key_sentences = []
        
        # Mots-clés indicateurs d'importance
        importance_keywords = [
            'announce', 'release', 'launch', 'introduce', 'new', 'update',
            'improve', 'performance', 'security', 'feature', 'version',
            'significant', 'major', 'important', 'breakthrough', 'innovative'
        ]
        
        for sentence in sentences[:10]:  # Examiner les 10 premières phrases
            sentence = sentence.strip()
            if len(sentence) > 30 and len(sentence) < 150:
                # Scorer la pertinence
                score = 0
                sentence_lower = sentence.lower()
                
                # Bonus pour mots-clés d'importance
                for keyword in importance_keywords:
                    if keyword in sentence_lower:
                        score += 2
                
                # Bonus pour contenu technique
                if any(word in sentence_lower for word in ['api', 'framework', 'library', 'tool', 'platform']):
                    score += 1
                
                # Éviter les phrases trop génériques
                if any(word in sentence_lower for word in ['according to', 'in conclusion', 'furthermore']):
                    score -= 1
                
                if score > 0:
                    key_sentences.append((sentence, score))
        
        if key_sentences:
            # Retourner la phrase avec le meilleur score
            best_sentence = max(key_sentences, key=lambda x: x[1])[0]
            # Nettoyer et raccourcir si nécessaire
            if len(best_sentence) > 120:
                best_sentence = best_sentence[:117] + "..."
            return best_sentence
        
        return ""
    
    def _optimize_for_linkedin(self, content: str, domain_key: str) -> str:
        """Optimise le contenu pour LinkedIn"""
        # Nettoyage de base
        optimized = content.strip()
        
        # Ajouter des sauts de ligne pour la lisibilité LinkedIn
        # Remplacer les longs paragraphes par des sections plus courtes
        paragraphs = optimized.split('\n\n')
        readable_paragraphs = []
        
        for paragraph in paragraphs:
            if len(paragraph) > 300:  # Paragraphe trop long
                # Diviser aux phrases
                sentences = paragraph.split('. ')
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk + sentence) < 200:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            readable_paragraphs.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                
                if current_chunk:
                    readable_paragraphs.append(current_chunk.strip())
            else:
                readable_paragraphs.append(paragraph)
        
        return "\n\n".join(readable_paragraphs)
    
    def _generate_smart_hashtags(self, articles: List[Dict], domain_key: str) -> str:
        """Génère des hashtags intelligents basés sur le contenu"""
        hashtags = set()
        
        # Hashtags de base par domaine
        base_hashtags = {
            'frontend': ['#Frontend', '#JavaScript', '#WebDev', '#React', '#CSS'],
            'backend': ['#Backend', '#API', '#DevOps', '#CloudComputing', '#Microservices'],
            'ai': ['#AI', '#MachineLearning', '#DeepLearning', '#LLM', '#Innovation'],
            'general': ['#Tech', '#Development', '#Innovation', '#DigitalTransformation']
        }
        
        hashtags.update(base_hashtags.get(domain_key, base_hashtags['general'])[:3])
        
        # Hashtags dynamiques basés sur les technologies mentionnées
        tech_hashtags = {
            'react': '#React', 'vue': '#VueJS', 'angular': '#Angular',
            'nodejs': '#NodeJS', 'python': '#Python', 'go': '#Golang',
            'rust': '#RustLang', 'typescript': '#TypeScript',
            'kubernetes': '#Kubernetes', 'docker': '#Docker',
            'openai': '#OpenAI', 'anthropic': '#Anthropic',
            'security': '#CyberSecurity', 'performance': '#Performance'
        }
        
        for article in articles:
            # Utiliser le contenu complet si disponible
            content = article.get('content', '') or article.get('summary', '')
            text = (article['title'] + ' ' + content).lower()
            for tech, hashtag in tech_hashtags.items():
                if tech in text and len(hashtags) < 8:
                    hashtags.add(hashtag)
        
        # Hashtags trending/génériques
        trending = ['#TechNews', '#DeveloperCommunity', '#SoftwareEngineering']
        for tag in trending:
            if len(hashtags) < 10:
                hashtags.add(tag)
            else:
                break
        
        return ' '.join(sorted(list(hashtags)[:8]))  # Max 8 hashtags
    
    def _generate_enhanced_sources(self, domain_key: str, articles: List[Dict]) -> str:
        """Génère une section sources optimisée pour LinkedIn"""
        domain_name = self.domains[domain_key]['name']
        
        # Header plus engageant
        sources_header = f"📚 **SOURCES {domain_name.upper()} ANALYSÉES**\n"
        
        # Regrouper par type de source pour plus de clarté
        source_groups = {
            'Officielles': [],
            'Académiques': [],
            'Médias Tech': [],
            'Communauté': []
        }
        
        # Classification des sources
        official_sources = {'React Blog', 'Node.js Blog', 'Go Dev Blog', 'Rust Blog', 'OpenAI Blog', 'Google AI Blog'}
        academic_sources = {'MIT CSAIL News', 'Stanford AI Lab', 'IEEE Spectrum', 'Papers With Code'}
        tech_media = {'TechCrunch', 'Ars Technica', 'MIT Technology Review', 'VentureBeat'}
        
        for article in articles:
            source = article['source']
            title = article['title']
            url = article.get('url', '')
            
            # Raccourcir le titre
            if len(title) > 50:
                title = title[:47] + "..."
            
            source_info = {'source': source, 'title': title, 'url': url}
            
            if source in official_sources:
                source_groups['Officielles'].append(source_info)
            elif source in academic_sources:
                source_groups['Académiques'].append(source_info)
            elif source in tech_media:
                source_groups['Médias Tech'].append(source_info)
            else:
                source_groups['Communauté'].append(source_info)
        
        # Construire la section optimisée
        sources_section = sources_header + "\n"
        
        for group_name, group_articles in source_groups.items():
            if group_articles:
                # Icônes par type
                icons = {
                    'Officielles': '🏢',
                    'Académiques': '🎓', 
                    'Médias Tech': '📰',
                    'Communauté': '👥'
                }
                
                sources_section += f"{icons[group_name]} **{group_name}:**\n"
                
                for i, article_info in enumerate(group_articles[:3], 1):  # Max 3 par groupe
                    source = article_info['source']
                    title = article_info['title']
                    url = article_info['url']
                    
                    if url:
                        sources_section += f"• [{source}]({url}) - {title}\n"
                    else:
                        sources_section += f"• **{source}** - {title}\n"
                
                sources_section += "\n"
        
        # Footer avec métadonnées
        total_sources = len(set(article['source'] for article in articles))
        sources_section += f"_Analyse basée sur {len(articles)} articles de {total_sources} sources fiables_"
        
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