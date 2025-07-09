import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogActions,
  Box,
  Typography,
  Button,
  Chip,
  Stack,
  IconButton,
  Link,
  Divider,
} from '@mui/material';
import {
  Close,
  OpenInNew,
  Schedule,
  Assessment,
} from '@mui/icons-material';
import { Article } from '../services/api';

interface ArticleModalProps {
  open: boolean;
  onClose: () => void;
  article: Article | null;
}

const ArticleModal: React.FC<ArticleModalProps> = ({
  open,
  onClose,
  article,
}) => {
  if (!article) return null;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          maxHeight: '90vh',
        },
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Typography variant="h6" component="div" sx={{ flex: 1, pr: 2 }}>
            {article.title}
          </Typography>
          <IconButton
            onClick={onClose}
            size="small"
            sx={{ color: 'text.secondary' }}
          >
            <Close />
          </IconButton>
        </Stack>
      </DialogTitle>

      <DialogContent>
        <Stack spacing={2}>
          {/* Métadonnées */}
          <Stack direction="row" spacing={1} flexWrap="wrap">
            <Chip
              icon={<Schedule />}
              label={formatDate(article.published)}
              size="small"
              variant="outlined"
              color="primary"
            />
            <Chip
              icon={<Assessment />}
              label={`Score: ${Math.round(article.relevance_score)}`}
              size="small"
              variant="outlined"
              color="secondary"
            />
            <Chip
              label={article.source}
              size="small"
              color="info"
              variant="outlined"
            />
            {article.domain_matches && (
              <Chip
                label={`${article.domain_matches} correspondances`}
                size="small"
                color="success"
                variant="outlined"
              />
            )}
          </Stack>

          <Divider />

          {/* Résumé */}
          {article.summary && (
            <Box>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Résumé
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {article.summary}
              </Typography>
            </Box>
          )}

          {/* Contenu complet */}
          {article.content && (
            <Box>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Contenu complet
              </Typography>
              <Typography 
                variant="body2" 
                component="div"
                sx={{ 
                  maxHeight: '400px', 
                  overflowY: 'auto',
                  lineHeight: 1.6,
                  '& p': { marginBottom: 1 }
                }}
              >
                {article.content.split('\n').map((paragraph, index) => (
                  paragraph.trim() && (
                    <Typography key={index} paragraph>
                      {paragraph}
                    </Typography>
                  )
                ))}
              </Typography>
            </Box>
          )}

          {/* Si pas de contenu */}
          {!article.content && !article.summary && (
            <Box sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Aucun contenu détaillé disponible pour cet article.
              </Typography>
            </Box>
          )}
        </Stack>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button
          variant="outlined"
          onClick={onClose}
          sx={{ mr: 1 }}
        >
          Fermer
        </Button>
        <Button
          variant="contained"
          startIcon={<OpenInNew />}
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          component={Link}
        >
          Ouvrir l'article original
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ArticleModal;