from flask import Flask, request
from flask_restx import Api, Resource, fields, Namespace
from flask_cors import CORS
from src.database import DatabaseManager
from src.linkedin_publisher import LinkedInPublisher
from src.enhanced_scraper import EnhancedFullstackScraper
from src.specialized_generator import SpecializedPostGenerator
from src.websocket_service import websocket_service, generate_session_id
from loguru import logger
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Initialiser le service WebSocket
websocket_service.init_app(app)

# Configuration Swagger
api = Api(
    app,
    version='1.0.0',
    title='LinkedIn Auto Publisher API',
    description='API pour générer et publier automatiquement des posts LinkedIn à partir de sources d\'actualités tech',
    doc='/docs/',
    contact='Support',
    contact_email='support@example.com',
    license='MIT',
    license_url='https://opensource.org/licenses/MIT',
    prefix='/api'
)

# Namespaces
posts_ns = Namespace('posts', description='Gestion des posts LinkedIn')
scrape_ns = Namespace('scrape', description='Scraping d\'articles et génération de contenu')
domains_ns = Namespace('domains', description='Gestion des domaines technologiques')

api.add_namespace(posts_ns, path='/posts')
api.add_namespace(scrape_ns, path='/scrape')
api.add_namespace(domains_ns, path='/')

# Modèles Swagger
article_model = api.model('Article', {
    'title': fields.String(required=True, description='Titre de l\'article'),
    'url': fields.String(required=True, description='URL de l\'article'),
    'source': fields.String(required=True, description='Source de l\'article'),
    'summary': fields.String(description='Résumé de l\'article'),
    'content': fields.String(description='Contenu complet de l\'article'),
    'relevance_score': fields.Float(description='Score de pertinence'),
    'published': fields.String(description='Date de publication'),
    'domains': fields.List(fields.String(), description='Domaines associés')
})

post_model = api.model('Post', {
    'id': fields.Integer(required=True, description='ID du post'),
    'content': fields.String(required=True, description='Contenu du post'),
    'domain_name': fields.String(required=True, description='Domaine du post'),
    'hashtags': fields.List(fields.String(), description='Hashtags du post'),
    'source_articles': fields.List(fields.Nested(article_model), description='Articles sources'),
    'sources_count': fields.Integer(description='Nombre de sources'),
    'generated_at': fields.String(description='Date de génération'),
    'approved': fields.Boolean(description='Post approuvé'),
    'published': fields.Boolean(description='Post publié'),
    'published_at': fields.String(description='Date de publication')
})

domain_model = api.model('Domain', {
    'name': fields.String(required=True, description='Nom du domaine'),
    'description': fields.String(required=True, description='Description du domaine'),
    'color': fields.String(required=True, description='Couleur associée')
})

scrape_response_model = api.model('ScrapeResponse', {
    'success': fields.Boolean(required=True, description='Succès de l\'opération'),
    'articles': fields.List(fields.Nested(article_model), description='Articles trouvés'),
    'total_count': fields.Integer(description='Nombre total d\'articles'),
    'domain': fields.String(description='Domaine scrapé'),
    'from_cache': fields.Boolean(description='Données issues du cache')
})

# Initialisation
db = DatabaseManager()
scraper = None
generator = None

def get_scraper():
    global scraper
    if scraper is None:
        scraper = EnhancedFullstackScraper(db_manager=db)
    return scraper

def get_generator():
    global generator
    if generator is None:
        generator = SpecializedPostGenerator()
    return generator

# Routes Posts
@posts_ns.route('/pending')
class PendingPosts(Resource):
    @posts_ns.doc('get_pending_posts')
    @posts_ns.marshal_with(api.model('PostsList', {
        'posts': fields.List(fields.Nested(post_model))
    }))
    def get(self):
        """Récupère tous les posts en attente d'approbation"""
        posts = db.get_pending_posts()
        return {'posts': posts}

