import { useEffect, useState, useCallback } from 'react';
import { 
  websocketService, 
  WebSocketCallbacks, 
  ScrapingProgressEvent, 
  GenerationProgressEvent, 
  SessionStartedEvent, 
  SessionCompletedEvent,
  WebSocketError
} from '../services/websocket';

export interface WebSocketState {
  isConnected: boolean;
  currentSession: string | null;
  sessionType: 'scraping' | 'generation' | null;
  progress: {
    type: string;
    message: string;
    percentage: number;
    details: any;
  } | null;
  error: string | null;
}

export interface UseWebSocketOptions {
  onScrapingStarted?: (data: SessionStartedEvent) => void;
  onScrapingProgress?: (data: ScrapingProgressEvent) => void;
  onScrapingCompleted?: (data: SessionCompletedEvent) => void;
  onGenerationStarted?: (data: SessionStartedEvent) => void;
  onGenerationProgress?: (data: GenerationProgressEvent) => void;
  onGenerationCompleted?: (data: SessionCompletedEvent) => void;
  onError?: (data: WebSocketError) => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    currentSession: null,
    sessionType: null,
    progress: null,
    error: null,
  });

  const updateProgress = useCallback((type: string, message: string, percentage: number, details: any = null) => {
    setState(prev => ({
      ...prev,
      progress: { type, message, percentage, details }
    }));
  }, []);

  const calculateScrapingProgress = useCallback((data: ScrapingProgressEvent): { message: string; percentage: number } => {
    switch (data.type) {
      case 'domain_started':
        return {
          message: `Début du scraping ${data.domain}...`,
          percentage: 10
        };
      case 'sources_started':
        return {
          message: `Scraping de ${(data as any).sources_count || 0} sources...`,
          percentage: 20
        };
      case 'source_completed':
        const sourceProgress = data.completed_sources && data.total_sources 
          ? (data.completed_sources / data.total_sources) * 60 
          : 30;
        return {
          message: `Source ${data.source_name} terminée (${data.articles_found} articles)`,
          percentage: 20 + sourceProgress
        };
      case 'processing_started':
        return {
          message: `Traitement de ${(data as any).total_articles || 0} articles...`,
          percentage: 80
        };
      case 'processing_completed':
        return {
          message: `Sélection finale: ${data.final_articles} articles`,
          percentage: 95
        };
      case 'domain_completed':
        return {
          message: `Domaine ${data.domain} terminé (${data.articles_found} articles)`,
          percentage: 100
        };
      default:
        return { message: 'En cours...', percentage: 50 };
    }
  }, []);

  const calculateGenerationProgress = useCallback((data: GenerationProgressEvent): { message: string; percentage: number } => {
    switch (data.type) {
      case 'generation_started':
        return {
          message: `Génération d'un post ${data.domain} avec ${data.articles_count} articles...`,
          percentage: 10
        };
      case 'step_completed':
        return {
          message: `Étape ${data.step} terminée...`,
          percentage: 50
        };
      case 'generation_completed':
        return {
          message: 'Post généré avec succès !',
          percentage: 100
        };
      case 'generation_failed':
        return {
          message: 'Échec de la génération',
          percentage: 0
        };
      default:
        return { message: 'Génération en cours...', percentage: 50 };
    }
  }, []);

  useEffect(() => {
    const callbacks: WebSocketCallbacks = {
      onConnected: () => {
        setState(prev => ({ ...prev, isConnected: true, error: null }));
      },
      onDisconnected: () => {
        setState(prev => ({ ...prev, isConnected: false }));
      },
      onScrapingStarted: (data) => {
        setState(prev => ({
          ...prev,
          currentSession: data.session_id,
          sessionType: 'scraping',
          progress: null,
          error: null
        }));
        updateProgress('scraping_started', `Début du scraping ${data.domain}...`, 0, data);
        options.onScrapingStarted?.(data);
      },
      onScrapingProgress: (data) => {
        const { message, percentage } = calculateScrapingProgress(data);
        updateProgress('scraping_progress', message, percentage, data);
        options.onScrapingProgress?.(data);
      },
      onScrapingCompleted: (data) => {
        updateProgress('scraping_completed', 'Scraping terminé !', 100, data);
        setState(prev => ({ ...prev, sessionType: null, currentSession: null }));
        options.onScrapingCompleted?.(data);
      },
      onGenerationStarted: (data) => {
        setState(prev => ({
          ...prev,
          currentSession: data.session_id,
          sessionType: 'generation',
          progress: null,
          error: null
        }));
        updateProgress('generation_started', `Génération d'un post ${data.domain}...`, 0, data);
        options.onGenerationStarted?.(data);
      },
      onGenerationProgress: (data) => {
        const { message, percentage } = calculateGenerationProgress(data);
        updateProgress('generation_progress', message, percentage, data);
        options.onGenerationProgress?.(data);
      },
      onGenerationCompleted: (data) => {
        updateProgress('generation_completed', 'Post généré avec succès !', 100, data);
        setState(prev => ({ ...prev, sessionType: null, currentSession: null }));
        options.onGenerationCompleted?.(data);
      },
      onError: (data) => {
        setState(prev => ({
          ...prev,
          error: data.error.message,
          progress: null,
          sessionType: null,
          currentSession: null
        }));
        options.onError?.(data);
      }
    };

    websocketService.setCallbacks(callbacks);

    return () => {
      // Cleanup des callbacks lors du démontage
      websocketService.setCallbacks({});
    };
  }, [options, updateProgress, calculateScrapingProgress, calculateGenerationProgress]);

  const joinScrapingSession = useCallback((sessionId: string) => {
    websocketService.joinScrapingSession(sessionId);
  }, []);

  const joinGenerationSession = useCallback((sessionId: string) => {
    websocketService.joinGenerationSession(sessionId);
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const clearProgress = useCallback(() => {
    setState(prev => ({ ...prev, progress: null }));
  }, []);

  return {
    ...state,
    joinScrapingSession,
    joinGenerationSession,
    clearError,
    clearProgress,
  };
};

export default useWebSocket;