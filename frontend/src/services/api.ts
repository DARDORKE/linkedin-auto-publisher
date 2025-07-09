import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 180000, // 3 minutes pour les opérations de scraping
});

export interface Post {
  id: number;
  content: string;
  domain_name: string;
  hashtags: string[];
  source_articles: Array<{
    title: string;
    url: string;
    source: string;
  }>;
  sources_count: number;
  generated_at: string;
  approved: boolean;
  published: boolean;
  published_at?: string;
}

export interface Article {
  title: string;
  url: string;
  source: string;
  summary: string;
  relevance_score: number;
  domain_matches?: number;
  published: string;
}

export interface Domain {
  name: string;
  description: string;
  color: string;
}

export interface CacheStats {
  total_articles: number;
  fresh_articles: number;
  expired_articles: number;
}

export interface DomainCacheStats {
  cached_count: number;
  sources_count: number;
}

export const postApi = {
  getPending: () => api.get<{ posts: Post[] }>('/posts/pending'),
  getApproved: () => api.get<{ posts: Post[] }>('/posts/approved'),
  approve: (id: number) => api.post(`/posts/approve/${id}`),
  publish: (id: number) => api.post(`/posts/publish/${id}`),
  delete: (id: number) => api.delete(`/posts/delete/${id}`),
  update: (id: number, content: string) => api.put(`/posts/edit/${id}`, { content }),
};

export const scrapeApi = {
  scrapeDomain: (domain: string, forceRefresh = false) =>
    api.post<{
      success: boolean;
      articles: Article[];
      total_count: number;
      domain: string;
      from_cache: boolean;
    }>(`/scrape/${domain}`, { force_refresh: forceRefresh }),
  
  generateFromSelection: (articles: Article[], domain: string) =>
    api.post<{
      success: boolean;
      post: Post;
      message: string;
    }>('/generate-from-selection', { articles, domain }),
};

export const domainApi = {
  getDomains: () => api.get<{ domains: Record<string, Domain> }>('/domains'),
  getCacheStats: () => api.get<CacheStats>('/cache/stats'),
  getCacheByDomains: () => api.get<Record<string, DomainCacheStats>>('/cache/domains'),
};

export default api;