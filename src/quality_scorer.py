"""
Système de scoring de qualité pour les articles
Focus sur le contenu, la profondeur technique et les nouveautés
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from .sources_config import NOVELTY_KEYWORDS, QUALITY_CONFIG

class QualityScorer:
    def __init__(self):
        self.novelty_patterns = self._compile_patterns()
        self.weights = QUALITY_CONFIG['scoring_weights']
        
    def calculate_quality_score(self, article: Dict, source_config: Dict) -> Tuple[float, Dict]:
        """Score basé sur la qualité du contenu, pas juste la fraîcheur"""
        scores = {
            'source_authority': self._score_source_authority(article, source_config),
            'content_depth': self._score_content_depth(article),
            'novelty_factor': self._score_novelty(article),
            'technical_value': self._score_technical_value(article),
            'freshness': self._score_balanced_freshness(article),
            'relevance': self._score_relevance(article, source_config)
        }
        
        # Calcul du score total avec pondération
        total_score = sum(scores[k] * self.weights[k] * 100 for k in scores)
        
        return total_score, scores
    
    def _score_source_authority(self, article: Dict, source_config: Dict) -> float:
        """Score basé sur l'autorité de la source"""
        base_weight = source_config.get('weight', 5) / 10
        
        # Bonus pour types de sources
        source_type = source_config.get('type', '')
        type_multipliers = {
            'official': 1.2,
            'research': 1.15,
            'deep-dive': 1.1,
            'expert': 1.1,
            'mvp': 1.05,
            'core-team': 1.15,
            'foundation': 1.1
        }
        
        multiplier = type_multipliers.get(source_type, 1.0)
        return min(base_weight * multiplier, 1.0)
    
    def _score_content_depth(self, article: Dict) -> float:
        """Évalue la profondeur du contenu"""
        content = article.get('content', article.get('summary', ''))
        title = article.get('title', '')
        
        # Score de longueur (optimisé pour 500-3000 mots)
        word_count = len(content.split())
        if 500 <= word_count <= 3000:
            length_score = 1.0
        elif word_count < 500:
            length_score = max(0.3, word_count / 500)
        else:
            length_score = max(0.7, 1 - (word_count - 3000) / 10000)
        
        # Présence d'exemples de code
        code_patterns = [
            r'```[\s\S]*?```',           # Markdown code blocks
            r'<code>[\s\S]*?</code>',    # HTML code tags
            r'<pre>[\s\S]*?</pre>',      # HTML pre tags
            r'function\s+\w+\s*\(',      # Function definitions
            r'class\s+\w+\s*[:{]',       # Class definitions
            r'import\s+\w+',             # Import statements
            r'const\s+\w+\s*=',          # Variable declarations
        ]
        
        code_blocks = 0
        for pattern in code_patterns:
            code_blocks += len(re.findall(pattern, content, re.IGNORECASE))
        
        code_score = min(code_blocks * 0.15, 0.6)
        
        # Structure du contenu (headers, listes, etc.)
        structure_patterns = [
            (r'^#{1,6}\s+\w+', 0.1),      # Headers
            (r'^\d+\.\s+\w+', 0.1),       # Numbered lists
            (r'^\*\s+\w+', 0.1),          # Bullet lists
            (r'^\-\s+\w+', 0.1),          # Dash lists
            (r'>\s+\w+', 0.05),           # Blockquotes
        ]
        
        structure_score = 0
        for pattern, score in structure_patterns:
            if re.search(pattern, content, re.MULTILINE):
                structure_score += score
        
        # Profondeur technique dans le titre
        technical_title_patterns = [
            r'how\s+to', r'guide', r'tutorial', r'implementation',
            r'deep\s+dive', r'comprehensive', r'complete', r'advanced',
            r'best\s+practices', r'patterns', r'architecture'
        ]
        
        title_depth = 0
        for pattern in technical_title_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                title_depth += 0.1
        
        total_score = (length_score + code_score + structure_score + title_depth) / 2.5
        return min(total_score, 1.0)
    
    def _score_novelty(self, article: Dict) -> float:
        """Détecte et score les vraies nouveautés"""
        title = article.get('title', '').lower()
        content = article.get('summary', '').lower()
        full_text = title + ' ' + content
        
        novelty_score = 0
        
        # Patterns de nouveauté avec poids spécifiques
        for category, keywords in NOVELTY_KEYWORDS.items():
            category_score = 0
            
            for keyword in keywords:
                if re.search(keyword, full_text, re.IGNORECASE):
                    # Bonus si c'est dans le titre
                    if re.search(keyword, title, re.IGNORECASE):
                        category_score += 0.3
                    else:
                        category_score += 0.2
            
            # Pondération par catégorie
            weights = {
                'releases': 0.35,
                'features': 0.25,
                'breaking': 0.15,
                'performance': 0.15,
                'security': 0.1,
                'ecosystem': 0.1
            }
            
            novelty_score += min(category_score, 1.0) * weights.get(category, 0.1)
        
        # Bonus pour versions spécifiques
        version_patterns = [
            r'v?\d+\.\d+\.\d+',  # Semantic versioning
            r'\d{4}\.\d{1,2}',   # Year.month versioning
            r'version\s+\d+',    # Version numbers
        ]
        
        for pattern in version_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                novelty_score += 0.1
                break
        
        # Bonus pour dates récentes mentionnées
        recent_date_patterns = [
            r'20\d{2}',  # Years
            r'january|february|march|april|may|june|july|august|september|october|november|december',
            r'Q[1-4]\s+20\d{2}'  # Quarters
        ]
        
        for pattern in recent_date_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                novelty_score += 0.05
                break
        
        return min(novelty_score, 1.0)
    
    def _score_technical_value(self, article: Dict) -> float:
        """Évalue la valeur technique du contenu"""
        content = article.get('content', article.get('summary', '')).lower()
        title = article.get('title', '').lower()
        full_text = title + ' ' + content
        
        technical_indicators = {
            'implementation': (r'implement|implementation|code\s+example|snippet|sample', 0.2),
            'architecture': (r'architecture|design\s+pattern|scalability|microservice', 0.2),
            'optimization': (r'optimize|optimization|performance|benchmark|profiling', 0.15),
            'best_practice': (r'best\s+practice|guideline|recommendation|tip|convention', 0.15),
            'comparison': (r'vs\.|versus|comparison|difference\s+between|compared\s+to', 0.1),
            'tutorial': (r'how\s+to|tutorial|guide|walkthrough|step[\s\-]by[\s\-]step', 0.1),
            'debugging': (r'debug|troubleshoot|error|fix|issue|problem', 0.1),
            'testing': (r'test|testing|unit\s+test|integration|e2e|qa', 0.1),
            'deployment': (r'deploy|deployment|production|ci\/cd|devops', 0.1),
            'security': (r'security|secure|vulnerability|authentication|authorization', 0.1)
        }
        
        score = 0
        for category, (pattern, weight) in technical_indicators.items():
            if re.search(pattern, full_text):
                score += weight
        
        # Bonus pour présence de termes techniques spécialisés
        specialized_terms = [
            r'algorithm', r'data\s+structure', r'complexity', r'runtime',
            r'memory\s+management', r'garbage\s+collection', r'concurrency',
            r'async|await', r'promise', r'callback', r'closure',
            r'inheritance', r'polymorphism', r'encapsulation',
            r'singleton', r'factory', r'observer', r'decorator'
        ]
        
        term_bonus = 0
        for term in specialized_terms:
            if re.search(term, full_text):
                term_bonus += 0.02
        
        total_score = score + min(term_bonus, 0.2)
        return min(total_score, 1.0)
    
    def _score_balanced_freshness(self, article: Dict) -> float:
        """Fraîcheur équilibrée, pas surdimensionnée"""
        published = article.get('published_parsed')
        if not published:
            # Si pas de date, supposer récent mais pas optimal
            return 0.6
            
        try:
            publish_date = datetime(*published[:6])
            age_hours = (datetime.now() - publish_date).total_seconds() / 3600
            
            # Courbe de fraîcheur plus équilibrée
            if age_hours < 6:
                return 1.0
            elif age_hours < 24:
                return 0.95
            elif age_hours < 72:
                return 0.85
            elif age_hours < 168:  # 1 semaine
                return 0.7
            elif age_hours < 336:  # 2 semaines
                return 0.5
            elif age_hours < 720:  # 1 mois
                return 0.3
            else:
                return 0.1
                
        except (TypeError, ValueError):
            return 0.6
    
    def _score_relevance(self, article: Dict, source_config: Dict) -> float:
        """Pertinence par rapport au focus de la source"""
        focus = source_config.get('focus', '')
        if not focus:
            return 0.5
            
        title = article.get('title', '').lower()
        content = article.get('summary', '').lower()
        
        focus_keywords = {
            'releases': ['release', 'version', 'launch', 'available', 'shipped', 'announced'],
            'patterns': ['pattern', 'practice', 'architecture', 'design', 'approach'],
            'optimization': ['performance', 'optimize', 'fast', 'efficient', 'speed'],
            'tutorials': ['how to', 'guide', 'tutorial', 'learn', 'getting started'],
            'ecosystem': ['library', 'tool', 'framework', 'package', 'plugin'],
            'internals': ['internal', 'under the hood', 'deep dive', 'implementation'],
            'advanced': ['advanced', 'expert', 'professional', 'complex'],
            'practices': ['practice', 'convention', 'standard', 'guideline'],
            'features': ['feature', 'capability', 'functionality', 'support'],
            'security': ['security', 'secure', 'vulnerability', 'safety'],
            'standards': ['standard', 'specification', 'RFC', 'proposal']
        }
        
        relevant_keywords = focus_keywords.get(focus, [focus.split('-')])
        if isinstance(relevant_keywords[0], list):
            relevant_keywords = relevant_keywords[0]
        
        # Compter les matches dans le titre (poids double) et contenu
        title_matches = sum(1 for keyword in relevant_keywords if keyword in title)
        content_matches = sum(1 for keyword in relevant_keywords if keyword in content)
        
        total_matches = (title_matches * 2) + content_matches
        max_possible = len(relevant_keywords) * 3  # 2 pour titre + 1 pour contenu
        
        relevance = total_matches / max_possible if max_possible > 0 else 0
        
        return min(relevance, 1.0)
    
    def _compile_patterns(self) -> Dict[str, List]:
        """Compile les patterns regex pour les nouveautés"""
        compiled = {}
        for category, keywords in NOVELTY_KEYWORDS.items():
            compiled[category] = []
            for keyword in keywords:
                try:
                    compiled[category].append(re.compile(keyword, re.IGNORECASE))
                except re.error:
                    # Si ce n'est pas un regex valide, traiter comme texte littéral
                    compiled[category].append(re.compile(re.escape(keyword), re.IGNORECASE))
        return compiled
    
    def get_score_explanation(self, article: Dict, scores: Dict) -> str:
        """Génère une explication du score pour debug"""
        explanation = f"Quality Score Breakdown for: {article.get('title', 'Unknown')[:50]}...\n"
        explanation += f"Total Score: {sum(scores[k] * self.weights[k] * 100 for k in scores):.1f}/100\n\n"
        
        for component, score in scores.items():
            weight = self.weights[component]
            weighted_score = score * weight * 100
            explanation += f"{component}: {score:.2f} (weight: {weight:.1%}) = {weighted_score:.1f} points\n"
        
        return explanation