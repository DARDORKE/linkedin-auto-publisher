# LinkedIn Auto Publisher

Système automatisé pour générer et publier des posts LinkedIn sur le domaine de la tech.

## Fonctionnalités

- **Scraping web automatique** : Récupère les dernières actualités tech depuis HackerNews, TechCrunch et TheVerge
- **Génération de contenu IA** : Utilise l'API Gemini pour créer des posts LinkedIn pertinents
- **Interface de validation** : Interface web pour approuver et éditer les posts avant publication
- **Publication automatisée** : Publie les posts approuvés directement sur LinkedIn

## Installation

1. Cloner le repository et installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Copier le fichier `.env.example` en `.env` et configurer les variables :
```bash
cp .env.example .env
```

3. Configurer les variables d'environnement :
- `GEMINI_API_KEY` : Clé API Google Gemini
- `LINKEDIN_EMAIL` : Email LinkedIn
- `LINKEDIN_PASSWORD` : Mot de passe LinkedIn
- `SCRAPING_INTERVAL_HOURS` : Intervalle de scraping (défaut: 6h)
- `MAX_ARTICLES_PER_SCRAPE` : Nombre max d'articles (défaut: 10)

## Utilisation

Lancer l'application :
```bash
python main.py
```

L'interface web sera disponible sur `http://localhost:5000`

## Architecture

- `src/scraper.py` : Bot de scraping pour récupérer les actualités tech
- `src/post_generator.py` : Génération de posts via l'API Gemini
- `src/linkedin_publisher.py` : Publication sur LinkedIn
- `src/web_interface.py` : Interface Flask pour la validation manuelle
- `src/database.py` : Gestion de la base de données SQLite
- `src/scheduler.py` : Orchestration et planification des tâches

## Workflow

1. Le scraper récupère automatiquement les dernières actualités tech
2. L'API Gemini génère 3 variations de posts LinkedIn
3. Les posts sont stockés en base de données
4. L'utilisateur valide/édite les posts via l'interface web
5. Les posts approuvés peuvent être publiés manuellement sur LinkedIn

## Sécurité

- Les credentials LinkedIn sont stockés dans les variables d'environnement
- L'interface web est protégée contre les injections XSS
- Les requêtes de scraping respectent un délai entre chaque source