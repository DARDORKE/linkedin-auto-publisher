import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Typography, Box, CircularProgress, Alert } from '@mui/material';
import { postApi } from '../services/api';
import PostCard from '../components/PostCard';

export default function PendingPosts() {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['posts', 'pending'],
    queryFn: () => postApi.getPending(),
  });

  const approveMutation = useMutation({
    mutationFn: (id: number) => postApi.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts', 'pending'] });
      queryClient.invalidateQueries({ queryKey: ['posts', 'approved'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => postApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts', 'pending'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, content }: { id: number; content: string }) => 
      postApi.update(id, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts', 'pending'] });
    },
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Erreur lors du chargement des posts en attente
      </Alert>
    );
  }

  const posts = data?.data.posts || [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ fontSize: { xs: '1.5rem', sm: '2rem', md: '2.5rem' } }}>
        Posts en attente
      </Typography>
      
      {posts.length === 0 ? (
        <Alert severity="info" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
          Aucun post en attente d'approbation
        </Alert>
      ) : (
        <Box>
          {posts.map((post) => (
            <PostCard
              key={post.id}
              post={post}
              type="pending"
              onApprove={approveMutation.mutateAsync}
              onDelete={deleteMutation.mutateAsync}
              onUpdate={(id, content) => updateMutation.mutateAsync({ id, content })}
            />
          ))}
        </Box>
      )}
    </Box>
  );
}