@posts_ns.route('/approved')
class ApprovedPosts(Resource):
    @posts_ns.doc('get_approved_posts')
    @posts_ns.marshal_with(api.model('PostsList', {
        'posts': fields.List(fields.Nested(post_model))
    }))
    def get(self):
        """Récupère tous les posts approuvés prêts à être publiés"""
        posts = db.get_approved_posts()
        return {'posts': posts}

@posts_ns.route('/approve/<int:post_id>')
class ApprovePost(Resource):
    @posts_ns.doc('approve_post')
    @posts_ns.marshal_with(api.model('SuccessResponse', {
        'success': fields.Boolean(),
        'message': fields.String()
    }))
    def post(self, post_id):
        """Approuve un post pour publication"""
        success = db.approve_post(post_id)
        if success:
            return {'success': True, 'message': 'Post approved'}
        return {'success': False, 'message': 'Post not found'}, 404

@posts_ns.route('/publish/<int:post_id>')
class PublishPost(Resource):
    @posts_ns.doc('publish_post')
    @posts_ns.marshal_with(api.model('SuccessResponse', {
        'success': fields.Boolean(),
        'message': fields.String()
    }))
    def post(self, post_id):
        """Publie un post approuvé sur LinkedIn"""
        posts = db.get_approved_posts()
        post = next((p for p in posts if p['id'] == post_id), None)
        
        if not post:
            return {'success': False, 'message': 'Post not found or not approved'}, 404
        
        try:
            publisher = LinkedInPublisher()
            success = publisher.publish_with_retry(post['content'])
            
            if success:
                db.mark_as_published(post_id)
                return {'success': True, 'message': 'Post published successfully'}
            else:
                return {'success': False, 'message': 'Failed to publish post'}, 500
                
        except Exception as e:
            logger.error(f"Error publishing post: {e}")
            return {'success': False, 'message': str(e)}, 500

@posts_ns.route('/delete/<int:post_id>')
class DeletePost(Resource):
    @posts_ns.doc('delete_post')
    @posts_ns.marshal_with(api.model('SuccessResponse', {
        'success': fields.Boolean(),
        'message': fields.String()
    }))
    def delete(self, post_id):
        """Supprime un post"""
        success = db.delete_post(post_id)
        if success:
            return {'success': True, 'message': 'Post deleted'}
        return {'success': False, 'message': 'Post not found'}, 404

@posts_ns.route('/edit/<int:post_id>')
class EditPost(Resource):
    @posts_ns.doc('edit_post')
    @posts_ns.expect(api.model('EditPostRequest', {
        'content': fields.String(required=True, description='Nouveau contenu du post')
    }))
    @posts_ns.marshal_with(api.model('SuccessResponse', {
        'success': fields.Boolean(),
        'message': fields.String()
    }))
    def put(self, post_id):
        """Modifie le contenu d'un post"""
        data = request.get_json()
        new_content = data.get('content')
        
        if not new_content:
            return {'success': False, 'message': 'Content is required'}, 400
        
        success = db.update_post_content(post_id, new_content)
        if success:
            return {'success': True, 'message': 'Post updated'}
        return {'success': False, 'message': 'Post not found'}, 404

