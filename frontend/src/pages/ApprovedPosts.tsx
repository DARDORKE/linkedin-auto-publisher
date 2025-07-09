import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Typography, Box, CircularProgress, Alert } from '@mui/material';
import { postApi } from '../services/api';
import PostCard from '../components/PostCard';

export default function ApprovedPosts() {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['posts', 'approved'],
    queryFn: () => postApi.getApproved(),
  });

  const publishMutation = useMutation({
    mutationFn: (id: number) => postApi.publish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts', 'approved'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => postApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts', 'approved'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, content }: { id: number; content: string }) => 
      postApi.update(id, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts', 'approved'] });
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
        Erreur lors du chargement des posts approuvés
      </Alert>
    );
  }

  const posts = data?.data.posts || [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Posts approuvés
      </Typography>
      
      {posts.length === 0 ? (
        <Alert severity="info">
          Aucun post approuvé prêt à être publié
        </Alert>
      ) : (
        <Box>
          {posts.map((post) => (
            <PostCard
              key={post.id}
              post={post}
              type="approved"
              onPublish={publishMutation.mutateAsync}
              onDelete={deleteMutation.mutateAsync}
              onUpdate={(id, content) => updateMutation.mutateAsync({ id, content })}
            />
          ))}
        </Box>
      )}
    </Box>
  );
}