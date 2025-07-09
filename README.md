# LinkedIn Auto Publisher - Frontend React

Une application complète pour générer et publier automatiquement des posts LinkedIn à partir de sources d'actualités tech.

## Architecture

### Frontend (React + TypeScript)
- **Framework**: React 18 avec TypeScript
- **UI**: Material-UI + Tailwind CSS
- **État**: TanStack Query pour la gestion d'état serveur
- **Routing**: React Router v6
- **Build**: Vite
- **Containerisé**: Docker avec Nginx

### Backend (Flask + Python)
- **API**: Flask RESTful
- **Base de données**: SQLite avec SQLAlchemy
- **Scraping**: BeautifulSoup + Feedparser
- **IA**: Google Gemini API
- **Cache**: Système de cache intelligent (6h)
- **Containerisé**: Docker

## Fonctionnalités

### 🎯 Tableau de bord
- Vue d'ensemble des posts et statistiques
- Graphiques de répartition des posts
- Monitoring du cache par domaine

### 📝 Gestion des posts
- **Posts en attente**: Validation et approbation
- **Posts approuvés**: Publication sur LinkedIn
- **Édition**: Modification du contenu avant publication

### 🔍 Scraping intelligent
- **3 domaines**: Frontend, Backend, IA
- **Sources multiples**: 58+ sources RSS fiables
- **Cache optimisé**: Performance 330x améliorée
- **Scoring avancé**: Pertinence par domaine

### 🤖 Génération automatique
- **IA spécialisée**: Prompts adaptés par domaine
- **Tone journalistique**: Contenu professionnel
- **Sources citées**: URLs et références
- **Hashtags optimisés**: LinkedIn-friendly

## Démarrage rapide

### Prérequis
- Docker et Docker Compose
- Clé API Google Gemini

### Configuration
1. Cloner le projet
2. Créer le fichier `.env`:
```bash
GEMINI_API_KEY=your_gemini_api_key
LINKEDIN_USERNAME=your_linkedin_username
LINKEDIN_PASSWORD=your_linkedin_password
```

### Lancement
```bash
# Lancer l'application complète
docker-compose up -d

# Accéder à l'application
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000
```

### Développement
```bash
# Frontend uniquement
cd frontend
npm install
npm run dev

# Backend uniquement
docker-compose up backend
```

## URLs d'accès

- **Application principale**: http://localhost:3000
- **API Backend**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs/

## Architecture technique

### Services Docker
- **frontend**: React app (port 3000)
- **backend**: Flask API (port 5000)
- **linkedin-net**: Réseau interne

### Structure des dossiers
```
├── frontend/           # Application React
│   ├── src/
│   │   ├── components/ # Composants réutilisables
│   │   ├── pages/      # Pages principales
│   │   ├── services/   # API calls
│   │   └── ...
│   ├── Dockerfile
│   └── nginx.conf
├── src/               # Backend Flask
│   ├── database.py    # Models SQLAlchemy
│   ├── fullstack_scraper.py  # Scraping engine
│   ├── specialized_generator.py  # IA generation
│   └── web_interface.py  # API endpoints
├── docker-compose.yml
└── requirements.txt
```

## Performance

### Cache intelligent
- **Avant**: 20-80 secondes par scraping
- **Après**: 0.06 secondes (cache hit)
- **Amélioration**: 330x à 1300x plus rapide

### Optimisations
- Proxy Nginx pour le frontend
- Cache Redis-like en SQLite
- Scraping différentiel par domaine
- Compression gzip

## API Endpoints

### Posts
- `GET /api/posts/pending` - Posts en attente
- `GET /api/posts/approved` - Posts approuvés
- `POST /api/posts/approve/{id}` - Approuver un post
- `POST /api/posts/publish/{id}` - Publier un post

### Scraping
- `POST /api/scrape/{domain}` - Scraper un domaine
- `POST /api/generate-from-selection` - Générer depuis sélection

### Cache
- `GET /api/cache/stats` - Statistiques générales
- `GET /api/cache/domains` - Stats par domaine

## Développement

### Ajout de nouvelles sources
1. Modifier `src/fullstack_scraper.py`
2. Ajouter la source dans `self.sources`
3. Spécifier le domaine et la catégorie

### Modification des prompts IA
1. Éditer `src/specialized_generator.py`
2. Modifier les prompts dans `_generate_domain_post`

### Nouveaux composants React
1. Créer dans `frontend/src/components/`
2. Utiliser TypeScript et Material-UI
3. Intégrer TanStack Query pour les données

## Production

### Optimisations recommandées
- Utiliser PostgreSQL au lieu de SQLite
- Ajouter Redis pour le cache
- Configurer un reverse proxy (nginx)
- Activer HTTPS
- Monitoring avec Prometheus

### Sécurité
- Utiliser des secrets Docker
- Validator les entrées utilisateur
- Rate limiting sur l'API
- Authentification JWT

## Roadmap

- [ ] Authentification utilisateur
- [ ] Planification des publications
- [ ] Analytics des performances
- [ ] Support multi-plateforme (Twitter, Facebook)
- [ ] Dashboard admin avancé
- [ ] Tests automatisés
- [ ] CI/CD pipeline