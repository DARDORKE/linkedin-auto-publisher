import React, { useState } from 'react';

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
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Box,
  Link,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  CheckCircle,
  Publish,
  Edit,
  Delete,
  ExpandMore,
  ExpandLess,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import toast from 'react-hot-toast';
import { Post } from '../services/api';

interface Props {
  post: Post;
  type: 'pending' | 'approved';
  onApprove?: (id: number) => Promise<any>;
  onPublish?: (id: number) => Promise<any>;
  onDelete?: (id: number) => Promise<any>;
  onUpdate?: (id: number, content: string) => Promise<any>;
}

export default function PostCard({ post, type, onApprove, onPublish, onDelete, onUpdate }: Props) {
  const [editOpen, setEditOpen] = useState(false);
  const [editContent, setEditContent] = useState(post.content);
  const [showSources, setShowSources] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleAction = async (action: () => Promise<void>, successMessage: string) => {
    setLoading(true);
    try {
      await action();
      toast.success(successMessage);
    } catch (error) {
      toast.error('Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = () => {
    if (onUpdate) {
      handleAction(
        () => onUpdate(post.id, editContent),
        'Post modifié avec succès'
      ).then(() => setEditOpen(false));
    }
  };

  const formatContent = (content: string) => {
    return content.split('\n').map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < content.split('\n').length - 1 && <br />}
      </React.Fragment>
    ));
  };

  return (
    <>
      <Card sx={{ mb: { xs: 1.5, sm: 2 } }}>
        <CardContent sx={{ px: { xs: 2, sm: 3 }, py: { xs: 2, sm: 3 } }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', sm: 'center' }} gap={{ xs: 1, sm: 0 }} mb={2}>
            <Chip 
              label={post.domain_name} 
              color="primary" 
              size="small" 
            />
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}>
              {format(new Date(post.generated_at), 'dd MMMM yyyy HH:mm', { locale: fr })}
            </Typography>
          </Stack>

          <Typography variant="body1" paragraph sx={{ whiteSpace: 'pre-wrap', fontSize: { xs: '0.875rem', sm: '1rem' }, lineHeight: { xs: 1.5, sm: 1.6 } }}>
            {formatContent(post.content)}
          </Typography>

          <Stack direction="row" spacing={1} flexWrap="wrap" mb={2} useFlexGap>
            {post.hashtags.map((tag, index) => (
              <Chip
                key={index}
                label={tag}
                size="small"
                sx={{ 
                  backgroundColor: '#e7f3ff',
                  color: '#0a66c2',
                  mb: 0.5,
                  fontSize: { xs: '0.7rem', sm: '0.75rem' }
                }}
              />
            ))}
          </Stack>

          {/* Tags technologiques basés sur les articles sources */}
          {(() => {
            const technologies = Array.from(new Set(
              post.source_articles
                .map(article => (article as any).primary_technology)
                .filter(tech => tech && tech !== 'general')
            ));
            
            if (technologies.length > 0) {
              return (
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mt: 1 }}>
                  <Typography variant="caption" sx={{ alignSelf: 'center', fontSize: { xs: '0.7rem', sm: '0.75rem' } }}>
                    Technologies:
                  </Typography>
                  {technologies.map((tech, index) => (
                    <Chip 
                      key={index}
                      label={tech} 
                      size="small" 
                      sx={{
                        backgroundColor: getTechColor(tech),
                        color: 'white',
                        fontWeight: 'bold',
                        fontSize: { xs: '0.65rem', sm: '0.7rem' },
                        height: { xs: '20px', sm: '24px' },
                        '&:hover': {
                          backgroundColor: getTechColor(tech),
                          opacity: 0.8,
                        }
                      }}
                    />
                  ))}
                </Stack>
              );
            }
            return null;
          })()}

          <Box>
            <Button
              size="small"
              onClick={() => setShowSources(!showSources)}
              endIcon={showSources ? <ExpandLess /> : <ExpandMore />}
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            >
              {post.source_articles?.length || 0} articles utilisés
            </Button>
            <Collapse in={showSources}>
              <Box sx={{ mt: 1, pl: { xs: 1, sm: 2 } }}>
                {post.source_articles.map((article, index) => (
                  <Typography key={index} variant="caption" display="block" sx={{ mb: 0.5, fontSize: { xs: '0.7rem', sm: '0.75rem' } }}>
                    • <Link href={article.url} target="_blank" rel="noopener">
                      {article.title}
                    </Link> ({article.source})
                  </Typography>
                ))}
              </Box>
            </Collapse>
          </Box>
        </CardContent>

        <CardActions sx={{ px: { xs: 2, sm: 3 }, py: { xs: 1, sm: 2 }, flexWrap: 'wrap', gap: { xs: 0.5, sm: 1 } }}>
          {type === 'pending' && onApprove && (
            <Button
              size="small"
              color="success"
              startIcon={<CheckCircle />}
              onClick={() => handleAction(() => onApprove(post.id), 'Post approuvé')}
              disabled={loading}
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            >
              Approuver
            </Button>
          )}
          {type === 'approved' && onPublish && (
            <Button
              size="small"
              color="primary"
              startIcon={<Publish />}
              onClick={() => {
                navigator.clipboard.writeText(post.content)
                  .then(() => toast.success('Post copié dans le presse-papier'))
                  .catch(() => toast.error('Erreur lors de la copie'));
              }}
              disabled={loading}
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            >
              Copier le post
            </Button>
          )}
          <IconButton
            size="small"
            onClick={() => setEditOpen(true)}
            disabled={loading}
          >
            <Edit />
          </IconButton>
          {onDelete && (
            <IconButton
              size="small"
              color="error"
              onClick={() => {
                if (confirm('Supprimer ce post ?')) {
                  handleAction(() => onDelete(post.id), 'Post supprimé');
                }
              }}
              disabled={loading}
            >
              <Delete />
            </IconButton>
          )}
        </CardActions>
      </Card>

      <Dialog open={editOpen} onClose={() => setEditOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ fontSize: { xs: '1.125rem', sm: '1.25rem' } }}>Éditer le post</DialogTitle>
        <DialogContent sx={{ px: { xs: 2, sm: 3 } }}>
          <TextField
            fullWidth
            multiline
            rows={10}
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            sx={{ 
              mt: 2,
              '& .MuiInputBase-root': {
                fontSize: { xs: '0.875rem', sm: '1rem' }
              }
            }}
          />
        </DialogContent>
        <DialogActions sx={{ px: { xs: 2, sm: 3 }, py: { xs: 1.5, sm: 2 } }}>
          <Button onClick={() => setEditOpen(false)} sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
            Annuler
          </Button>
          <Button onClick={handleSave} variant="contained" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
            Sauvegarder
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}