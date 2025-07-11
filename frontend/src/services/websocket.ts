import { io, Socket } from 'socket.io-client';

// Types pour les événements WebSocket
export interface ScrapingProgressEvent {
  session_id: string;
  type: 'domain_started' | 'domain_completed' | 'sources_started' | 'source_completed' | 'source_error' | 'processing_started' | 'processing_completed';
  domain?: string;
  source_name?: string;
  articles_found?: number;
  completed_sources?: number;
  total_sources?: number;
  processed_articles?: number;
  final_articles?: number;
  target_articles?: number;
  total_domains?: number;
  error?: string;
  timestamp: string;
}

export interface GenerationProgressEvent {
  session_id: string;
  type: 'generation_started' | 'generation_completed' | 'generation_failed' | 'generation_error' | 'step_completed' | 'post_generation';
  domain?: string;
  articles_count?: number;
  post_generated?: boolean;
  step?: string;
  percentage?: number;
  current_post?: number;
  total_posts?: number;
  post_id?: number;
  error?: string;
  timestamp: string;
}

export interface WebSocketError {
  session_id: string;
  error: {
    type: string;
    message: string;
  };
  timestamp: string;
}

export interface SessionStartedEvent {
  session_id: string;
  domain: string;
  max_articles?: number;
  articles_count?: number;
  timestamp: string;
}

export interface SessionCompletedEvent {
  session_id: string;
  results: {
    total_articles?: number;
    domain?: string;
    from_cache?: boolean;
    post_id?: number;
    articles_count?: number;
    posts?: any[];
    posts_count?: number;
  };
  timestamp: string;
}

// Interface pour les callbacks
export interface WebSocketCallbacks {
  onScrapingStarted?: (data: SessionStartedEvent) => void;
  onScrapingProgress?: (data: ScrapingProgressEvent) => void;
  onScrapingCompleted?: (data: SessionCompletedEvent) => void;
  onGenerationStarted?: (data: SessionStartedEvent) => void;
  onGenerationProgress?: (data: GenerationProgressEvent) => void;
  onGenerationCompleted?: (data: SessionCompletedEvent) => void;
  onError?: (data: WebSocketError) => void;
  onConnected?: () => void;
  onDisconnected?: () => void;
}

class WebSocketService {
  private socket: Socket | null = null;
  private callbacks: WebSocketCallbacks = {};
  private isConnected = false;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor() {
    this.connect();
  }

  private connect(): void {
    try {
      // Connexion au serveur WebSocket
      this.socket = io('http://localhost:5000', {
        transports: ['websocket'],
        upgrade: false,
        autoConnect: true,
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
      });

      this.registerEventHandlers();
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
    }
  }

  private registerEventHandlers(): void {
    if (!this.socket) return;

    // Événements de connexion
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.isConnected = true;
      this.callbacks.onConnected?.();
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      this.isConnected = false;
      this.callbacks.onDisconnected?.();
    });

    this.socket.on('connect_error', (error: any) => {
      console.error('WebSocket connection error:', error);
      this.isConnected = false;
    });

    // Événements de session
    this.socket.on('session_joined', (data: any) => {
      console.log('Joined session:', data);
    });

    // Événements de scraping
    this.socket.on('scraping_started', (data: SessionStartedEvent) => {
      console.log('Scraping started:', data);
      this.callbacks.onScrapingStarted?.(data);
    });

    this.socket.on('scraping_progress', (data: ScrapingProgressEvent) => {
      console.log('Scraping progress:', data);
      this.callbacks.onScrapingProgress?.(data);
    });

    this.socket.on('scraping_completed', (data: SessionCompletedEvent) => {
      console.log('Scraping completed:', data);
      this.callbacks.onScrapingCompleted?.(data);
    });

    // Événements de génération
    this.socket.on('generation_started', (data: SessionStartedEvent) => {
      console.log('Generation started:', data);
      this.callbacks.onGenerationStarted?.(data);
    });

    this.socket.on('generation_progress', (data: GenerationProgressEvent) => {
      console.log('Generation progress:', data);
      this.callbacks.onGenerationProgress?.(data);
    });

    this.socket.on('generation_completed', (data: SessionCompletedEvent) => {
      console.log('Generation completed:', data);
      this.callbacks.onGenerationCompleted?.(data);
    });

    // Événements d'erreur
    this.socket.on('error', (data: WebSocketError) => {
      console.error('WebSocket error:', data);
      this.callbacks.onError?.(data);
    });
  }

  public setCallbacks(callbacks: WebSocketCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  public joinScrapingSession(sessionId: string): void {
    if (this.socket && this.isConnected) {
      this.socket.emit('join_scraping_session', { session_id: sessionId });
    }
  }

  public joinGenerationSession(sessionId: string): void {
    if (this.socket && this.isConnected) {
      this.socket.emit('join_generation_session', { session_id: sessionId });
    }
  }

  public disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  public getConnectionStatus(): boolean {
    return this.isConnected;
  }

  public reconnect(): void {
    if (this.socket) {
      this.socket.connect();
    } else {
      this.connect();
    }
  }
}

// Instance singleton
export const websocketService = new WebSocketService();
export default websocketService;