"""
WebSocket service for real-time progress updates during scraping and generation
"""
from flask_socketio import SocketIO, emit
from typing import Dict, Any, Optional
from loguru import logger
import threading
import time
from datetime import datetime

class WebSocketService:
    """Service pour gérer les communications WebSocket en temps réel"""
    
    def __init__(self, app=None):
        self.socketio = None
        self.active_sessions = {}
        self.lock = threading.Lock()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialise le service WebSocket avec l'application Flask"""
        self.socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode='threading',
            logger=False,
            engineio_logger=False
        )
        
        # Enregistrer les handlers d'événements
        self._register_handlers()
        
        logger.info("WebSocket service initialized")
    
    def _register_handlers(self):
        """Enregistre les handlers d'événements WebSocket"""
        
        @self.socketio.on('connect')
        def handle_connect():
            from flask import request
            logger.info(f"Client connected: {request.sid}")
            emit('connected', {'status': 'connected'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            from flask import request
            logger.info(f"Client disconnected: {request.sid}")
            with self.lock:
                if hasattr(request, 'sid') and request.sid in self.active_sessions:
                    del self.active_sessions[request.sid]
        
        @self.socketio.on('join_scraping_session')
        def handle_join_scraping_session(data):
            """Client rejoint une session de scraping"""
            from flask import request
            session_id = data.get('session_id')
            if session_id:
                with self.lock:
                    self.active_sessions[request.sid] = {
                        'session_id': session_id,
                        'type': 'scraping',
                        'joined_at': datetime.now()
                    }
                logger.info(f"Client {request.sid} joined scraping session {session_id}")
                emit('session_joined', {'session_id': session_id})
        
        @self.socketio.on('join_generation_session')
        def handle_join_generation_session(data):
            """Client rejoint une session de génération"""
            from flask import request
            session_id = data.get('session_id')
            if session_id:
                with self.lock:
                    self.active_sessions[request.sid] = {
                        'session_id': session_id,
                        'type': 'generation',
                        'joined_at': datetime.now()
                    }
                logger.info(f"Client {request.sid} joined generation session {session_id}")
                emit('session_joined', {'session_id': session_id})
    
    def start_scraping_session(self, session_id: str, domain: str, max_articles: int) -> None:
        """Démarre une session de scraping"""
        if not self.socketio:
            return
            
        self.socketio.emit('scraping_started', {
            'session_id': session_id,
            'domain': domain,
            'max_articles': max_articles,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Started scraping session {session_id} for domain {domain}")
    
    def update_scraping_progress(self, session_id: str, progress_data: Dict[str, Any]) -> None:
        """Met à jour le progrès du scraping"""
        if not self.socketio:
            return
            
        # Ajouter timestamp et session_id
        progress_data.update({
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
        self.socketio.emit('scraping_progress', progress_data)
        
        # Logger les mises à jour importantes
        if progress_data.get('type') == 'source_completed':
            logger.info(f"Session {session_id}: Source {progress_data.get('source_name')} completed")
        elif progress_data.get('type') == 'domain_completed':
            logger.info(f"Session {session_id}: Domain {progress_data.get('domain')} completed")
    
    def complete_scraping_session(self, session_id: str, results: Dict[str, Any]) -> None:
        """Termine une session de scraping"""
        if not self.socketio:
            return
            
        self.socketio.emit('scraping_completed', {
            'session_id': session_id,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Completed scraping session {session_id} with {results.get('total_articles', 0)} articles")
    
    def start_generation_session(self, session_id: str, domain: str, articles_count: int) -> None:
        """Démarre une session de génération"""
        if not self.socketio:
            return
            
        self.socketio.emit('generation_started', {
            'session_id': session_id,
            'domain': domain,
            'articles_count': articles_count,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Started generation session {session_id} for domain {domain}")
    
    def update_generation_progress(self, session_id: str, progress_data: Dict[str, Any]) -> None:
        """Met à jour le progrès de la génération"""
        if not self.socketio:
            return
            
        # Ajouter timestamp et session_id
        progress_data.update({
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
        self.socketio.emit('generation_progress', progress_data)
        
        # Logger les étapes importantes
        if progress_data.get('type') == 'step_completed':
            logger.info(f"Session {session_id}: Step {progress_data.get('step')} completed")
    
    def complete_generation_session(self, session_id: str, results: Dict[str, Any]) -> None:
        """Termine une session de génération"""
        if not self.socketio:
            return
            
        self.socketio.emit('generation_completed', {
            'session_id': session_id,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Completed generation session {session_id}")
    
    def send_error(self, session_id: str, error_data: Dict[str, Any]) -> None:
        """Envoie une erreur au client"""
        if not self.socketio:
            return
            
        self.socketio.emit('error', {
            'session_id': session_id,
            'error': error_data,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.error(f"Error in session {session_id}: {error_data}")
    
    def get_active_sessions_count(self) -> int:
        """Retourne le nombre de sessions actives"""
        with self.lock:
            return len(self.active_sessions)


# Instance globale du service WebSocket
websocket_service = WebSocketService()

# Fonction helper pour générer des IDs de session
def generate_session_id() -> str:
    """Génère un ID de session unique"""
    import uuid
    return str(uuid.uuid4())