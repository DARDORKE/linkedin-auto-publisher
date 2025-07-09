from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from src.database import DatabaseManager
from src.linkedin_publisher import LinkedInPublisher
from src.fullstack_scraper import FullStackDevScraper
from src.specialized_generator import SpecializedPostGenerator
from loguru import logger
import os
import json
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

db = DatabaseManager()
scraper = None  # Initialize only when needed
generator = None  # Initialize only when needed

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/posts/pending')
def get_pending_posts():
    posts = db.get_pending_posts()
    return jsonify({'posts': posts})

@app.route('/api/posts/approved')
def get_approved_posts():
    posts = db.get_approved_posts()
    return jsonify({'posts': posts})

@app.route('/api/posts/approve/<int:post_id>', methods=['POST'])
def approve_post(post_id):
    success = db.approve_post(post_id)
    if success:
        return jsonify({'success': True, 'message': 'Post approved'})
    return jsonify({'success': False, 'message': 'Post not found'}), 404

@app.route('/api/posts/publish/<int:post_id>', methods=['POST'])
def publish_post(post_id):
    posts = db.get_approved_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if not post:
        return jsonify({'success': False, 'message': 'Post not found or not approved'}), 404
    
    try:
        publisher = LinkedInPublisher()
        success = publisher.publish_with_retry(post['content'])
        
        if success:
            db.mark_as_published(post_id)
            return jsonify({'success': True, 'message': 'Post published successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to publish post'}), 500
            
    except Exception as e:
        logger.error(f"Error publishing post: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/posts/delete/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    success = db.delete_post(post_id)
    if success:
        return jsonify({'success': True, 'message': 'Post deleted'})
    return jsonify({'success': False, 'message': 'Post not found'}), 404

@app.route('/api/posts/edit/<int:post_id>', methods=['PUT'])
def edit_post(post_id):
    data = request.get_json()
    new_content = data.get('content')
    
    if not new_content:
        return jsonify({'success': False, 'message': 'Content is required'}), 400
    
    success = db.update_post_content(post_id, new_content)
    if success:
        return jsonify({'success': True, 'message': 'Post updated'})
    return jsonify({'success': False, 'message': 'Post not found'}), 404

@app.route('/api/scrape/<domain>', methods=['POST'])
def scrape_domain(domain):
    """Lance le scraping pour un domaine spécifique"""
    try:
        # Valider le domaine
        valid_domains = ['frontend', 'backend', 'ai', 'all']
        if domain not in valid_domains:
            return jsonify({'success': False, 'message': f'Domaine invalide. Domaines valides: {valid_domains}'}), 400
        
        # Récupérer le paramètre force_refresh
        data = request.get_json() or {}
        force_refresh = data.get('force_refresh', False)
        
        logger.info(f"Starting manual scraping for domain: {domain}, force_refresh: {force_refresh}")
        
        # Initialize scraper if not already done
        global scraper
        if scraper is None:
            scraper = FullStackDevScraper(db_manager=db)
        
        # Scraper selon le domaine sélectionné
        if domain == 'all':
            articles = scraper.scrape_all_sources(max_articles=100, use_cache=not force_refresh)
        else:
            # Scraper seulement les sources du domaine choisi
            articles = scraper.scrape_domain_sources(domain, max_articles=50, use_cache=not force_refresh)
        
        # Trier par score de pertinence
        articles = sorted(articles, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        logger.info(f"Scraped {len(articles)} articles for domain {domain}")
        
        return jsonify({
            'success': True,
            'articles': articles[:50],  # Limiter pour l'interface
            'total_count': len(articles),
            'domain': domain,
            'from_cache': not force_refresh
        })
        
    except Exception as e:
        logger.error(f"Error scraping domain {domain}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/generate-from-selection', methods=['POST'])
def generate_from_selection():
    """Génère un post à partir d'articles sélectionnés"""
    try:
        data = request.get_json()
        selected_articles = data.get('articles', [])
        domain = data.get('domain', 'general')
        
        if not selected_articles:
            return jsonify({'success': False, 'message': 'Aucun article sélectionné'}), 400
        
        if len(selected_articles) < 2:
            return jsonify({'success': False, 'message': 'Sélectionnez au moins 2 articles'}), 400
        
        logger.info(f"Generating post from {len(selected_articles)} selected articles for domain {domain}")
        
        # Organiser les articles par domaine pour le générateur
        articles_by_domain = {domain: selected_articles}
        
        # Initialize generator if not already done
        global generator
        if generator is None:
            generator = SpecializedPostGenerator()
        
        # Générer le post spécialisé
        post = generator._generate_domain_post(domain, selected_articles)
        
        if not post:
            return jsonify({'success': False, 'message': 'Erreur lors de la génération du post'}), 500
        
        # Sauvegarder en base
        post_id = db.save_post(post)
        post['id'] = post_id
        
        logger.info(f"Generated and saved post {post_id} from manual selection")
        
        return jsonify({
            'success': True,
            'post': post,
            'message': f'Post généré avec succès à partir de {len(selected_articles)} articles'
        })
        
    except Exception as e:
        logger.error(f"Error generating post from selection: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/domains')
def get_domains():
    """Retourne la liste des domaines disponibles"""
    domains = {
        'frontend': {
            'name': 'Développement Frontend',
            'description': 'JavaScript, React, Vue, Angular, CSS, HTML',
            'color': '#61DAFB'
        },
        'backend': {
            'name': 'Développement Backend', 
            'description': 'APIs, Node.js, Python, Java, bases de données',
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
    
    return jsonify({'domains': domains})

@app.route('/api/cache/stats')
def get_cache_stats():
    """Retourne les statistiques du cache d'articles"""
    stats = db.get_cache_stats()
    return jsonify(stats)

@app.route('/api/cache/domains')
def get_cache_by_domains():
    """Retourne le nombre d'articles en cache par domaine"""
    try:
        # Initialize scraper if needed
        global scraper
        if scraper is None:
            scraper = FullStackDevScraper(db_manager=db)
        
        domain_stats = {}
        for domain in ['frontend', 'backend', 'ai']:
            # Obtenir les sources du domaine
            domain_sources = []
            domain_categories = {
                'frontend': ['frontend', 'dev_fr', 'community'],
                'backend': ['backend', 'dev_fr', 'devops', 'enterprise', 'community'],
                'ai': ['ai', 'dev_fr', 'community'],
            }
            
            target_categories = domain_categories.get(domain, [])
            for source in scraper.sources:
                source_category = source.get('category', '')
                source_domains = source.get('domains', [])
                if source_category in target_categories or domain in source_domains:
                    domain_sources.append(source['name'])
            
            # Compter les articles en cache pour ce domaine
            cached_articles = db.get_cached_articles(source_names=domain_sources)
            domain_stats[domain] = {
                'cached_count': len(cached_articles),
                'sources_count': len(domain_sources)
            }
        
        return jsonify(domain_stats)
    except Exception as e:
        logger.error(f"Error getting cache stats by domain: {e}")
        return jsonify({})

def run_web_interface():
    port = int(os.getenv('FLASK_PORT', 5000))
    # Avoid debug mode in threading environment
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)