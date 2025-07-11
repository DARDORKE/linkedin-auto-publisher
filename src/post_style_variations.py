"""
Module pour gérer les variations de style et de structure des posts LinkedIn
"""
import random
from typing import Dict, List, Tuple
from datetime import datetime

class PostStyleVariations:
    def __init__(self):
        # Définir différents formats de posts
        self.post_formats = {
            'storytelling': {
                'name': 'Storytelling',
                'description': 'Format narratif avec une histoire ou anecdote',
                'structure': [
                    'hook_story',
                    'context_narrative',
                    'development_story',
                    'lesson_learned',
                    'call_to_action_story'
                ]
            },
            'listicle': {
                'name': 'Liste structurée',
                'description': 'Format liste avec points numérotés',
                'structure': [
                    'hook_number',
                    'intro_list',
                    'numbered_points',
                    'conclusion_list',
                    'engagement_question'
                ]
            },
            'question_driven': {
                'name': 'Question-réponse',
                'description': 'Commence par une question provocante',
                'structure': [
                    'opening_question',
                    'context_problem',
                    'solutions_explored',
                    'key_insight',
                    'follow_up_question'
                ]
            },
            'comparison': {
                'name': 'Comparaison',
                'description': 'Compare deux approches ou technologies',
                'structure': [
                    'hook_comparison',
                    'option_a',
                    'option_b',
                    'analysis',
                    'recommendation'
                ]
            },
            'breaking_news': {
                'name': 'Breaking News',
                'description': 'Format actualité urgente',
                'structure': [
                    'breaking_hook',
                    'what_happened',
                    'why_important',
                    'implications',
                    'stay_tuned'
                ]
            },
            'deep_dive': {
                'name': 'Analyse approfondie',
                'description': 'Format technique détaillé',
                'structure': [
                    'technical_hook',
                    'problem_statement',
                    'technical_analysis',
                    'practical_applications',
                    'expert_question'
                ]
            },
            'hot_take': {
                'name': 'Opinion tranchée',
                'description': 'Format opinion forte',
                'structure': [
                    'controversial_hook',
                    'thesis_statement',
                    'supporting_arguments',
                    'counter_perspective',
                    'debate_invitation'
                ]
            },
            'tutorial_mini': {
                'name': 'Mini tutoriel',
                'description': 'Format éducatif rapide',
                'structure': [
                    'learning_hook',
                    'what_youll_learn',
                    'step_by_step',
                    'pro_tip',
                    'practice_suggestion'
                ]
            }
        }
        
        # Variations de tons
        self.tone_variations = {
            'enthusiastic': {
                'name': 'Enthousiaste',
                'characteristics': ['exclamations', 'superlatifs', 'énergie positive'],
                'emoji_style': 'abundant',
                'sentence_style': 'short_punchy'
            },
            'analytical': {
                'name': 'Analytique',
                'characteristics': ['données', 'métriques', 'objectivité'],
                'emoji_style': 'minimal',
                'sentence_style': 'structured'
            },
            'conversational': {
                'name': 'Conversationnel',
                'characteristics': ['questions rhétoriques', 'langage familier', 'proximité'],
                'emoji_style': 'moderate',
                'sentence_style': 'varied'
            },
            'authoritative': {
                'name': 'Autoritaire',
                'characteristics': ['affirmations fortes', 'expertise', 'confiance'],
                'emoji_style': 'strategic',
                'sentence_style': 'declarative'
            },
            'curious': {
                'name': 'Curieux',
                'characteristics': ['questions ouvertes', 'exploration', 'découverte'],
                'emoji_style': 'thoughtful',
                'sentence_style': 'interrogative'
            },
            'pragmatic': {
                'name': 'Pragmatique',
                'characteristics': ['solutions concrètes', 'ROI', 'résultats'],
                'emoji_style': 'professional',
                'sentence_style': 'direct'
            }
        }
        
        # Variations d'ouvertures
        self.opening_variations = {
            'stat_shock': [
                "📊 {stat}% des développeurs {domain} ne savent pas que...",
                "🎯 Chiffre du jour: {stat} {metric} grâce à {technology}",
                "📈 +{stat}% de performance avec cette nouvelle approche {domain}"
            ],
            'question_hook': [
                "🤔 Vous êtes-vous déjà demandé pourquoi {technology} {action}?",
                "💭 Et si je vous disais que {bold_statement}?",
                "❓ {technology} ou {alternative}? La réponse va vous surprendre..."
            ],
            'story_opener': [
                "📖 Il y a {timeframe}, personne n'aurait imaginé que {outcome}...",
                "🎬 Scène: Un développeur {domain} découvre {discovery}...",
                "💡 L'histoire commence avec un simple problème de {problem}..."
            ],
            'breaking_opener': [
                "🚨 FLASH: {company} vient d'annoncer {announcement}",
                "⚡ BREAKING: {technology} révolutionne {domain} avec {feature}",
                "🔥 À L'INSTANT: La communauté {domain} en ébullition après {event}"
            ],
            'controversial_opener': [
                "🎯 Opinion impopulaire: {technology} est surcoté(e).",
                "💣 Il est temps d'arrêter de prétendre que {common_belief}",
                "🔥 Hot take: {bold_statement} (et voici pourquoi)"
            ]
        }
        
        # Variations de conclusions
        self.closing_variations = {
            'question_engage': [
                "💬 Quelle est votre expérience avec {topic}?",
                "🤝 Êtes-vous team {option1} ou team {option2}?",
                "💭 Comment voyez-vous l'évolution de {technology}?"
            ],
            'call_to_action': [
                "📌 Sauvegardez ce post pour votre prochaine revue tech!",
                "🔄 Partagez si vous pensez que {statement}",
                "👇 Dites-moi en commentaire votre approche préférée"
            ],
            'prediction': [
                "🔮 Prédiction: {technology} deviendra incontournable d'ici {timeframe}",
                "📅 Rendez-vous dans 6 mois pour voir si j'avais raison!",
                "🚀 Le futur de {domain}? Un indice: {hint}"
            ],
            'challenge': [
                "🎯 Challenge de la semaine: essayez {technology} sur un projet",
                "💪 Qui relève le défi d'implémenter {feature} cette semaine?",
                "🏆 Partagez vos résultats avec #Challenge{Technology}"
            ]
        }
        
        # Styles d'emojis variés
        self.emoji_styles = {
            'tech_minimal': ['💻', '🔧', '⚡', '🚀', '📊'],
            'colorful': ['🌟', '🎨', '🌈', '✨', '🎯', '💎', '🔮'],
            'professional': ['📈', '📊', '🎯', '✅', '🔍', '📌'],
            'playful': ['🚀', '🎢', '🎪', '🎭', '🎨', '🌟', '⚡'],
            'scientific': ['🔬', '🧪', '📐', '🔭', '🧬', '⚗️'],
            'nature': ['🌱', '🌳', '🌊', '⛰️', '🌅', '🌿']
        }
        
    def get_random_format(self, context: Dict) -> Dict:
        """Sélectionne un format aléatoire adapté au contexte"""
        # Filtrer les formats selon le contexte
        suitable_formats = []
        
        urgency = context.get('urgency_level', 'normal')
        temporal = context.get('temporal_context', 'current')
        article_types = context.get('article_types', [])
        
        # Logique de sélection basée sur le contexte
        if urgency == 'high' or temporal == 'breaking':
            suitable_formats = ['breaking_news', 'hot_take', 'question_driven']
        elif 'tutorial' in article_types or 'educational' in article_types:
            suitable_formats = ['tutorial_mini', 'listicle', 'deep_dive']
        elif 'analytical' in article_types:
            suitable_formats = ['deep_dive', 'comparison', 'question_driven']
        elif temporal == 'trending':
            suitable_formats = ['hot_take', 'comparison', 'storytelling']
        else:
            # Par défaut, tous les formats sont possibles
            suitable_formats = list(self.post_formats.keys())
        
        # Sélection aléatoire parmi les formats adaptés
        selected_format = random.choice(suitable_formats)
        return self.post_formats[selected_format]
    
    def get_random_tone(self, format_type: str) -> Dict:
        """Sélectionne un ton aléatoire adapté au format"""
        # Certains tons sont mieux adaptés à certains formats
        tone_compatibility = {
            'breaking_news': ['enthusiastic', 'authoritative', 'analytical'],
            'storytelling': ['conversational', 'curious', 'enthusiastic'],
            'listicle': ['pragmatic', 'analytical', 'authoritative'],
            'question_driven': ['curious', 'conversational', 'analytical'],
            'comparison': ['analytical', 'pragmatic', 'authoritative'],
            'deep_dive': ['analytical', 'authoritative', 'pragmatic'],
            'hot_take': ['authoritative', 'enthusiastic', 'conversational'],
            'tutorial_mini': ['pragmatic', 'conversational', 'enthusiastic']
        }
        
        suitable_tones = tone_compatibility.get(format_type, list(self.tone_variations.keys()))
        selected_tone = random.choice(suitable_tones)
        return self.tone_variations[selected_tone]
    
    def get_opening_line(self, style: str, context: Dict) -> str:
        """Génère une ligne d'ouverture selon le style"""
        openings = self.opening_variations.get(style, self.opening_variations['question_hook'])
        template = random.choice(openings)
        
        # Remplacer les placeholders avec des valeurs du contexte
        replacements = {
            '{stat}': str(random.randint(40, 95)),
            '{metric}': random.choice(['requêtes/seconde', 'ms de latence', 'de temps gagné']),
            '{technology}': context.get('main_technology', 'cette technologie'),
            '{domain}': context.get('domain_name', 'tech'),
            '{action}': random.choice(['change tout', 'révolutionne le game', 'devient incontournable']),
            '{bold_statement}': self._generate_bold_statement(context),
            '{alternative}': context.get('alternative_tech', 'l\'ancienne méthode'),
            '{timeframe}': random.choice(['3 mois', '6 mois', 'un an']),
            '{outcome}': self._generate_outcome(context),
            '{company}': random.choice(context.get('key_companies', [['Une major tech']])[0]) if context.get('key_companies') else 'Une entreprise majeure',
            '{announcement}': self._generate_announcement(context),
            '{feature}': self._generate_feature(context),
            '{event}': self._generate_event(context),
            '{problem}': random.choice(['performance', 'scalabilité', 'sécurité', 'UX']),
            '{common_belief}': self._generate_common_belief(context),
            '{discovery}': self._generate_discovery(context)
        }
        
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, str(value))
        
        return template
    
    def get_closing_line(self, style: str, context: Dict) -> str:
        """Génère une ligne de conclusion selon le style"""
        closings = self.closing_variations.get(style, self.closing_variations['question_engage'])
        template = random.choice(closings)
        
        # Remplacer les placeholders
        replacements = {
            '{topic}': context.get('main_topic', 'ces nouvelles approches'),
            '{option1}': context.get('tech1', 'nouvelle approche'),
            '{option2}': context.get('tech2', 'méthode classique'),
            '{technology}': context.get('main_technology', 'cette technologie'),
            '{statement}': self._generate_statement(context),
            '{timeframe}': random.choice(['2025', 'fin 2024', '18 mois']),
            '{domain}': context.get('domain_name', 'tech'),
            '{hint}': self._generate_hint(context),
            '{feature}': self._generate_feature(context),
            '{Technology}': context.get('main_technology', 'Tech').capitalize()
        }
        
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, str(value))
        
        return template
    
    def get_emoji_set(self, style: str) -> List[str]:
        """Retourne un set d'emojis selon le style"""
        return self.emoji_styles.get(style, self.emoji_styles['tech_minimal'])
    
    def vary_sentence_structure(self, text: str, style: str) -> str:
        """Varie la structure des phrases selon le style"""
        if style == 'short_punchy':
            # Diviser les phrases longues
            text = text.replace(', mais', '.\n\n💥 Mais')
            text = text.replace(', et', '.\n\n✨ Et')
            text = text.replace(' car ', '.\n\n📌 Pourquoi? ')
        elif style == 'interrogative':
            # Ajouter plus de questions
            text = text.replace('Il est important de', 'Pourquoi est-il important de')
            text = text.replace('Cela permet', 'Comment cela permet-il')
        elif style == 'structured':
            # Ajouter de la structure
            text = text.replace('Premièrement,', '1️⃣ ')
            text = text.replace('Deuxièmement,', '2️⃣ ')
            text = text.replace('Enfin,', '3️⃣ ')
        
        return text
    
    # Méthodes helper pour générer du contenu contextuel
    def _generate_bold_statement(self, context: Dict) -> str:
        statements = [
            f"{context.get('main_technology', 'cette approche')} rend obsolète 50% des pratiques actuelles",
            f"la majorité des devs {context.get('domain', 'tech')} passent à côté de cette innovation",
            "ce qui fonctionnait hier ne suffira plus demain"
        ]
        return random.choice(statements)
    
    def _generate_outcome(self, context: Dict) -> str:
        outcomes = [
            f"{context.get('main_technology', 'cette technologie')} dominerait le marché",
            "les performances seraient multipliées par 10",
            "le développement serait si rapide"
        ]
        return random.choice(outcomes)
    
    def _generate_announcement(self, context: Dict) -> str:
        announcements = [
            f"une mise à jour majeure de {context.get('main_technology', 'sa plateforme')}",
            "un partenariat stratégique game-changing",
            "des fonctionnalités qui changent tout"
        ]
        return random.choice(announcements)
    
    def _generate_feature(self, context: Dict) -> str:
        features = [
            "l'auto-optimisation",
            "le support natif du edge computing",
            "l'intégration IA native",
            "la scalabilité infinie"
        ]
        return random.choice(features)
    
    def _generate_event(self, context: Dict) -> str:
        events = [
            "cette annonce surprise",
            "ce benchmark controversé",
            "cette migration massive",
            "ce retournement de situation"
        ]
        return random.choice(events)
    
    def _generate_common_belief(self, context: Dict) -> str:
        beliefs = [
            f"{context.get('main_technology', 'cette approche')} est la meilleure solution",
            "les anciennes méthodes sont dépassées",
            "plus c'est complexe, mieux c'est"
        ]
        return random.choice(beliefs)
    
    def _generate_discovery(self, context: Dict) -> str:
        discoveries = [
            "une optimisation 10x plus rapide",
            "la solution à un bug vieux de 5 ans",
            "une approche révolutionnaire"
        ]
        return random.choice(discoveries)
    
    def _generate_statement(self, context: Dict) -> str:
        statements = [
            f"{context.get('main_technology', 'cette innovation')} va transformer notre industrie",
            "c'est le futur du développement",
            "chaque développeur devrait connaître ça"
        ]
        return random.choice(statements)
    
    def _generate_hint(self, context: Dict) -> str:
        hints = [
            "pensez automatisation totale",
            "l'IA est la clé",
            "la simplicité gagne toujours"
        ]
        return random.choice(hints)
    
    def format_with_variations(self, content: str, format_type: str, tone: Dict) -> str:
        """Applique les variations de format et de ton au contenu"""
        # Appliquer le style de phrases
        content = self.vary_sentence_structure(content, tone['sentence_style'])
        
        # Ajuster le niveau d'emojis
        if tone['emoji_style'] == 'minimal':
            # Réduire les emojis
            emoji_count = content.count('🔥') + content.count('💡') + content.count('🚀')
            if emoji_count > 3:
                # Supprimer certains emojis
                content = content.replace('🔥 ', '', 1)
                content = content.replace('💡 ', '', 1)
        elif tone['emoji_style'] == 'abundant':
            # Ajouter plus d'emojis
            content = content.replace('. ', '. ✨ ', 1)
            content = content.replace('! ', '! 🎯 ', 1)
        
        return content