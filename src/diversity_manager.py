"""
Gestionnaire de diversité technologique pour garantir 
une sélection équilibrée d'articles par technologie
"""

import re
from collections import defaultdict
from typing import List, Dict, Set, Tuple
from loguru import logger
from .sources_config import QUALITY_CONFIG

class DiversityManager:
    def __init__(self):
        self.tech_patterns = self._build_tech_patterns()
        self.diversity_config = QUALITY_CONFIG['diversity_config']
        
    def ensure_diversity(self, articles: List[Dict], domain: str, target_count: int = 20) -> List[Dict]:
        """Garantit un équilibre optimal entre diversité technologique et qualité du contenu"""
        
        if not articles:
            return []
            
        # Catégoriser les articles par technologie
        categorized = self._categorize_articles(articles, domain)
        
        logger.info(f"Articles categorized for {domain}: {dict((k, len(v)) for k, v in categorized.items())}")
        
        # Calculer le score hybride qualité-diversité pour chaque article
        self._calculate_hybrid_scores(categorized, domain)
        
        # Sélection équilibrée avec nouveau algorithme
        selected = self._balanced_selection(categorized, target_count, domain)
        
        logger.info(f"Final selection for {domain}: {len(selected)} articles")
        
        return selected
    
    def _categorize_articles(self, articles: List[Dict], domain: str) -> Dict[str, List[Dict]]:
        """Catégorise les articles par technologie"""
        categorized = defaultdict(list)
        patterns = self.tech_patterns.get(domain, {})
        
        for article in articles:
            title = article.get('title', '').lower()
            content = article.get('summary', '').lower()
            full_text = title + ' ' + content
            
            # Récupérer la technologie depuis la source si disponible
            source_tech = article.get('technology', '')
            
            # Détection multi-catégorie avec score
            tech_scores = {}
            
            # Bonus pour la technologie de la source
            if source_tech and source_tech in patterns:
                tech_scores[source_tech] = 5  # Score de base élevé
            
            # Analyse des patterns dans le contenu
            for tech, pattern_list in patterns.items():
                score = 0
                for pattern in pattern_list:
                    # Recherche dans le titre (poids double)
                    if re.search(pattern, title):
                        score += 3
                    # Recherche dans le contenu
                    elif re.search(pattern, full_text):
                        score += 1
                
                if score > 0:
                    tech_scores[tech] = tech_scores.get(tech, 0) + score
            
            # Assigner à la catégorie principale ou générale
            if tech_scores:
                # Si plusieurs technologies détectées, prendre celle avec le meilleur score
                main_tech = max(tech_scores, key=tech_scores.get)
                categorized[main_tech].append(article)
                
                # Ajouter les métadonnées de détection
                article['detected_technologies'] = tech_scores
                article['primary_technology'] = main_tech
            else:
                categorized['general'].append(article)
                article['primary_technology'] = 'general'
                
        return dict(categorized)
    
    def _calculate_hybrid_scores(self, categorized: Dict[str, List[Dict]], domain: str):
        """Calcule un score hybride combinant qualité et valeur de diversité"""
        # Calculer les métriques de diversité
        total_articles = sum(len(articles) for articles in categorized.values())
        tech_counts = {tech: len(articles) for tech, articles in categorized.items()}
        
        # Calculer le bonus/malus de diversité pour chaque technologie
        diversity_factors = {}
        for tech, count in tech_counts.items():
            if tech == 'general':
                diversity_factors[tech] = 0.8  # Légère pénalité pour articles généraux
            else:
                # Bonus pour technologies sous-représentées
                representation_ratio = count / total_articles
                if representation_ratio < 0.1:  # Moins de 10% = bonus
                    diversity_factors[tech] = self.diversity_config['underrepresented_bonus']
                elif representation_ratio < 0.2:  # 10-20% = léger bonus
                    diversity_factors[tech] = 1.1
                elif representation_ratio > 0.4:  # Plus de 40% = malus
                    diversity_factors[tech] = self.diversity_config['overrepresented_penalty']
                else:
                    diversity_factors[tech] = 1.0
        
        # Appliquer les scores hybrides
        for tech, articles in categorized.items():
            diversity_factor = diversity_factors.get(tech, 1.0)
            
            for article in articles:
                base_quality = article.get('quality_score', 0)
                
                # Score hybride = qualité * facteur de diversité
                hybrid_score = base_quality * diversity_factor
                
                # Bonus supplémentaire pour articles rares dans leur catégorie
                if len(articles) <= 2:  # Technologie très rare
                    hybrid_score *= self.diversity_config['rare_tech_bonus']
                elif len(articles) <= 5:  # Technologie rare
                    hybrid_score *= 1.1
                
                article['hybrid_score'] = hybrid_score
                article['diversity_factor'] = diversity_factor
    
    def _balanced_selection(self, categorized: Dict[str, List[Dict]], target_count: int, domain: str) -> List[Dict]:
        """Sélection équilibrée prioritisant qualité ET diversité"""
        selected = []
        
        # Étape 1: Garantir au moins 1 article par technologie majeure (si qualité suffisante)
        reserved_slots = 0
        for tech, articles in categorized.items():
            if tech != 'general' and articles:
                # Prendre le meilleur article de chaque techno (si score > seuil)
                best_article = max(articles, key=lambda x: x.get('hybrid_score', 0))
                if best_article.get('quality_score', 0) > self.diversity_config['quality_threshold_guaranteed']:  # Seuil minimum de qualité
                    selected.append(best_article)
                    best_article['selected_for_tech'] = tech
                    best_article['selection_reason'] = 'diversity_guarantee'
                    reserved_slots += 1
        
        # Étape 2: Remplir les slots restants avec les meilleurs scores hybrides
        remaining_slots = target_count - reserved_slots
        
        # Créer une liste de tous les articles restants
        remaining_articles = []
        for tech, articles in categorized.items():
            for article in articles:
                if article not in selected:
                    remaining_articles.append(article)
        
        # Trier par score hybride décroissant
        remaining_articles.sort(key=lambda x: x.get('hybrid_score', 0), reverse=True)
        
        # Ajouter les meilleurs articles restants
        for article in remaining_articles[:remaining_slots]:
            article['selected_for_tech'] = article.get('primary_technology', 'general')
            article['selection_reason'] = 'hybrid_score'
            selected.append(article)
        
        # Étape 3: Validation finale de l'équilibre
        final_selection = self._validate_final_balance(selected, target_count)
        
        return final_selection
    
    def _validate_final_balance(self, selected: List[Dict], target_count: int) -> List[Dict]:
        """Validation finale pour s'assurer d'un bon équilibre"""
        if not selected:
            return selected
        
        # Analyser la distribution finale
        tech_distribution = {}
        for article in selected:
            tech = article.get('selected_for_tech', 'general')
            tech_distribution[tech] = tech_distribution.get(tech, 0) + 1
        
        # Vérifier si une technologie domine trop
        max_tech = max(tech_distribution.values())
        if max_tech > target_count * self.diversity_config['max_tech_dominance']:
            # Rééquilibrer en remplaçant les articles de moindre qualité
            dominant_tech = max(tech_distribution, key=tech_distribution.get)
            
            # Identifier les articles les plus faibles de la techno dominante
            dominant_articles = [a for a in selected if a.get('selected_for_tech') == dominant_tech]
            dominant_articles.sort(key=lambda x: x.get('quality_score', 0))
            
            # Remplacer par des articles d'autres technos si disponibles
            articles_to_replace = dominant_articles[:max_tech - target_count // 2]
            
            logger.info(f"Rééquilibrage détecté: {dominant_tech} domine avec {max_tech} articles")
            
            # Retirer les articles à remplacer
            for article in articles_to_replace:
                selected.remove(article)
        
        return selected[:target_count]
    
    def _calculate_distribution(self, categorized: Dict[str, List[Dict]], target_count: int) -> Dict[str, int]:
        """Calcule la distribution optimale des articles"""
        if not categorized:
            return {}
            
        total_available = sum(len(articles) for articles in categorized.values())
        
        if total_available <= target_count:
            # Si on a moins d'articles que nécessaire, prendre tout
            return {tech: len(articles) for tech, articles in categorized.items()}
        
        # Stratégie de distribution équilibrée
        distribution = {}
        
        # Étape 1: Garantir un minimum par catégorie active
        active_categories = [tech for tech, articles in categorized.items() if articles]
        min_per_category = max(1, target_count // len(active_categories) // 2)
        
        remaining_slots = target_count
        
        # Allocation minimale
        for tech in active_categories:
            min_allocation = min(min_per_category, len(categorized[tech]))
            distribution[tech] = min_allocation
            remaining_slots -= min_allocation
        
        # Étape 2: Distribuer les slots restants proportionnellement
        if remaining_slots > 0:
            # Calculer les poids basés sur la disponibilité et la qualité
            tech_weights = {}
            for tech, articles in categorized.items():
                if tech in distribution:
                    # Poids basé sur nombre d'articles disponibles et qualité moyenne
                    available = len(articles) - distribution[tech]
                    if available > 0:
                        avg_quality = sum(a.get('quality_score', 0) for a in articles) / len(articles)
                        tech_weights[tech] = available * (1 + avg_quality / 100)
            
            total_weight = sum(tech_weights.values())
            
            # Distribuer proportionnellement
            for tech in sorted(tech_weights.keys(), key=lambda x: tech_weights[x], reverse=True):
                if remaining_slots <= 0:
                    break
                    
                if total_weight > 0:
                    weight_ratio = tech_weights[tech] / total_weight
                    additional = min(
                        int(remaining_slots * weight_ratio + 0.5),
                        len(categorized[tech]) - distribution[tech],
                        remaining_slots
                    )
                    
                    distribution[tech] += additional
                    remaining_slots -= additional
        
        # Étape 3: Distribuer les derniers slots aux catégories avec le plus de qualité
        if remaining_slots > 0:
            candidates = []
            for tech, articles in categorized.items():
                available = len(articles) - distribution.get(tech, 0)
                if available > 0:
                    avg_quality = sum(a.get('quality_score', 0) for a in articles) / len(articles)
                    candidates.append((tech, avg_quality))
            
            # Trier par qualité décroissante
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            for tech, _ in candidates:
                if remaining_slots <= 0:
                    break
                
                available = len(categorized[tech]) - distribution.get(tech, 0)
                if available > 0:
                    distribution[tech] = distribution.get(tech, 0) + 1
                    remaining_slots -= 1
        
        return distribution
    
    def get_diversity_report(self, articles: List[Dict], domain: str) -> Dict:
        """Génère un rapport de diversité pour analyse"""
        categorized = self._categorize_articles(articles, domain)
        
        report = {
            'total_articles': len(articles),
            'categories_found': len(categorized),
            'distribution': {},
            'quality_by_category': {},
            'coverage': {}
        }
        
        for tech, tech_articles in categorized.items():
            report['distribution'][tech] = len(tech_articles)
            
            if tech_articles:
                scores = [a.get('quality_score', 0) for a in tech_articles]
                report['quality_by_category'][tech] = {
                    'count': len(tech_articles),
                    'avg_quality': sum(scores) / len(scores),
                    'max_quality': max(scores),
                    'min_quality': min(scores)
                }
        
        # Calculer la couverture technologique
        total_categories = len(self.tech_patterns.get(domain, {}))
        covered_categories = len([k for k in categorized.keys() if k != 'general'])
        report['coverage']['percentage'] = (covered_categories / total_categories * 100) if total_categories > 0 else 0
        report['coverage']['covered'] = covered_categories
        report['coverage']['total'] = total_categories
        
        return report
    
    def _build_tech_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Patterns de détection par domaine et technologie (version améliorée)"""
        return {
            'frontend': {
                'react': [
                    r'\breact\b', r'\bnext\.?js\b', r'\bgatsby\b', r'\bremix\b', 
                    r'\bhooks?\b', r'\bjsx\b', r'\bcomponent\b', r'\bstate\b',
                    r'\buseState\b', r'\buseEffect\b', r'\bvirtual\s+dom\b'
                ],
                'vue': [
                    r'\bvue\b', r'\bnuxt\b', r'\bvuex\b', r'\bpinia\b', 
                    r'\bcomposition\s+api\b', r'\boptions\s+api\b', r'\bv-\w+\b'
                ],
                'angular': [
                    r'\bangular\b', r'\brxjs\b', r'\bngrx\b', r'\bzone\.?js\b',
                    r'\btypescript\b', r'\binjection\b', r'\bcomponent\b', r'\bservice\b'
                ],
                'svelte': [
                    r'\bsvelte\b', r'\bsveltekit\b', r'\breactive\b', r'\bstore\b'
                ],
                'css': [
                    r'\bcss\b', r'\bsass\b', r'\bscss\b', r'\btailwind\b', 
                    r'\bstyled.components\b', r'\bemotion\b', r'\bflexbox\b',
                    r'\bgrid\b', r'\banimation\b', r'\btransition\b'
                ],
                'javascript': [
                    r'\bjavascript\b', r'\btypescript\b', r'\bes\d+\b', r'\becmascript\b',
                    r'\basync\b', r'\bawait\b', r'\bpromise\b', r'\bclosure\b'
                ],
                'tooling': [
                    r'\bwebpack\b', r'\bvite\b', r'\besbuild\b', r'\brollup\b', 
                    r'\bparcel\b', r'\bbabel\b', r'\bundler\b'
                ],
                'testing': [
                    r'\bjest\b', r'\bvitest\b', r'\bcypress\b', r'\bplaywright\b', 
                    r'\btesting.library\b', r'\bunit\s+test\b', r'\be2e\b'
                ],
                'mobile': [
                    r'\breact\s+native\b', r'\bflutter\b', r'\bionic\b', 
                    r'\bcapacitor\b', r'\bcordova\b', r'\bmobile\b'
                ],
                'performance': [
                    r'\bperformance\b', r'\boptimiz\w+\b', r'\blighthouse\b', 
                    r'\bcore\s+web\s+vitals\b', r'\blazy\s+loading\b', r'\bcaching\b'
                ]
            },
            'backend': {
                'nodejs': [
                    r'\bnode\.?js\b', r'\bexpress\b', r'\bnestjs\b', r'\bfastify\b', 
                    r'\bkoa\b', r'\bnpm\b', r'\byarn\b', r'\bv8\b'
                ],
                'python': [
                    r'\bpython\b', r'\bdjango\b', r'\bflask\b', r'\bfastapi\b', 
                    r'\bpydantic\b', r'\bsqlalchemy\b', r'\bpip\b', r'\bconda\b'
                ],
                'java': [
                    r'\bjava\b', r'\bspring\b', r'\bboot\b', r'\bquarkus\b', 
                    r'\bmicronaut\b', r'\bmaven\b', r'\bgradle\b', r'\bjvm\b'
                ],
                'go': [
                    r'\bgolang\b', r'\bgo\s+\d+\.\d+\b', r'\bgin\b', r'\becho\b', 
                    r'\bfiber\b', r'\bgoroutine\b', r'\bchannel\b'
                ],
                'rust': [
                    r'\brust\b', r'\bactix\b', r'\brocket\b', r'\btokio\b', 
                    r'\basync\b', r'\bcargo\b', r'\borrowing\b', r'\bownership\b'
                ],
                'php': [
                    r'\bphp\b', r'\blaravel\b', r'\bsymfony\b', r'\bcomposer\b',
                    r'\bphp\s+\d+\b', r'\bartisan\b'
                ],
                'ruby': [
                    r'\bruby\b', r'\brails\b', r'\bsinatra\b', r'\bgem\b', r'\bbundler\b'
                ],
                'dotnet': [
                    r'\.net\b', r'\bc#\b', r'\basp\.net\b', r'\blazor\b', 
                    r'\bentity\s+framework\b', r'\bnuget\b'
                ],
                'databases': [
                    r'\bpostgres\b', r'\bmysql\b', r'\bmongodb\b', r'\bredis\b', 
                    r'\belasticsearch\b', r'\bsqlite\b', r'\bcassandra\b', r'\boracle\b'
                ],
                'devops': [
                    r'\bdocker\b', r'\bkubernetes\b', r'\bk8s\b', r'\bhelm\b', 
                    r'\bterraform\b', r'\bansible\b', r'\bjenkins\b', r'\bci/cd\b'
                ],
                'cloud': [
                    r'\baws\b', r'\bazure\b', r'\bgcp\b', r'\bserverless\b', 
                    r'\blambda\b', r'\bs3\b', r'\bec2\b', r'\brds\b'
                ],
                'api': [
                    r'\brest\b', r'\bgraphql\b', r'\bapi\b', r'\bgrpc\b', 
                    r'\bopenapi\b', r'\bswagger\b', r'\bmicroservice\b'
                ]
            },
            'ai': {
                'llms': [
                    r'\bllm\b', r'\bgpt\b', r'\bclaude\b', r'\bgemini\b', 
                    r'\blanguage\s+model\b', r'\btransformer\b', r'\bert\b', r'\bllama\b'
                ],
                'ml_frameworks': [
                    r'\btensorflow\b', r'\bpytorch\b', r'\bjax\b', r'\bkeras\b',
                    r'\bscikit.learn\b', r'\bxgboost\b', r'\blightgbm\b'
                ],
                'nlp': [
                    r'\bnlp\b', r'\bnatural\s+language\b', r'\bembedding\b', 
                    r'\btokeniz\w+\b', r'\bsentiment\b', r'\bnamed\s+entity\b'
                ],
                'computer_vision': [
                    r'\bcomputer\s+vision\b', r'\byolo\b', r'\bocr\b', 
                    r'\bimage\s+recognition\b', r'\bopencv\b', r'\bcnn\b'
                ],
                'mlops': [
                    r'\bmlops\b', r'\bmlflow\b', r'\bwandb\b', r'\bkubeflow\b',
                    r'\bmodel\s+deployment\b', r'\bmodel\s+monitoring\b'
                ],
                'data_science': [
                    r'\bpandas\b', r'\bnumpy\b', r'\bscipy\b', r'\bjupyter\b',
                    r'\bnotebook\b', r'\bdata\s+analysis\b', r'\bvisualization\b'
                ],
                'ai_tools': [
                    r'\blangchain\b', r'\bhugging\s?face\b', r'\bstable\s+diffusion\b',
                    r'\bmidjourney\b', r'\bautogen\b', r'\bcrewai\b'
                ],
                'research': [
                    r'\barxiv\b', r'\bpaper\b', r'\bresearch\b', r'\bstudy\b',
                    r'\bexperiment\b', r'\bneural\s+network\b', r'\bdeep\s+learning\b'
                ],
                'ethics': [
                    r'\bai\s+ethics\b', r'\bbias\b', r'\bfairness\b', 
                    r'\bresponsible\s+ai\b', r'\bexplainable\b', r'\binterpretable\b'
                ]
            }
        }
    
    def validate_diversity(self, selected_articles: List[Dict], domain: str, min_categories: int = 3) -> Tuple[bool, Dict]:
        """Valide que la sélection respecte les critères de diversité"""
        categorized = self._categorize_articles(selected_articles, domain)
        
        # Compter les catégories non-générales
        tech_categories = [k for k in categorized.keys() if k != 'general']
        
        validation_result = {
            'is_diverse': len(tech_categories) >= min_categories,
            'categories_count': len(tech_categories),
            'min_required': min_categories,
            'categories': tech_categories,
            'distribution': {k: len(v) for k, v in categorized.items()},
            'recommendations': []
        }
        
        if not validation_result['is_diverse']:
            validation_result['recommendations'].append(
                f"Augmenter la diversité: seulement {len(tech_categories)} catégories détectées, minimum {min_categories} requis"
            )
        
        # Vérifier l'équilibre de la distribution
        if len(tech_categories) > 0:
            tech_counts = [len(categorized[tech]) for tech in tech_categories]
            max_count = max(tech_counts)
            min_count = min(tech_counts)
            
            if max_count > min_count * 3:  # Si une catégorie a 3x plus d'articles qu'une autre
                validation_result['recommendations'].append(
                    "Distribution déséquilibrée: certaines technologies sont sur-représentées"
                )
        
        return validation_result['is_diverse'], validation_result