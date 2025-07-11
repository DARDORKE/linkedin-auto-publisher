from google import genai
from typing import List, Dict, Any
import os
from loguru import logger
import json
from datetime import datetime
import random
from .post_style_variations import PostStyleVariations

class SpecializedPostGenerator:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-pro"
        
        # WebSocket session pour le suivi des progrès
        self.websocket_session_id = None
        self.websocket_service = None
        
        # Initialiser le gestionnaire de variations de style
        self.style_variations = PostStyleVariations()
        
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
    
    def set_websocket_session(self, session_id: str, websocket_service) -> None:
        """Configure la session WebSocket pour le suivi des progrès"""
        self.websocket_session_id = session_id
        self.websocket_service = websocket_service
    
    def _emit_progress(self, progress_data: Dict[str, Any]) -> None:
        """Émet un événement de progression via WebSocket"""
        if self.websocket_service and self.websocket_session_id:
            try:
                self.websocket_service.update_generation_progress(self.websocket_session_id, progress_data)
            except Exception as e:
                logger.debug(f"Error emitting progress: {e}")
        
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
            
            self._emit_progress({
                'type': 'generation_started',
                'domain': domain,
                'articles_count': len(articles)
            })
            
            # Utiliser la méthode privée existante
            result = self._generate_domain_post(domain, articles)
            
            if result:
                self._emit_progress({
                    'type': 'generation_completed',
                    'domain': domain,
                    'post_generated': True
                })
            else:
                self._emit_progress({
                    'type': 'generation_failed',
                    'domain': domain,
                    'error': 'Failed to generate post'
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in generate_domain_post: {e}")
            self._emit_progress({
                'type': 'generation_error',
                'domain': domain,
                'error': str(e)
            })
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
            
            # Score de base - Utiliser le nouveau quality_score si disponible
            base_score = article.get('quality_score', article.get('relevance_score', 0))
            content_score += base_score * 0.7  # Poids principal sur la qualité
            
            # Bonus pour diversité des sources
            content_score += self._calculate_source_diversity_bonus(article, articles)
            
            # Bonus pour contenu substantiel
            title_quality = self._evaluate_title_quality(article['title'])
            content_score += title_quality
            
            # Bonus pour résumé informatif
            # Utiliser le contenu complet pour évaluer la qualité
            content = article.get('content', '') or article.get('summary', '')
            content_quality = self._evaluate_content_quality_enhanced(content, article)
            content_score += content_quality
            
            # Bonus pour nouveauté/fraîcheur
            novelty_bonus = self._calculate_novelty_bonus(article)
            content_score += novelty_bonus
            
            # Bonus pour métadonnées de qualité (du nouveau système)
            metadata_bonus = self._calculate_metadata_bonus(article)
            content_score += metadata_bonus
            
            # Malus pour redondance technologique
            tech_redundancy = self._calculate_tech_redundancy(article, scored_articles)
            content_score -= tech_redundancy
            
            scored_articles.append({
                **article,
                'content_generation_score': content_score
            })
        
        # Trier par score de génération
        scored_articles.sort(key=lambda x: x['content_generation_score'], reverse=True)
        
        # Sélection finale avec diversité technologique améliorée
        selected = []
        used_sources = set()
        covered_technologies = set()
        selected_domains = set()
        
        for article in scored_articles:
            if len(selected) >= max_count:
                break
                
            source = article.get('source', article.get('source_name', 'Unknown'))
            
            # Éviter trop d'articles de la même source
            if source in used_sources and len([a for a in selected if a.get('source', a.get('source_name', '')) == source]) >= 2:
                continue
            
            # Privilégier la diversité technologique
            article_techs = self._extract_technologies_enhanced(article)
            article_domain = article.get('technology', article.get('domain', 'general'))
            
            # Critères de sélection améliorés
            tech_overlap = len(article_techs & covered_technologies)
            domain_count = len([a for a in selected if a.get('technology', a.get('domain', 'general')) == article_domain])
            
            # Conditions de sélection
            should_select = False
            
            if len(selected) < max_count // 3:
                # Premiers articles : moins strict
                should_select = True
            elif tech_overlap == 0:
                # Nouvelle technologie : priorité
                should_select = True
            elif domain_count < 2:
                # Diversité des domaines techniques
                should_select = True
            elif len(selected) < max_count * 0.8 and tech_overlap <= 1:
                # Phase intermédiaire : tolérer un peu de redondance
                should_select = True
            
            if should_select:
                selected.append(article)
                used_sources.add(source)
                covered_technologies.update(article_techs)
                selected_domains.add(article_domain)
        
        # Log de la sélection finale
        logger.info(f"Selected {len(selected)} articles from {len(scored_articles)} candidates")
        logger.info(f"Technologies covered: {covered_technologies}")
        logger.info(f"Domains covered: {selected_domains}")
        
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
    
    def _extract_technologies_enhanced(self, article: Dict) -> set:
        """Version améliorée de l'extraction de technologies"""
        # Utiliser les métadonnées si disponibles
        detected_techs = article.get('metadata', {}).get('technologies', [])
        if detected_techs:
            return set(tech.lower() for tech in detected_techs)
        
        # Fallback vers l'ancienne méthode
        return self._extract_technologies(article)
    
    def _evaluate_content_quality_enhanced(self, content: str, article: Dict) -> float:
        """Évaluation améliorée de la qualité du contenu"""
        if not content:
            return 0
        
        score = 0
        
        # Score de base selon la longueur
        length = len(content)
        if 500 <= length <= 3000:
            score += 20  # Longueur optimale
        elif 200 <= length <= 5000:
            score += 15
        elif length < 100:
            score -= 10
        
        # Bonus pour extraction de qualité
        extraction_quality = article.get('metadata', {}).get('extraction_quality', 'unknown')
        if extraction_quality == 'full':
            score += 15
        elif extraction_quality == 'summary_only':
            score += 5
        elif extraction_quality == 'error':
            score -= 5
        
        # Bonus pour présence de code/exemples
        if any(pattern in content for pattern in ['```', '<code>', 'function ', 'class ', '```']):
            score += 10
        
        # Bonus pour structure (listes, headers)
        if any(pattern in content for pattern in ['* ', '- ', '1. ', '2. ', '## ', '### ']):
            score += 8
        
        # Bonus pour mots-clés techniques avancés
        technical_keywords = [
            'implementation', 'architecture', 'performance', 'optimization',
            'security', 'scalability', 'algorithm', 'framework', 'api'
        ]
        tech_count = sum(1 for keyword in technical_keywords if keyword in content.lower())
        score += min(tech_count * 2, 10)
        
        return score
    
    def _calculate_novelty_bonus(self, article: Dict) -> float:
        """Calcule un bonus basé sur la nouveauté de l'article"""
        score = 0
        
        # Utiliser les métadonnées de fraîcheur si disponibles
        freshness = article.get('metadata', {}).get('freshness', 'unknown')
        freshness_scores = {
            'hot': 15,      # < 6h
            'fresh': 12,    # < 24h
            'recent': 8,    # < 48h
            'relevant': 5,  # < 72h
            'older': 2,     # > 72h
            'unknown': 0
        }
        score += freshness_scores.get(freshness, 0)
        
        # Bonus pour score de nouveauté du nouveau système
        score_breakdown = article.get('score_breakdown', {})
        novelty_factor = score_breakdown.get('novelty_factor', 0)
        score += novelty_factor * 20  # Convertir en bonus
        
        # Patterns de nouveauté dans le titre
        title = article.get('title', '').lower()
        novelty_patterns = [
            'release', 'launch', 'announce', 'introduce', 'new', 'latest',
            'update', 'version', 'breaking', 'just released'
        ]
        for pattern in novelty_patterns:
            if pattern in title:
                score += 3
                
        return min(score, 25)  # Cap à 25 points
    
    def _calculate_metadata_bonus(self, article: Dict) -> float:
        """Calcule un bonus basé sur les métadonnées de qualité"""
        score = 0
        metadata = article.get('metadata', {})
        
        # Bonus pour nombre de technologies détectées
        tech_count = len(metadata.get('technologies', []))
        score += min(tech_count * 2, 10)
        
        # Bonus pour tags pertinents
        tags_count = len(article.get('tags', []))
        score += min(tags_count, 5)
        
        # Bonus pour score de qualité élevé
        quality_score = article.get('quality_score', 0)
        if quality_score > 80:
            score += 15
        elif quality_score > 60:
            score += 10
        elif quality_score > 40:
            score += 5
        
        # Bonus pour technologie spécialisée
        technology = article.get('technology', 'general')
        if technology != 'general':
            score += 8
        
        return score
    
    def _generate_domain_post(self, domain_key: str, articles: List[Dict]) -> Dict:
        """Génère un post spécialisé optimisé pour LinkedIn"""
        domain_info = self.domains[domain_key]
        
        # Sélection intelligente des articles pour génération optimale
        self._emit_progress({
            'type': 'step_completed',
            'step': 'Sélection des articles',
            'domain': domain_key,
            'percentage': 20
        })
        top_articles = self._select_optimal_articles(articles, max_count=10)
        
        # Analyser le contexte des articles pour un prompt adaptatif
        self._emit_progress({
            'type': 'step_completed',
            'step': 'Analyse du contexte',
            'domain': domain_key,
            'percentage': 35
        })
        article_context = self._analyze_article_context(top_articles, domain_key)
        
        # Créer le prompt optimisé
        self._emit_progress({
            'type': 'step_completed',
            'step': 'Préparation du prompt',
            'domain': domain_key,
            'percentage': 45
        })
        prompt = self._create_optimized_prompt(domain_key, domain_info, top_articles, article_context)
        
        try:
            # Génération du contenu via IA
            self._emit_progress({
                'type': 'step_completed',
                'step': 'Génération du contenu IA',
                'domain': domain_key,
                'percentage': 60
            })
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            content = response.text
            
            # Post-traitement pour LinkedIn avec variations de style
            self._emit_progress({
                'type': 'step_completed',
                'step': 'Optimisation LinkedIn',
                'domain': domain_key,
                'percentage': 75
            })
            optimized_content = self._optimize_for_linkedin(content, domain_key, article_context)
            
            # Générer hashtags intelligents
            self._emit_progress({
                'type': 'step_completed',
                'step': 'Génération des hashtags',
                'domain': domain_key,
                'percentage': 85
            })
            hashtags_str = self._generate_smart_hashtags(top_articles, domain_key, article_context)
            hashtags_list = hashtags_str.split() if hashtags_str else []
            
            # Générer la section sources améliorée
            self._emit_progress({
                'type': 'step_completed',
                'step': 'Finalisation des sources',
                'domain': domain_key,
                'percentage': 95
            })
            sources_section = self._generate_enhanced_sources(domain_key, top_articles, article_context)
            
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
        """Crée un prompt optimisé basé sur le contexte des articles avec variations de style"""
        
        # Sélectionner un format et un ton aléatoires
        post_format = self.style_variations.get_random_format(context)
        tone = self.style_variations.get_random_tone(post_format['name'])
        
        # Stocker les choix de style dans le contexte pour usage ultérieur
        context['selected_format'] = post_format
        context['selected_tone'] = tone
        context['domain_name'] = domain_info['name']
        
        # Construction dynamique du résumé des articles
        articles_summary = self._build_contextual_summary(articles, context)
        
        # Technologies tendances pour ce batch
        trending_techs = [tech for tech, _ in context['trending_technologies']]
        tech_focus = ', '.join(trending_techs[:4]) if trending_techs else 'diverses technologies'
        context['main_technology'] = trending_techs[0] if trending_techs else 'technologie'
        
        # Entreprises clés
        key_companies = [comp for comp, _ in context['key_companies']]
        company_context = f" (notamment {', '.join(key_companies[:2])})" if key_companies else ""
        
        # Thèmes clés
        key_themes = [theme for theme, _ in context['key_themes']]
        themes_context = f"Thèmes dominants: {', '.join(key_themes[:3])}" if key_themes else ""
        context['main_topic'] = key_themes[0] if key_themes else 'innovation tech'
        
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
        
        # Générer le prompt dynamique basé sur le format et le ton sélectionnés
        return self._generate_dynamic_prompt(
            domain_key, domain_info, articles, context, 
            post_format, tone, articles_summary, tech_focus, 
            key_companies, themes_context, insights_context,
            urgency_tone, temporal_indicators
        )
    
    def _generate_dynamic_prompt(self, domain_key: str, domain_info: Dict, articles: List[Dict], 
                                 context: Dict, post_format: Dict, tone: Dict, articles_summary: str,
                                 tech_focus: str, key_companies: List[str], themes_context: str,
                                 insights_context: str, urgency_tone: str, temporal_indicators: str) -> str:
        """Génère un prompt dynamique basé sur le format et le ton sélectionnés"""
        
        # Adapter les consignes selon le format
        format_instructions = self._get_format_instructions(post_format, tone)
        
        # Adapter le style d'écriture selon le ton
        tone_instructions = self._get_tone_instructions(tone)
        
        # Générer la structure selon le format
        structure_template = self._get_structure_template(post_format, context)
        
        # Prompt de base adaptatif
        base_prompt = f"""
Tu es un expert en {domain_info['name']} reconnu sur LinkedIn. 
FORMAT CHOISI: {post_format['name']} - {post_format['description']}
TON CHOISI: {tone['name']} - Caractéristiques: {', '.join(tone['characteristics'])}

🎯 CONTEXTE ENRICHI:
• Technologies tendances: {tech_focus}
• Entreprises actives: {', '.join(key_companies) if key_companies else 'écosystème global'}
• {themes_context}
• {insights_context}
• Niveau technique: {context['technical_depth']}
• Urgence: {context['urgency_level']} | Temporalité: {context.get('temporal_context', 'current')}

📰 SOURCES ANALYSÉES ({len(articles)} articles):
{articles_summary}

✅ CONSIGNES DE FORMAT ({post_format['name']}):
{format_instructions}

✅ CONSIGNES DE TON ({tone['name']}):
{tone_instructions}

✅ STRUCTURE À SUIVRE:
{structure_template}

📝 INSTRUCTIONS CRITIQUES:
- LONGUEUR MAXIMALE: 280-350 mots (ABSOLUMENT IMPÉRATIF)
- UNE SEULE OUVERTURE: Éviter toute répétition ou doublon
- ÉMOJIS: Maximum 3-4 émojis stratégiques, style {tone['emoji_style']}
- STYLE: {tone['sentence_style']} - cohérent du début à la fin
- TON UNIFORME: Maintenir le ton {tone['name']} sans déviation
- SOURCES: Intégrer naturellement sans surcharger
- STRUCTURE: Respecter strictement le format {post_format['name']}
- APPEL À L'ACTION: Une seule question finale percutante

CONTRAINTES ABSOLUES:
❌ PAS de doublons dans l'introduction
❌ PAS de répétitions de phrases
❌ PAS d'émojis redondants ou excessifs
❌ PAS de dépassement de longueur

Génère le post LinkedIn en respectant ces contraintes critiques:
"""
        
        return base_prompt
    
    def _get_format_instructions(self, post_format: Dict, tone: Dict) -> str:
        """Retourne les instructions spécifiques au format choisi"""
        format_instructions = {
            'storytelling': """
- UNE SEULE ouverture narrative (pas de répétition)
- Maximum 3 paragraphes: situation → développement → leçon
- Intègre naturellement 1-2 technologies dans l'histoire
- Termine par UNE question d'engagement
- Évite les émojis dans le récit principal""",
            
            'listicle': """
- Ouverture avec chiffre accrocheur (ex: "3 innovations qui...")
- Maximum 3-4 points numérotés (1️⃣, 2️⃣, 3️⃣)
- Chaque point = 1 phrase + 1 exemple concret
- Pas plus de 50 mots par point
- Conclusion actionnable en 1 phrase""",
            
            'question_driven': """
- Ouvre avec une question provocante ou intrigante
- Explore différentes réponses possibles
- Présente des perspectives contrastées
- Guide vers une réflexion plus profonde
- Termine par une nouvelle question ouverte""",
            
            'comparison': """
- Présente clairement les deux options dès le début
- Structure en "D'un côté... De l'autre..."
- Analyse objective des avantages/inconvénients
- Utilise des exemples concrets pour chaque option
- Conclusion nuancée avec recommandation contextuelle""",
            
            'breaking_news': """
- Lead percutant façon journalistique
- Réponses aux 5W (What, When, Where, Who, Why)
- Informations par ordre d'importance décroissante
- Citations et sources crédibles
- Impact immédiat et implications futures""",
            
            'deep_dive': """
- Introduction qui pose le contexte technique
- Analyse structurée en sections claires
- Explications techniques avec analogies accessibles
- Exemples de code ou architectures si pertinent
- Conclusion avec ressources pour approfondir""",
            
            'hot_take': """
- Opinion forte dès la première ligne
- Arguments structurés et sourcés
- Anticipe et adresse les contre-arguments
- Ton confiant mais respectueux
- Invite au débat constructif""",
            
            'tutorial_mini': """
- Promesse claire de ce qu'on va apprendre
- Étapes numérotées et actionnables
- Tips et raccourcis pratiques
- Pièges à éviter clairement identifiés
- Exercice ou défi pour pratiquer"""
        }
        
        return format_instructions.get(post_format['name'], format_instructions['storytelling'])
    
    def _get_tone_instructions(self, tone: Dict) -> str:
        """Retourne les instructions spécifiques au ton choisi"""
        tone_instructions = {
            'enthusiastic': """
- Utilise des superlatifs et des exclamations (avec modération)
- Montre de l'énergie et de la passion
- Célèbre les innovations et les réussites
- Phrases courtes et dynamiques
- Emojis expressifs pour ponctuer""",
            
            'analytical': """
- Focus sur les données et métriques concrètes
- Argumentation logique et structurée
- Évite les jugements émotionnels
- Utilise des connecteurs logiques
- Minimal en emojis, préfère les chiffres""",
            
            'conversational': """
- Adresse directe au lecteur ("vous" uniquement, pas "tu")
- Maximum 2 questions dans tout le post
- Langage accessible mais professionnel
- Éviter les parenthèses excessives
- Ton bienveillant et expert""",
            
            'authoritative': """
- Affirmations confiantes et directes
- Expertise démontrée par les exemples
- Évite les hésitations ("peut-être", "il semble")
- Structure claire et professionnelle
- Leadership d'opinion assumé""",
            
            'curious': """
- Questions ouvertes fréquentes
- Exploration des possibilités
- "Et si...", "Imaginez que..."
- Encourage la réflexion collective
- Ton humble malgré l'expertise""",
            
            'pragmatic': """
- Focus sur l'actionnable et le ROI
- Exemples concrets d'implémentation
- Métriques de succès claires
- Évite la théorie pure
- Solutions pratiques immédiates"""
        }
        
        return tone_instructions.get(tone['name'], tone_instructions['conversational'])
    
    def _get_structure_template(self, post_format: Dict, context: Dict) -> str:
        """Génère un template de structure adapté au format"""
        structure_templates = {
            'storytelling': f"""
1. 🎬 Accroche narrative (situation concrète ou anecdote)
2. 📖 Développement de l'histoire avec les insights tech
3. 🔍 Moment de révélation ou tournant
4. 💡 Leçon tirée pour les professionnels {context.get('domain_name', 'tech')}
5. 🎯 Call-to-action lié à la morale de l'histoire""",
            
            'listicle': f"""
1. 📋 Titre avec nombre + promesse de valeur
2. 🎯 Intro courte (pourquoi cette liste maintenant?)
3. 1️⃣ Premier point avec exemple concret
4. 2️⃣ Deuxième point avec métrique/preuve
5. 3️⃣ Troisième point avec impact business
6. ✅ Conclusion actionnable""",
            
            'question_driven': f"""
1. ❓ Question d'ouverture intrigante sur {context.get('main_topic', 'le sujet')}
2. 🤔 Exploration du contexte et des enjeux
3. 💭 Présentation de différentes perspectives
4. 🔍 Analyse basée sur les sources
5. 🎯 Nouvelle question pour continuer la réflexion""",
            
            'comparison': f"""
1. ⚖️ Introduction du dilemme technique
2. ➡️ Option A: avantages et cas d'usage
3. ⬅️ Option B: avantages et cas d'usage
4. 📊 Analyse comparative objective
5. 🎯 Recommandation contextuelle""",
            
            'breaking_news': f"""
1. 🚨 Lead d'actualité percutant
2. 📰 Faits essentiels (qui, quoi, quand, où)
3. 💥 Impact immédiat sur l'écosystème
4. 🔮 Implications futures
5. 📢 Call-to-action d'urgence""",
            
            'deep_dive': f"""
1. 🔬 Contexte technique et problématique
2. 🧪 Analyse détaillée avec données
3. 💻 Exemples pratiques/techniques
4. 📈 Résultats et métriques
5. 📚 Ressources pour approfondir""",
            
            'hot_take': f"""
1. 🔥 Opinion forte et claire
2. 📍 Arguments principaux avec preuves
3. 🎯 Contre-arguments anticipés
4. 💪 Renforcement de la position
5. 💬 Invitation au débat constructif""",
            
            'tutorial_mini': f"""
1. 🎓 Ce que vous allez apprendre
2. ✅ Prérequis rapides
3. 1️⃣ Première étape clé
4. 2️⃣ Deuxième étape avec astuce
5. 💡 Pro tip bonus
6. 🚀 Défi pratique à relever"""
        }
        
        return structure_templates.get(post_format['name'], structure_templates['storytelling'])
    
    
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
    
    def _optimize_for_linkedin(self, content: str, domain_key: str, context: Dict) -> str:
        """Optimise le contenu pour LinkedIn avec variations de style"""
        # Récupérer le format et le ton sélectionnés
        selected_format = context.get('selected_format', {})
        selected_tone = context.get('selected_tone', {})
        
        # Nettoyage de base
        optimized = content.strip()
        
        # Appliquer les variations de style si disponibles
        if hasattr(self, 'style_variations') and selected_format and selected_tone:
            # Appliquer les variations de format et de ton
            optimized = self.style_variations.format_with_variations(
                optimized, 
                selected_format.get('name', 'storytelling'),
                selected_tone
            )
            
            # Les variations d'ouverture et fermeture sont gérées par le prompt principal
            # pour éviter les doublons - désactivées temporairement
        
        # Optimisation standard de la lisibilité LinkedIn
        paragraphs = optimized.split('\n\n')
        readable_paragraphs = []
        
        # Adapter la longueur des paragraphes selon le style de phrases
        sentence_style = selected_tone.get('sentence_style', 'varied')
        max_paragraph_length = {
            'short_punchy': 150,
            'structured': 250,
            'varied': 200,
            'declarative': 220,
            'interrogative': 180,
            'direct': 160
        }.get(sentence_style, 200)
        
        for paragraph in paragraphs:
            if len(paragraph) > max_paragraph_length:
                # Diviser aux phrases
                sentences = paragraph.split('. ')
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk + sentence) < max_paragraph_length - 50:
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
    
    def _get_opening_style(self, format_name: str) -> str:
        """Retourne le style d'ouverture approprié pour le format"""
        opening_styles = {
            'storytelling': 'story_opener',
            'listicle': 'stat_shock',
            'question_driven': 'question_hook',
            'comparison': 'question_hook',
            'breaking_news': 'breaking_opener',
            'deep_dive': 'stat_shock',
            'hot_take': 'controversial_opener',
            'tutorial_mini': 'question_hook'
        }
        return opening_styles.get(format_name, 'question_hook')
    
    def _get_closing_style(self, format_name: str) -> str:
        """Retourne le style de fermeture approprié pour le format"""
        closing_styles = {
            'storytelling': 'call_to_action',
            'listicle': 'challenge',
            'question_driven': 'question_engage',
            'comparison': 'question_engage',
            'breaking_news': 'prediction',
            'deep_dive': 'call_to_action',
            'hot_take': 'question_engage',
            'tutorial_mini': 'challenge'
        }
        return closing_styles.get(format_name, 'question_engage')
    
    def _generate_smart_hashtags(self, articles: List[Dict], domain_key: str, context: Dict) -> str:
        """Génère des hashtags intelligents basés sur le contenu avec variations"""
        hashtags = set()
        
        # Récupérer le ton sélectionné pour adapter les hashtags
        selected_tone = context.get('selected_tone', {})
        selected_format = context.get('selected_format', {})
        
        # Hashtags de base par domaine avec variations
        base_hashtags_variations = {
            'frontend': {
                'core': ['#Frontend', '#JavaScript', '#WebDev'],
                'trendy': ['#FrontendDev', '#ModernWeb', '#UIEngineering'],
                'specific': ['#ReactJS', '#VueJS', '#AngularDev', '#SvelteJS'],
                'community': ['#100DaysOfCode', '#WebDevCommunity', '#FrontendMasters']
            },
            'backend': {
                'core': ['#Backend', '#API', '#DevOps'],
                'trendy': ['#CloudNative', '#ServerlessComputing', '#InfraAsCode'],
                'specific': ['#NodeJS', '#Python', '#Golang', '#RustLang'],
                'community': ['#BackendDevelopment', '#SystemDesign', '#TechArchitecture']
            },
            'ai': {
                'core': ['#AI', '#MachineLearning', '#DeepLearning'],
                'trendy': ['#GenerativeAI', '#LLMs', '#AIEngineering'],
                'specific': ['#ChatGPT', '#Claude', '#Gemini', '#OpenAI'],
                'community': ['#AIcommunity', '#MLOps', '#DataScience']
            },
            'general': {
                'core': ['#Tech', '#Development', '#Innovation'],
                'trendy': ['#TechTrends', '#DigitalTransformation', '#FutureTech'],
                'specific': ['#Programming', '#SoftwareEngineering', '#CodingLife'],
                'community': ['#TechCommunity', '#DeveloperLife', '#TechNews']
            }
        }
        
        domain_hashtags = base_hashtags_variations.get(domain_key, base_hashtags_variations['general'])
        
        # Sélectionner des hashtags selon le ton et le format
        if selected_tone.get('name') == 'enthusiastic' or selected_format.get('name') == 'hot_take':
            hashtags.update(domain_hashtags['trendy'][:2])
            hashtags.update(domain_hashtags['community'][:1])
        elif selected_tone.get('name') == 'analytical' or selected_format.get('name') == 'deep_dive':
            hashtags.update(domain_hashtags['core'][:2])
            hashtags.update(domain_hashtags['specific'][:1])
        elif selected_format.get('name') == 'breaking_news':
            hashtags.add('#Breaking')
            hashtags.update(domain_hashtags['trendy'][:2])
        else:
            # Mix par défaut
            hashtags.add(domain_hashtags['core'][0])
            hashtags.add(domain_hashtags['trendy'][0])
            hashtags.add(domain_hashtags['community'][0])
        
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
        
        # Hashtags trending/génériques avec variations selon le contexte
        trending_variations = {
            'breaking': ['#BreakingTech', '#TechNews', '#JustAnnounced'],
            'trending': ['#Trending', '#TechTrends2024', '#HotInTech'],
            'educational': ['#LearnToCode', '#TechEducation', '#SkillUp'],
            'community': ['#TechTwitter', '#DevCommunity', '#CodeNewbie'],
            'professional': ['#TechLeadership', '#EngineeringExcellence', '#TechStrategy']
        }
        
        # Ajouter des hashtags selon le type d'articles
        article_types = context.get('article_types', [])
        if 'security' in article_types:
            hashtags.add('#CyberSecurity')
        if 'release' in article_types:
            hashtags.add('#NewRelease')
        if 'tutorial' in article_types or 'educational' in article_types:
            hashtags.update(trending_variations['educational'][:1])
        
        # Ajouter des hashtags selon la temporalité
        temporal_context = context.get('temporal_context', 'current')
        if temporal_context in trending_variations:
            hashtags.update(trending_variations[temporal_context][:1])
        
        # Compléter avec des hashtags génériques variés
        generic_pool = [
            '#TechNews', '#DeveloperLife', '#CodingLife', '#TechCommunity',
            '#SoftwareDevelopment', '#Innovation', '#Technology', '#CodeLife',
            '#Programming', '#Developers', '#TechIndustry', '#DigitalInnovation'
        ]
        
        # Mélanger le pool pour plus de variété
        random.shuffle(generic_pool)
        
        for tag in generic_pool:
            if len(hashtags) < 10:
                hashtags.add(tag)
            else:
                break
        
        # Retourner une sélection variée de hashtags
        hashtag_list = list(hashtags)
        random.shuffle(hashtag_list)  # Mélanger l'ordre pour plus de variation
        
        return ' '.join(hashtag_list[:8])  # Max 8 hashtags
    
    def _generate_enhanced_sources(self, domain_key: str, articles: List[Dict], context: Dict = None) -> str:
        """Génère une section sources optimisée pour LinkedIn avec variations"""
        domain_name = self.domains[domain_key]['name']
        
        # Variations de headers selon le contexte
        header_variations = [
            f"📚 **SOURCES {domain_name.upper()} ANALYSÉES**",
            f"🔍 **RÉFÉRENCES {domain_name.upper()} CONSULTÉES**",
            f"📰 **VEILLE {domain_name.upper()} DU JOUR**",
            f"💡 **INSIGHTS {domain_name.upper()} SOURCÉS**",
            f"🌐 **PANORAMA {domain_name.upper()} ACTUEL**"
        ]
        
        # Sélectionner un header aléatoire
        sources_header = random.choice(header_variations) + "\n"
        
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
        
        # Footer avec métadonnées - variations
        total_sources = len(set(article['source'] for article in articles))
        
        footer_variations = [
            f"_Analyse basée sur {len(articles)} articles de {total_sources} sources fiables_",
            f"_Synthèse de {len(articles)} publications issues de {total_sources} références reconnues_",
            f"_Curation de {len(articles)} contenus provenant de {total_sources} médias spécialisés_",
            f"_Agrégation de {len(articles)} ressources via {total_sources} plateformes de référence_",
            f"_Veille réalisée sur {len(articles)} articles depuis {total_sources} sources tech de confiance_"
        ]
        
        sources_section += random.choice(footer_variations)
        
        return sources_section.strip()
    
    
