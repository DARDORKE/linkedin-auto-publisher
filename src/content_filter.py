"""
Système de filtrage avancé pour garantir la qualité du contenu
Élimine les articles promotionnels, de faible qualité ou dupliqués
"""

import re
import hashlib
from typing import List, Dict, Tuple, Set
from datetime import datetime, timedelta
from loguru import logger
from .sources_config import QUALITY_CONFIG

class AdvancedContentFilter:
    def __init__(self):
        self.quality_thresholds = QUALITY_CONFIG
        self.blocklist_patterns = self._build_blocklist_patterns()
        self.low_quality_indicators = self._build_quality_indicators()
        
    def filter_articles(self, articles: List[Dict]) -> Tuple[List[Dict], Dict[str, int]]:
        """Filtre les articles selon des critères de qualité stricts"""
        filtered = []
        rejection_reasons = {
            'duplicate_title': 0,
            'duplicate_content': 0,
            'low_quality_title': 0,
            'promotional': 0,
            'too_short': 0,
            'too_long': 0,
            'too_old': 0,
            'low_score': 0,
            'no_content': 0,
            'spam_indicators': 0
        }
        
        seen_titles = set()
        seen_content_hashes = set()
        
        for article in articles:
            # Vérification de base - contenu existant
            if not self._has_valid_content(article):
                rejection_reasons['no_content'] += 1
                continue
            
            # Vérification de duplication par titre
            title_normalized = self._normalize_title(article.get('title', ''))
            if title_normalized in seen_titles:
                rejection_reasons['duplicate_title'] += 1
                continue
            
            # Vérification de duplication sémantique
            content_hash = self._generate_content_hash(article)
            if content_hash in seen_content_hashes:
                rejection_reasons['duplicate_content'] += 1
                continue
            
            # Vérification de la qualité du titre
            title_quality = self._check_title_quality(article)
            if not title_quality['passed']:
                rejection_reasons['low_quality_title'] += 1
                continue
            
            # Vérification de la qualité du contenu
            content_quality = self._check_content_quality(article)
            if not content_quality['passed']:
                rejection_reasons[content_quality['reason']] += 1
                continue
            
            # Vérification anti-promotion/spam
            if self._is_promotional_or_spam(article):
                rejection_reasons['promotional'] += 1
                continue
            
            # Vérification du score minimum
            if article.get('quality_score', 0) < self.quality_thresholds['min_quality_score']:
                rejection_reasons['low_score'] += 1
                continue
            
            # Vérification des indicateurs de spam
            if self._has_spam_indicators(article):
                rejection_reasons['spam_indicators'] += 1
                continue
            
            # Article accepté
            seen_titles.add(title_normalized)
            seen_content_hashes.add(content_hash)
            filtered.append(article)
        
        logger.info(f"Filtering results: {len(filtered)}/{len(articles)} articles kept. Rejections: {rejection_reasons}")
        
        return filtered, rejection_reasons
    
    def _has_valid_content(self, article: Dict) -> bool:
        """Vérifie que l'article a du contenu utilisable"""
        title = article.get('title', '').strip()
        content = article.get('content', '') or article.get('summary', '')
        
        return bool(title and len(title) > 10 and content and len(content) > 50)
    
    def _normalize_title(self, title: str) -> str:
        """Normalise le titre pour la détection de doublons"""
        # Supprimer la ponctuation et normaliser
        normalized = re.sub(r'[^\w\s]', '', title.lower())
        # Supprimer les mots vides courts
        words = [w for w in normalized.split() if len(w) > 2]
        return ' '.join(words[:10])  # Premiers 10 mots significatifs
    
    def _generate_content_hash(self, article: Dict) -> str:
        """Génère un hash pour détecter les duplicatas sémantiques"""
        title = article.get('title', '').lower()
        content = article.get('summary', '')[:1000].lower()  # Premier 1000 chars
        
        # Normaliser le texte
        full_text = title + ' ' + content
        normalized = re.sub(r'[^\w\s]', ' ', full_text)
        words = normalized.split()
        
        # Créer une signature basée sur les mots clés importants
        important_words = [w for w in words if len(w) > 4][:30]
        signature = ''.join(sorted(set(important_words)))
        
        return hashlib.md5(signature.encode()).hexdigest()
    
    def _check_title_quality(self, article: Dict) -> Dict[str, any]:
        """Vérifie la qualité du titre"""
        title = article.get('title', '')
        
        # Vérifications de base
        if len(title) < 10:
            return {'passed': False, 'reason': 'title_too_short'}
        
        if len(title) > 200:
            return {'passed': False, 'reason': 'title_too_long'}
        
        # Vérification des indicateurs de faible qualité
        low_quality_patterns = [
            r'you\s+won\'t\s+believe',
            r'this\s+one\s+trick',
            r'shocking',
            r'must\s+read',
            r'click\s+here',
            r'\d+\s+things?\s+you',
            r'hate\s+this',
            r'doctors\s+hate',
            r'amazing\s+secret',
            r'weird\s+trick'
        ]
        
        for pattern in low_quality_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return {'passed': False, 'reason': 'clickbait_title'}
        
        # Vérification des titres trop génériques
        generic_patterns = [
            r'^top\s+\d+$',
            r'^best\s+\w+\s+\d{4}$',
            r'^how\s+to\s+\w+$',
            r'^the\s+\w+\s+guide$'
        ]
        
        for pattern in generic_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return {'passed': False, 'reason': 'generic_title'}
        
        return {'passed': True, 'reason': None}
    
    def _check_content_quality(self, article: Dict) -> Dict[str, any]:
        """Vérifie la qualité du contenu"""
        content = article.get('content', article.get('summary', ''))
        word_count = len(content.split())
        
        # Vérification de la longueur
        if word_count < self.quality_thresholds['min_word_count']:
            return {'passed': False, 'reason': 'too_short'}
        
        if word_count > self.quality_thresholds['max_word_count']:
            return {'passed': False, 'reason': 'too_long'}
        
        # Vérification de l'âge (max 2 semaines)
        published = article.get('published_parsed')
        if published:
            try:
                publish_date = datetime(*published[:6])
                age = datetime.now() - publish_date
                if age > timedelta(days=self.quality_thresholds['max_age_days']):
                    return {'passed': False, 'reason': 'too_old'}
            except (TypeError, ValueError):
                pass  # Ignorer les erreurs de date
        
        # Vérification du ratio signal/bruit
        if not self._has_good_signal_to_noise(content):
            return {'passed': False, 'reason': 'low_quality_content'}
        
        return {'passed': True, 'reason': None}
    
    def _has_good_signal_to_noise(self, content: str) -> bool:
        """Vérifie le ratio signal/bruit du contenu"""
        if not content or len(content) < 100:
            return True  # Contenu court accepté
        
        # Compter les éléments de qualité vs bruit
        technical_terms = len(re.findall(r'\b(?:function|class|algorithm|implementation|optimize|performance|security|architecture|pattern|framework|library|api|database|server|client|async|sync|cache|scale|deploy|test|debug|refactor|code|syntax|semantic|protocol|interface|abstract|inherit|polymorphism|encapsulation|javascript|python|react|vue|angular|nodejs|backend|frontend|development|programming)\b', content, re.IGNORECASE))
        
        noise_indicators = len(re.findall(r'\b(?:click here|subscribe now|follow us|like and share|comment below|notification bell|sponsor|affiliate link|advertisement|promo code|sale ends|discount expires|limited time|buy now|purchase today|order now|payment required|free trial expires|signup bonus|register today|login required)\b', content, re.IGNORECASE))
        
        # Ratio technique vs bruit - plus permissif
        if technical_terms + noise_indicators == 0:
            return True  # Pas assez de contenu pour juger, accepter
        
        # Si on a du contenu technique, c'est bon
        if technical_terms > 0:
            signal_ratio = technical_terms / (technical_terms + noise_indicators)
            return signal_ratio >= 0.15  # Réduit à 15% de contenu technique minimum
        
        # Si pas de termes techniques mais aussi pas de bruit, accepter
        return noise_indicators == 0
    
    def _is_promotional_or_spam(self, article: Dict) -> bool:
        """Détecte le contenu promotionnel ou spam"""
        full_text = (
            article.get('title', '') + ' ' + 
            article.get('summary', '') + ' ' + 
            article.get('content', '')[:2000]  # Premier 2000 chars
        ).lower()
        
        # Vérification des patterns de blocage
        for pattern in self.blocklist_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                return True
        
        # Vérification de la densité de mots-clés promotionnels
        promo_words = ['buy', 'purchase', 'sale', 'discount', 'offer', 'deal', 'free', 'trial', 'signup', 'register', 'subscribe', 'follow', 'like', 'share']
        promo_count = sum(1 for word in promo_words if word in full_text)
        
        words_total = len(full_text.split())
        if words_total > 0:
            promo_density = promo_count / words_total
            if promo_density > 0.05:  # Plus de 5% de mots promotionnels
                return True
        
        return False
    
    def _has_spam_indicators(self, article: Dict) -> bool:
        """Détecte les indicateurs de spam"""
        title = article.get('title', '')
        content = article.get('content', article.get('summary', ''))
        
        spam_indicators = [
            # Trop d'emojis
            len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', title)) > 3,
            
            # Trop de majuscules
            len(re.findall(r'[A-Z]', title)) / max(len(title), 1) > 0.5,
            
            # Trop de ponctuation
            len(re.findall(r'[!?]', title)) > 3,
            
            # Répétition excessive
            len(set(title.lower().split())) / max(len(title.split()), 1) < 0.6,
            
            # Mots en majuscules excessifs
            len([w for w in title.split() if w.isupper() and len(w) > 1]) > 2,
            
            # URL suspectes dans le contenu
            len(re.findall(r'bit\.ly|tinyurl|goo\.gl|t\.co', content)) > 0
        ]
        
        return sum(spam_indicators) >= 2  # Au moins 2 indicateurs de spam
    
    def _build_blocklist_patterns(self) -> List[str]:
        """Construit la liste des patterns à bloquer"""
        return [
            # Contenu promotionnel évident
            r'sponsored\s+post',
            r'affiliate\s+link',
            r'(buy|purchase)\s+now',
            r'limited\s+time\s+offer',
            r'click\s+here\s+to',
            r'sign\s+up\s+for\s+our',
            r'subscribe\s+to\s+our\s+newsletter',
            r'follow\s+us\s+on',
            r'like\s+and\s+subscribe',
            
            # Contenu marketing
            r'special\s+discount',
            r'exclusive\s+deal',
            r'act\s+now',
            r'don\'t\s+miss\s+out',
            r'hurry\s+up',
            r'while\s+supplies\s+last',
            
            # Contenu de faible qualité
            r'you\s+need\s+to\s+see\s+this',
            r'this\s+will\s+change\s+your\s+life',
            r'secret\s+that\s+\w+\s+don\'t\s+want',
            r'industry\s+doesn\'t\s+want\s+you\s+to\s+know',
            
            # Spam technique
            r'earn\s+\$\d+',
            r'make\s+money\s+online',
            r'work\s+from\s+home',
            r'get\s+rich\s+quick',
            
            # Contenu duplicate/scraped
            r'originally\s+published\s+at',
            r'cross[\s\-]posted\s+from',
            r'reposted\s+from',
            
            # Patterns de redirection
            r'read\s+more\s+at',
            r'continue\s+reading\s+at',
            r'full\s+article\s+at'
        ]
    
    def _build_quality_indicators(self) -> List[str]:
        """Construit les indicateurs de qualité faible"""
        return [
            # Listes clickbait
            r'top\s+\d+\s+(?:list|things?|ways?|tips?)',
            r'\d+\s+(?:amazing|incredible|unbelievable|shocking)',
            r'\d+\s+things?\s+you\s+(?:need|should|must)',
            
            # Titles sensationnalistes
            r'you\s+won\'t\s+believe',
            r'this\s+one\s+trick',
            r'shocking\s+truth',
            r'industry\s+secret',
            r'what\s+\w+\s+don\'t\s+want\s+you\s+to\s+know',
            
            # Contenu générique
            r'^(?:a|an|the)\s+complete\s+guide\s+to\s+\w+$',
            r'^(?:everything|all)\s+you\s+need\s+to\s+know\s+about',
            r'^(?:ultimate|definitive)\s+\w+\s+guide$',
            
            # Urgence artificielle
            r'urgent',
            r'breaking\s+news',
            r'just\s+announced',
            r'happening\s+now'
        ]
    
    def get_filter_stats(self, original_count: int, filtered_count: int, rejections: Dict[str, int]) -> Dict:
        """Génère des statistiques de filtrage"""
        total_rejected = sum(rejections.values())
        
        return {
            'original_count': original_count,
            'filtered_count': filtered_count,
            'rejected_count': total_rejected,
            'retention_rate': (filtered_count / original_count * 100) if original_count > 0 else 0,
            'rejection_breakdown': rejections,
            'top_rejection_reasons': sorted(
                [(reason, count) for reason, count in rejections.items() if count > 0], 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        }
    
    def validate_article_quality(self, article: Dict) -> Tuple[bool, List[str]]:
        """Valide un article individuel et retourne les raisons de rejet"""
        issues = []
        
        # Test de contenu valide
        if not self._has_valid_content(article):
            issues.append("Contenu insuffisant ou manquant")
        
        # Test de qualité du titre
        title_quality = self._check_title_quality(article)
        if not title_quality['passed']:
            issues.append(f"Titre de faible qualité: {title_quality['reason']}")
        
        # Test de qualité du contenu
        content_quality = self._check_content_quality(article)
        if not content_quality['passed']:
            issues.append(f"Contenu de faible qualité: {content_quality['reason']}")
        
        # Test promotionnel/spam
        if self._is_promotional_or_spam(article):
            issues.append("Contenu promotionnel ou spam détecté")
        
        # Test d'indicateurs de spam
        if self._has_spam_indicators(article):
            issues.append("Indicateurs de spam détectés")
        
        # Test de score de qualité
        if article.get('quality_score', 0) < self.quality_thresholds['min_quality_score']:
            issues.append(f"Score de qualité trop bas: {article.get('quality_score', 0)}")
        
        return len(issues) == 0, issues