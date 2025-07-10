import { useState } from 'react';

// Fonction pour obtenir la couleur d'une technologie
const getTechColor = (tech: string): string => {
  const techColors: Record<string, string> = {
    // Frontend
    'react': '#61DAFB',
    'vue': '#4FC08D',
    'angular': '#DD0031',
    'svelte': '#FF3E00',
    'css': '#1572B6',
    'javascript': '#F7DF1E',
    'typescript': '#3178C6',
    'tooling': '#FF6B6B',
    'testing': '#8CC84B',
    'mobile': '#A663CC',
    'performance': '#FFA500',
    
    // Backend
    'nodejs': '#339933',
    'python': '#3776AB',
    'java': '#ED8B00',
    'go': '#00ADD8',
    'rust': '#CE422B',
    'php': '#777BB4',
    'ruby': '#CC342D',
    'dotnet': '#512BD4',
    'databases': '#336791',
    'devops': '#2496ED',
    'cloud': '#FF9900',
    'api': '#009688',
    
    // AI
    'llms': '#FF6B35',
    'ml_frameworks': '#FF6F00',
    'nlp': '#8E24AA',
    'computer_vision': '#1976D2',
    'mlops': '#00897B',
    'data_science': '#FFC107',
    'ai_tools': '#E91E63',
    'research': '#9C27B0',
    'ethics': '#795548',
    
    // Default
    'general': '#6C757D'
  };
  
  return techColors[tech] || '#6C757D';
};
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Button,
  Chip,
  Checkbox,
  FormControlLabel,
  Stack,
  Alert,
  CircularProgress,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh,
  SelectAll,
  Clear,
  Send,
  Visibility,
  OpenInNew,
} from '@mui/icons-material';
import toast from 'react-hot-toast';
import { domainApi, scrapeApi, Article } from '../services/api';
import LoadingScreen from '../components/LoadingScreen';
import ArticleModal from '../components/ArticleModal';
import useWebSocket from '../hooks/useWebSocket';


const MAX_SELECTED_ARTICLES = 5;

