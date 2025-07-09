import React, { useState } from 'react';
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
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
            <Chip 
              label={post.domain_name} 
              color="primary" 
              size="small" 
            />
            <Typography variant="caption" color="text.secondary">
              {format(new Date(post.generated_at), 'dd MMMM yyyy HH:mm', { locale: fr })}
            </Typography>
          </Stack>

          <Typography variant="body1" paragraph sx={{ whiteSpace: 'pre-wrap' }}>
            {formatContent(post.content)}
          </Typography>

          <Stack direction="row" spacing={1} flexWrap="wrap" mb={2}>
            {post.hashtags.map((tag, index) => (
              <Chip
                key={index}
                label={tag}
                size="small"
                sx={{ 
                  backgroundColor: '#e7f3ff',
                  color: '#0a66c2',
                  mb: 0.5
                }}
              />
            ))}
          </Stack>

          <Box>
            <Button
              size="small"
              onClick={() => setShowSources(!showSources)}
              endIcon={showSources ? <ExpandLess /> : <ExpandMore />}
            >
              {post.sources_count} sources utilisées
            </Button>
            <Collapse in={showSources}>
              <Box sx={{ mt: 1, pl: 2 }}>
                {post.source_articles.map((article, index) => (
                  <Typography key={index} variant="caption" display="block" sx={{ mb: 0.5 }}>
                    • <Link href={article.url} target="_blank" rel="noopener">
                      {article.title}
                    </Link> ({article.source})
                  </Typography>
                ))}
              </Box>
            </Collapse>
          </Box>
        </CardContent>

        <CardActions>
          {type === 'pending' && onApprove && (
            <Button
              size="small"
              color="success"
              startIcon={<CheckCircle />}
              onClick={() => handleAction(() => onApprove(post.id), 'Post approuvé')}
              disabled={loading}
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
        <DialogTitle>Éditer le post</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={10}
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditOpen(false)}>Annuler</Button>
          <Button onClick={handleSave} variant="contained">
            Sauvegarder
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}