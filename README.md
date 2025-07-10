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
- **API**: Flask RESTful avec WebSocket
- **Base de données**: SQLite avec SQLAlchemy
- **Scraping**: BeautifulSoup + Feedparser
- **IA**: Google Gemini API
- **Containerisé**: Docker

## Fonctionnalités

### 🎯 Tableau de bord
- Vue d'ensemble des posts et statistiques
- Graphiques de répartition des posts
- Suivi en temps réel avec WebSocket

### 📝 Gestion des posts
- **Posts en attente**: Validation et approbation
- **Posts approuvés**: Publication sur LinkedIn
- **Édition**: Modification du contenu avant publication

### 🔍 Scraping intelligent
- **3 domaines**: Frontend, Backend, IA
- **Sources multiples**: 58+ sources RSS fiables
- **Suivi temps réel**: Progress WebSocket
- **Scoring avancé**: Pertinence par domaine

### 🤖 Génération automatique
- **IA spécialisée**: Prompts adaptés par domaine
- **Tone journalistique**: Contenu professionnel
- **Sources citées**: URLs et références
- **Hashtags optimisés**: LinkedIn-friendly

## Démarrage rapide

### Prérequis
- Docker et Docker Compose
- Make (optionnel, mais recommandé)
- Clé API Google Gemini

### Installation automatique
```bash
# Configuration initiale (crée .env, dossiers requis)
make install

# Éditer le fichier .env avec votre clé API
nano .env
```

### Déploiement rapide
```bash
# Déploiement complet (build + start)
make deploy

# Redéploiement (down + build + up)
make redeploy
```

### Commandes disponibles
```bash
make help          # Afficher toutes les commandes
make build         # Construire les images Docker
make up            # Démarrer l'application
make down          # Arrêter l'application
make deploy        # Déploiement complet
make redeploy      # Redéploiement complet
make status        # Statut des conteneurs
make check         # Vérifier si les services fonctionnent
make logs          # Voir les logs en temps réel
make clean         # Nettoyer conteneurs et volumes
```

### Méthode manuelle (sans Makefile)
```bash
# Configuration
echo "GEMINI_API_KEY=your_api_key" > .env

# Lancement
docker-compose up -d
```

## URLs d'accès

- **Application principale**: http://localhost:3000
- **API Backend**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs/

## Développement

### Monitoring des services
```bash
make status  # Voir l'état des conteneurs
make logs    # Suivre les logs en temps réel
make check   # Vérifier que les services répondent
```

### Développement local frontend
```bash
cd frontend
npm install
npm run dev  # Frontend sur http://localhost:5173
```

### Maintenance
```bash
# Mise à jour après modifications
make redeploy

# Nettoyage complet
make clean
```

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
│   ├── api_docs.py    # API endpoints avec Swagger
│   ├── websocket_service.py  # Service WebSocket
│   └── scheduler.py   # Planificateur de tâches
├── docker-compose.yml
└── requirements.txt
```

## Performance

### Optimisations
- Proxy Nginx pour le frontend
- WebSocket pour le temps réel
- Scraping différentiel par domaine
- Compression gzip
- Build Docker optimisé

## API Endpoints

### Posts
- `GET /api/posts/pending` - Posts en attente
- `GET /api/posts/approved` - Posts approuvés
- `POST /api/posts/approve/{id}` - Approuver un post
- `POST /api/posts/publish/{id}` - Publier un post

### Scraping
- `POST /api/scrape/{domain}` - Scraper un domaine avec WebSocket
- `POST /api/scrape/generate-from-selection` - Générer depuis sélection

### Domaines
- `GET /api/domains` - Liste des domaines disponibles

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
- Configurer un reverse proxy (nginx)
- Activer HTTPS
- Monitoring avec Prometheus
- Rate limiting avancé

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