# Routes Scraping
@scrape_ns.route('/<string:domain>')
class ScrapeDomain(Resource):
    @scrape_ns.doc('scrape_domain')
    @scrape_ns.expect(api.model('ScrapeRequest', {
        'force_refresh': fields.Boolean(description='Forcer le refresh (ignorer le cache)')
    }))
    @scrape_ns.marshal_with(api.model('ScrapeResponse', {
        'success': fields.Boolean(),
        'session_id': fields.String(),
        'articles': fields.List(fields.Nested(article_model)),
        'total_count': fields.Integer(),
        'domain': fields.String(),
        'from_cache': fields.Boolean()
    }))
    def post(self, domain):
        """Lance le scraping pour un domaine spécifique avec WebSocket"""
        try:
            valid_domains = ['frontend', 'backend', 'ai', 'all']
            if domain not in valid_domains:
                return {'success': False, 'message': f'Invalid domain. Valid domains: {valid_domains}'}, 400
            
            data = request.get_json() or {}
            force_refresh = data.get('force_refresh', False)
            
            # Limiter le nombre d'articles pour éviter les timeouts
            max_articles = 30 if domain == 'all' else 20
            
            # Générer un ID de session unique
            session_id = generate_session_id()
            
            logger.info(f"Starting scraping session {session_id} for domain: {domain}, force_refresh: {force_refresh}, max_articles: {max_articles}")
            
            # Démarrer la session WebSocket
            websocket_service.start_scraping_session(session_id, domain, max_articles)
            
            scraper = get_scraper()
            
            # Passer la session WebSocket au scraper
            scraper.set_websocket_session(session_id, websocket_service)
            
            if domain == 'all':
                articles = scraper.scrape_all_sources(max_articles=max_articles, use_cache=not force_refresh)
            else:
                articles = scraper.scrape_domain_sources(domain, max_articles=max_articles, use_cache=not force_refresh)
            
            articles = sorted(articles, key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            logger.info(f"Scraping completed for domain: {domain}, found {len(articles)} articles")
            
            # Terminer la session WebSocket
            results = {
                'total_articles': len(articles),
                'domain': domain,
                'from_cache': not force_refresh
            }
            websocket_service.complete_scraping_session(session_id, results)
            
            return {
                'success': True,
                'session_id': session_id,
                'articles': articles[:30],  # Limiter davantage pour l'interface
                'total_count': len(articles),
                'domain': domain,
                'from_cache': not force_refresh
            }
            
        except Exception as e:
            logger.error(f"Error scraping domain {domain}: {e}")
            if 'session_id' in locals():
                websocket_service.send_error(session_id, {
                    'type': 'scraping_error',
                    'message': str(e)
                })
            return {'success': False, 'message': str(e)}, 500

@scrape_ns.route('/generate-from-selection')
class GenerateFromSelection(Resource):
    @scrape_ns.doc('generate_from_selection')
    @scrape_ns.expect(api.model('GenerateRequest', {
        'articles': fields.List(fields.Nested(article_model), required=True, description='Articles sélectionnés'),
        'domain': fields.String(required=True, description='Domaine cible'),
        'numberOfPosts': fields.Integer(description='Nombre de posts à générer (1-5)', default=1)
    }))
    @scrape_ns.marshal_with(api.model('GenerateResponse', {
        'success': fields.Boolean(),
        'session_id': fields.String(),
        'post': fields.Nested(post_model),
        'posts': fields.List(fields.Nested(post_model)),
        'message': fields.String()
    }))
    def post(self):
        """Génère un ou plusieurs posts à partir d'articles sélectionnés avec WebSocket"""
        try:
            data = request.get_json()
            articles = data.get('articles', [])
            domain = data.get('domain')
            numberOfPosts = data.get('numberOfPosts', 1)
            
            if not articles or len(articles) < 2:
                return {'success': False, 'message': 'At least 2 articles required'}, 400
            
            if not domain:
                return {'success': False, 'message': 'Domain is required'}, 400
            
            # Valider numberOfPosts
            if numberOfPosts < 1 or numberOfPosts > 5:
                return {'success': False, 'message': 'Number of posts must be between 1 and 5'}, 400
            
            # Générer un ID de session unique
            session_id = generate_session_id()
            
            logger.info(f"Starting generation session {session_id} for domain: {domain} with {len(articles)} articles, {numberOfPosts} posts")
            
            # Démarrer la session WebSocket
            websocket_service.start_generation_session(session_id, domain, len(articles))
            
            generator = get_generator()
            
            generated_posts = []
            
            # Générer le nombre de posts demandé
            for i in range(numberOfPosts):
                logger.info(f"Generating post {i+1}/{numberOfPosts}")
                
                # Émettre le progrès de début pour ce post
                start_percentage = int((i / numberOfPosts) * 100)
                websocket_service.update_generation_progress(session_id, {
                    'type': 'post_generation',
                    'current_post': i + 1,
                    'total_posts': numberOfPosts,
                    'percentage': start_percentage,
                    'step': 'starting',
                    'domain': domain,
                    'articles_count': len(articles)
                })
                
                # Désactiver les WebSockets du générateur pour éviter les conflits
                generator.set_websocket_session(None, None)
                
                post_data = generator.generate_domain_post(articles, domain)
                
                if post_data:
                    post_id = db.save_post(post_data)
                    post_data['id'] = post_id
                    generated_posts.append(post_data)
                    
                    # Progrès de fin pour ce post
                    end_percentage = int(((i + 1) / numberOfPosts) * 100)
                    websocket_service.update_generation_progress(session_id, {
                        'type': 'post_generation',
                        'current_post': i + 1,
                        'total_posts': numberOfPosts,
                        'percentage': end_percentage,
                        'step': 'completed',
                        'post_id': post_id,
                        'domain': domain
                    })
                    
                    logger.info(f"Post {i+1}/{numberOfPosts} generated successfully with ID {post_id}")
                else:
                    logger.error(f"Failed to generate post {i+1}/{numberOfPosts}")
                    websocket_service.send_error(session_id, {
                        'type': 'generation_error',
                        'message': f'Failed to generate post {i+1}/{numberOfPosts}'
                    })
                    return {'success': False, 'message': f'Failed to generate post {i+1}/{numberOfPosts}'}, 500
            
            # Terminer la session WebSocket
            results = {
                'posts': generated_posts,
                'domain': domain,
                'articles_count': len(articles),
                'posts_count': len(generated_posts)
            }
            websocket_service.complete_generation_session(session_id, results)
            
            # Réponse conditionnelle selon le nombre de posts
            if numberOfPosts == 1:
                return {
                    'success': True,
                    'session_id': session_id,
                    'post': generated_posts[0],
                    'message': 'Post generated successfully'
                }
            else:
                return {
                    'success': True,
                    'session_id': session_id,
                    'posts': generated_posts,
                    'message': f'{len(generated_posts)} posts generated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error generating posts: {e}")
            if 'session_id' in locals():
                websocket_service.send_error(session_id, {
                    'type': 'generation_error',
                    'message': str(e)
                })
            return {'success': False, 'message': str(e)}, 500

# Routes Domains
@domains_ns.route('/domains')
class Domains(Resource):
    @domains_ns.doc('get_domains')
    @domains_ns.marshal_with(api.model('DomainsResponse', {
        'domains': fields.Raw(description='Dictionnaire des domaines disponibles')
    }))
    def get(self):
        """Récupère la liste des domaines technologiques disponibles"""
        domains = {
            'frontend': {
                'name': 'Développement Frontend',
                'description': 'JavaScript, React, Vue, Angular, CSS, HTML',
                'color': '#61DAFB'
            },
            'backend': {
                'name': 'Développement Backend', 
                'description': 'APIs, Node.js, Python, Go, PHP, Java, bases de données',
                'color': '#68D391'
            },
            'ai': {
                'name': 'Intelligence Artificielle',
                'description': 'Machine Learning, LLMs, Deep Learning',
                'color': '#9F7AEA'
            },
            'all': {
                'name': 'Tous les domaines',
                'description': 'Scraping complet de toutes les sources',
                'color': '#4A5568'
            }
        }
        return {'domains': domains}


# Route d'accueil avec info API
@app.route('/')
def api_info():
    return {
        'message': 'LinkedIn Auto Publisher API',
        'version': '1.0.0',
        'documentation': 'http://localhost:5000/docs/',
        'frontend_url': 'http://localhost:3000',
        'endpoints': {
            'posts': '/api/posts/',
            'scraping': '/api/scrape/',
            'domains': '/api/domains'
        }
    }


def run_web_interface():
    port = int(os.getenv('FLASK_PORT', 5000))
    # Utiliser socketio.run au lieu de app.run pour le support WebSocket
    websocket_service.socketio.run(app, host='0.0.0.0', port=port, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    import os
    run_web_interface()