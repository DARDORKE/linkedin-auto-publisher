import React from 'react';
import {
  Dialog,
  DialogContent,
  Box,
  Typography,
  LinearProgress,
  CircularProgress,
  Stack,
  Chip,
  Paper,
} from '@mui/material';

interface LoadingScreenProps {
  open: boolean;
  title?: string;
  description?: string;
  progress?: number;
  showProgress?: boolean;
  realTimeMessage?: string;
  progressDetails?: any;
  sessionType?: 'scraping' | 'generation' | null;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({
  open,
  title = 'Chargement en cours...',
  description,
  progress,
  showProgress = true,
  realTimeMessage,
  progressDetails,
  sessionType,
}) => {
  return (
    <Dialog
      open={open}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          padding: 2,
        },
      }}
      disableEscapeKeyDown
    >
      <DialogContent>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            py: 3,
          }}
        >
          <Stack spacing={3} alignItems="center" sx={{ width: '100%' }}>
            <CircularProgress size={60} thickness={4} />
            
            <Typography variant="h6" color="primary" gutterBottom>
              {title}
            </Typography>
            
            {/* Session type indicator */}
            {sessionType && (
              <Chip
                label={sessionType === 'scraping' ? 'Scraping' : 'Génération'}
                color={sessionType === 'scraping' ? 'info' : 'success'}
                size="small"
                sx={{ mb: 1 }}
              />
            )}
            
            {/* Real-time message */}
            {realTimeMessage && (
              <Typography variant="body2" color="text.primary" sx={{ fontWeight: 500 }}>
                {realTimeMessage}
              </Typography>
            )}
            
            {/* Fallback description */}
            {description && !realTimeMessage && (
              <Typography variant="body2" color="text.secondary">
                {description}
              </Typography>
            )}
            
            {/* Progress details */}
            {progressDetails && (
              <Paper elevation={0} sx={{ p: 2, backgroundColor: '#f5f5f5', width: '100%', maxWidth: 400 }}>
                <Stack spacing={1}>
                  {progressDetails.type === 'source_completed' && (
                    <>
                      <Typography variant="caption" color="text.secondary">
                        Source: {progressDetails.source_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Articles trouvés: {progressDetails.articles_found}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Progression: {progressDetails.completed_sources}/{progressDetails.total_sources}
                      </Typography>
                    </>
                  )}
                  {progressDetails.type === 'domain_completed' && (
                    <>
                      <Typography variant="caption" color="text.secondary">
                        Domaine: {progressDetails.domain}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Articles trouvés: {progressDetails.articles_found}
                      </Typography>
                    </>
                  )}
                  {progressDetails.type === 'generation_started' && (
                    <>
                      <Typography variant="caption" color="text.secondary">
                        Domaine: {progressDetails.domain}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Articles sélectionnés: {progressDetails.articles_count}
                      </Typography>
                    </>
                  )}
                </Stack>
              </Paper>
            )}
            
            {showProgress && (
              <Box sx={{ width: '100%', maxWidth: 400 }}>
                <LinearProgress
                  variant={progress !== undefined ? 'determinate' : 'indeterminate'}
                  value={progress}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: '#e0e0e0',
                    '& .MuiLinearProgress-bar': {
                      borderRadius: 4,
                    },
                  }}
                />
                {progress !== undefined && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ mt: 1, display: 'block' }}
                  >
                    {Math.round(progress)}%
                  </Typography>
                )}
              </Box>
            )}
          </Stack>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default LoadingScreen;