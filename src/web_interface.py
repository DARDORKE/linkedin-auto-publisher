from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from src.database import DatabaseManager
from src.linkedin_publisher import LinkedInPublisher
from loguru import logger
import os

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

db = DatabaseManager()

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

def run_web_interface():
    port = int(os.getenv('FLASK_PORT', 5000))
    # Avoid debug mode in threading environment
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)