export default function ManualScraping() {
  const queryClient = useQueryClient();
  const [selectedDomain, setSelectedDomain] = useState<string>('');
  const [selectedArticles, setSelectedArticles] = useState<number[]>([]);
  const [scrapedArticles, setScrapedArticles] = useState<Article[]>([]);
  const [scrapingTime, setScrapingTime] = useState<number | null>(null);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [isArticleModalOpen, setIsArticleModalOpen] = useState(false);

  const { data: domainsData } = useQuery({
    queryKey: ['domains'],
    queryFn: () => domainApi.getDomains(),
  });

  // WebSocket hook pour suivre les progrès en temps réel
  const webSocketState = useWebSocket({
    onScrapingStarted: () => {
      setScrapingTime(Date.now());
    },
    onScrapingCompleted: (data) => {
      if (scrapingTime) {
        const endTime = Date.now();
        setScrapingTime(endTime - scrapingTime);
      }
      toast.success(`${data.results.total_articles} articles trouvés`);
    },
    onGenerationCompleted: () => {
      toast.success('Post généré avec succès');
      queryClient.invalidateQueries({ queryKey: ['posts', 'pending'] });
      // Reset
      setSelectedArticles([]);
      setScrapedArticles([]);
      setSelectedDomain('');
    },
    onError: (data) => {
      toast.error(`Erreur: ${data.error.message}`);
    },
  });


  const scrapeMutation = useMutation({
    mutationFn: ({ domain }: { domain: string }) => {
      return scrapeApi.scrapeDomain(domain, false);
    },
    onSuccess: (data) => {
      setScrapedArticles(data.data.articles);
      setSelectedArticles([]);
      
      // Rejoindre la session WebSocket si elle existe
      if (data.data.session_id) {
        webSocketState.joinScrapingSession(data.data.session_id);
      }
    },
    onError: () => {
      toast.error('Erreur lors du scraping');
      setScrapingTime(null);
    },
  });

  const generateMutation = useMutation({
    mutationFn: ({ articles, domain }: { articles: Article[]; domain: string }) =>
      scrapeApi.generateFromSelection(articles, domain),
    onSuccess: (data) => {
      // Rejoindre la session WebSocket si elle existe
      if (data.data.session_id) {
        webSocketState.joinGenerationSession(data.data.session_id);
      }
      // Le toast et reset sont gérés par le WebSocket callback
    },
    onError: () => {
      toast.error('Erreur lors de la génération');
    },
  });

  const domains = domainsData?.data.domains || {};

  const handleDomainSelect = (domain: string) => {
    setSelectedDomain(domain);
    setSelectedArticles([]);
    setScrapedArticles([]);
    setScrapingTime(null);
  };

  const handleScrape = () => {
    if (!selectedDomain) return;
    scrapeMutation.mutate({ domain: selectedDomain });
  };


  const handleArticleToggle = (index: number) => {
    setSelectedArticles(prev => {
      if (prev.includes(index)) {
        return prev.filter(i => i !== index);
      } else if (prev.length >= MAX_SELECTED_ARTICLES) {
        toast.error(`Vous ne pouvez sélectionner que ${MAX_SELECTED_ARTICLES} articles maximum`);
        return prev;
      } else {
        return [...prev, index];
      }
    });
  };

  const handleSelectAll = () => {
    const indicesToSelect = scrapedArticles.slice(0, MAX_SELECTED_ARTICLES).map((_, index) => index);
    setSelectedArticles(indicesToSelect);
    if (scrapedArticles.length > MAX_SELECTED_ARTICLES) {
      toast.success(`Seuls les ${MAX_SELECTED_ARTICLES} premiers articles ont été sélectionnés`);
    }
  };

  const handleClearAll = () => {
    setSelectedArticles([]);
  };

  const handleGenerate = () => {
    const articles = selectedArticles.map(index => scrapedArticles[index]);
    generateMutation.mutate({ articles, domain: selectedDomain });
  };

  const handleOpenArticle = (article: Article) => {
    setSelectedArticle(article);
    setIsArticleModalOpen(true);
  };

  const handleCloseArticle = () => {
    setSelectedArticle(null);
    setIsArticleModalOpen(false);
  };

  const DomainCard = ({ domainKey, domain }: { domainKey: string; domain: any }) => {
    const isSelected = selectedDomain === domainKey;

    return (
      <Card 
        sx={{ 
          border: isSelected ? '2px solid #0a66c2' : '1px solid #e0e0e0',
          backgroundColor: isSelected ? '#f0f8ff' : 'white',
          position: 'relative',
        }}
      >
        <CardActionArea onClick={() => handleDomainSelect(domainKey)}>
          <CardContent sx={{ px: { xs: 2, sm: 3 }, py: { xs: 2, sm: 3 } }}>
            <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1}>
              <Typography variant="h6" component="div" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                {domain.name}
              </Typography>
            </Stack>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
              {domain.description}
            </Typography>
            <Stack direction="row" alignItems="center" spacing={1} mt={1}>
              <Box
                sx={{
                  width: { xs: 16, sm: 20 },
                  height: { xs: 16, sm: 20 },
                  borderRadius: '50%',
                  backgroundColor: domain.color,
                }}
              />
            </Stack>
          </CardContent>
        </CardActionArea>
      </Card>
    );
  };

  const ArticleCard = ({ article, index, selected }: { article: Article; index: number; selected: boolean }) => (
    <Card 
      sx={{ 
        border: selected ? '2px solid #0a66c2' : '1px solid #e0e0e0',
        backgroundColor: selected ? '#f0f8ff' : 'white',
      }}
    >
      <CardContent sx={{ px: { xs: 2, sm: 3 }, py: { xs: 2, sm: 3 } }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1}>
          <FormControlLabel
            control={
              <Checkbox
                checked={selected}
                onChange={() => handleArticleToggle(index)}
                disabled={!selected && selectedArticles.length >= MAX_SELECTED_ARTICLES}
              />
            }
            label=""
            sx={{ mr: 1 }}
          />
          <Box sx={{ flex: 1 }} onClick={() => handleArticleToggle(index)}>
            <Typography variant="subtitle2" gutterBottom sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
              {article.title}
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
              {article.summary ? article.summary.substring(0, 150) : 'Aucun résumé disponible'}...
            </Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }} spacing={{ xs: 1, sm: 0 }}>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                <Chip label={article.source} size="small" color="primary" variant="outlined" />
                <Chip 
                  label={`Score: ${Math.round(article.relevance_score)}`} 
                  size="small" 
                  color="secondary"
                  variant="outlined"
                />
                {article.primary_technology && article.primary_technology !== 'general' && (
                  <Chip 
                    label={article.primary_technology} 
                    size="small" 
                    sx={{
                      backgroundColor: getTechColor(article.primary_technology),
                      color: 'white',
                      fontWeight: 'bold',
                      '&:hover': {
                        backgroundColor: getTechColor(article.primary_technology),
                        opacity: 0.8,
                      }
                    }}
                  />
                )}
              </Stack>
              <Stack direction="row" spacing={1}>
                <Tooltip title="Voir le contenu">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleOpenArticle(article);
                    }}
                  >
                    <Visibility />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Ouvrir l'article original">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(article.url, '_blank');
                    }}
                  >
                    <OpenInNew />
                  </IconButton>
                </Tooltip>
              </Stack>
            </Stack>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ fontSize: { xs: '1.5rem', sm: '2rem', md: '2.5rem' } }}>
        Scraping Manuel
      </Typography>


      {/* Étape 1: Sélection du domaine */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ px: { xs: 2, sm: 3 }, py: { xs: 2, sm: 3 } }}>
          <Typography variant="h6" gutterBottom sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
            1. Choisir un domaine
          </Typography>
          <Grid container spacing={{ xs: 2, sm: 2, md: 3 }}>
            {Object.entries(domains).map(([key, domain]) => (
              <Grid item xs={12} sm={6} lg={3} key={key}>
                <DomainCard domainKey={key} domain={domain} />
              </Grid>
            ))}
          </Grid>
          <Box sx={{ mt: 2 }}>
            <Stack direction="row" spacing={2} alignItems="center" mb={2} flexWrap="wrap" useFlexGap>
              {scrapingTime && (
                <Chip
                  label={`${scrapingTime}ms`}
                  size="small"
                  color="info"
                  variant="outlined"
                />
              )}
            </Stack>
            
            <Stack direction="row" spacing={2}>
              <Button
                variant="contained"
                onClick={handleScrape}
                disabled={!selectedDomain || scrapeMutation.isPending}
                startIcon={scrapeMutation.isPending ? <CircularProgress size={20} /> : <Refresh />}
                sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
              >
                {scrapeMutation.isPending ? 'Scraping...' : 'Lancer le scraping'}
              </Button>
            </Stack>
          </Box>
        </CardContent>
      </Card>

      {/* Étape 2: Sélection des articles */}
      {scrapedArticles.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ px: { xs: 2, sm: 3 }, py: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" gutterBottom sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              2. Sélectionner les articles ({scrapedArticles.length} articles trouvés)
            </Typography>
            
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }} flexWrap="wrap" useFlexGap>
              <Button
                variant="outlined"
                onClick={handleSelectAll}
                startIcon={<SelectAll />}
                size="small"
                sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
              >
                Tout sélectionner
              </Button>
              <Button
                variant="outlined"
                onClick={handleClearAll}
                startIcon={<Clear />}
                size="small"
                sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
              >
                Tout désélectionner
              </Button>
              <Chip
                label={`${selectedArticles.length}/${MAX_SELECTED_ARTICLES} articles sélectionnés`}
                color={selectedArticles.length >= MAX_SELECTED_ARTICLES ? "warning" : "primary"}
                size="small"
              />
            </Stack>
            
            <Alert severity="info" sx={{ mb: 2, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
              Vous pouvez sélectionner jusqu'à {MAX_SELECTED_ARTICLES} articles maximum pour éviter de surcharger le prompt.
            </Alert>

            <Grid container spacing={{ xs: 2, sm: 2, md: 3 }}>
              {scrapedArticles.map((article, index) => (
                <Grid item xs={12} lg={6} key={index}>
                  <ArticleCard
                    article={article}
                    index={index}
                    selected={selectedArticles.includes(index)}
                  />
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Étape 3: Génération */}
      {selectedArticles.length > 0 && (
        <Card>
          <CardContent sx={{ px: { xs: 2, sm: 3 }, py: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" gutterBottom sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              3. Générer le post
            </Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ xs: 'stretch', sm: 'center' }}>
              <Button
                variant="contained"
                color="success"
                onClick={handleGenerate}
                disabled={selectedArticles.length < 2 || generateMutation.isPending}
                startIcon={generateMutation.isPending ? <CircularProgress size={20} /> : <Send />}
                sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
              >
                {generateMutation.isPending ? 'Génération...' : 'Générer le post'}
              </Button>
              {selectedArticles.length < 2 && (
                <Alert severity="warning" sx={{ flex: 1, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                  Sélectionnez au moins 2 articles pour générer un post
                </Alert>
              )}
            </Stack>
            {generateMutation.isPending && (
              <LinearProgress sx={{ mt: 2 }} />
            )}
          </CardContent>
        </Card>
      )}

      <LoadingScreen
        open={scrapeMutation.isPending || webSocketState.sessionType === 'scraping'}
        title="Scraping en cours..."
        description="Récupération des articles depuis les sources RSS"
        showProgress={true}
        progress={webSocketState.progress?.percentage}
        realTimeMessage={webSocketState.progress?.message}
        progressDetails={webSocketState.progress?.details}
        sessionType={webSocketState.sessionType}
      />

      <LoadingScreen
        open={generateMutation.isPending || webSocketState.sessionType === 'generation'}
        title="Génération en cours..."
        description="Création du post LinkedIn à partir des articles sélectionnés"
        showProgress={true}
        progress={webSocketState.progress?.percentage}
        realTimeMessage={webSocketState.progress?.message}
        progressDetails={webSocketState.progress?.details}
        sessionType={webSocketState.sessionType}
      />

      <ArticleModal
        open={isArticleModalOpen}
        onClose={handleCloseArticle}
        article={selectedArticle}
      />
    </Box>
  );
}