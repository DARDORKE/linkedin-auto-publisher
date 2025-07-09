import { useState } from 'react';
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
} from '@mui/material';
import {
  Refresh,
  SelectAll,
  Clear,
  Send,
} from '@mui/icons-material';
import toast from 'react-hot-toast';
import { domainApi, scrapeApi, Article } from '../services/api';


export default function ManualScraping() {
  const queryClient = useQueryClient();
  const [selectedDomain, setSelectedDomain] = useState<string>('');
  const [selectedArticles, setSelectedArticles] = useState<number[]>([]);
  const [scrapedArticles, setScrapedArticles] = useState<Article[]>([]);
  const [scrapingTime, setScrapingTime] = useState<number | null>(null);

  const { data: domainsData } = useQuery({
    queryKey: ['domains'],
    queryFn: () => domainApi.getDomains(),
  });


  const scrapeMutation = useMutation({
    mutationFn: ({ domain }: { domain: string }) => {
      const startTime = Date.now();
      return scrapeApi.scrapeDomain(domain, false).then(response => {
        const endTime = Date.now();
        setScrapingTime(endTime - startTime);
        return response;
      });
    },
    onSuccess: (data) => {
      setScrapedArticles(data.data.articles);
      setSelectedArticles([]);
      
      const timeInfo = scrapingTime ? ` en ${scrapingTime}ms` : '';
      toast.success(`${data.data.total_count} articles trouvés${timeInfo}`);
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
      toast.success(data.data.message);
      queryClient.invalidateQueries({ queryKey: ['posts', 'pending'] });
      // Reset
      setSelectedArticles([]);
      setScrapedArticles([]);
      setSelectedDomain('');
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
    setSelectedArticles(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  const handleSelectAll = () => {
    setSelectedArticles(scrapedArticles.map((_, index) => index));
  };

  const handleClearAll = () => {
    setSelectedArticles([]);
  };

  const handleGenerate = () => {
    const articles = selectedArticles.map(index => scrapedArticles[index]);
    generateMutation.mutate({ articles, domain: selectedDomain });
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
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1}>
              <Typography variant="h6" component="div">
                {domain.name}
              </Typography>
            </Stack>
            <Typography variant="body2" color="text.secondary">
              {domain.description}
            </Typography>
            <Stack direction="row" alignItems="center" spacing={1} mt={1}>
              <Box
                sx={{
                  width: 20,
                  height: 20,
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
      <CardActionArea onClick={() => handleArticleToggle(index)}>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={selected}
                  onChange={() => handleArticleToggle(index)}
                />
              }
              label=""
              sx={{ mr: 1 }}
            />
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                {article.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {article.summary ? article.summary.substring(0, 150) : 'Aucun résumé disponible'}...
              </Typography>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Chip label={article.source} size="small" color="primary" variant="outlined" />
                <Chip 
                  label={`Score: ${Math.round(article.relevance_score)}`} 
                  size="small" 
                  color="secondary"
                  variant="outlined"
                />
              </Stack>
            </Box>
          </Stack>
        </CardContent>
      </CardActionArea>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Scraping Manuel
      </Typography>


      {/* Étape 1: Sélection du domaine */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            1. Choisir un domaine
          </Typography>
          <Grid container spacing={2}>
            {Object.entries(domains).map(([key, domain]) => (
              <Grid item xs={12} sm={6} md={3} key={key}>
                <DomainCard domainKey={key} domain={domain} />
              </Grid>
            ))}
          </Grid>
          <Box sx={{ mt: 2 }}>
            <Stack direction="row" spacing={2} alignItems="center" mb={2}>
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
          <CardContent>
            <Typography variant="h6" gutterBottom>
              2. Sélectionner les articles ({scrapedArticles.length} articles trouvés)
            </Typography>
            
            <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
              <Button
                variant="outlined"
                onClick={handleSelectAll}
                startIcon={<SelectAll />}
                size="small"
              >
                Tout sélectionner
              </Button>
              <Button
                variant="outlined"
                onClick={handleClearAll}
                startIcon={<Clear />}
                size="small"
              >
                Tout désélectionner
              </Button>
              <Chip
                label={`${selectedArticles.length} article${selectedArticles.length !== 1 ? 's' : ''} sélectionné${selectedArticles.length !== 1 ? 's' : ''}`}
                color="primary"
              />
            </Stack>

            <Grid container spacing={2}>
              {scrapedArticles.map((article, index) => (
                <Grid item xs={12} md={6} key={index}>
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
          <CardContent>
            <Typography variant="h6" gutterBottom>
              3. Générer le post
            </Typography>
            <Stack direction="row" spacing={2} alignItems="center">
              <Button
                variant="contained"
                color="success"
                onClick={handleGenerate}
                disabled={selectedArticles.length < 2 || generateMutation.isPending}
                startIcon={generateMutation.isPending ? <CircularProgress size={20} /> : <Send />}
              >
                {generateMutation.isPending ? 'Génération...' : 'Générer le post'}
              </Button>
              {selectedArticles.length < 2 && (
                <Alert severity="warning" sx={{ flex: 1 }}>
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
    </Box>
  );
}