import React from 'react';
import {
  Dialog,
  DialogContent,
  Box,
  Typography,
  LinearProgress,
  CircularProgress,
  Stack,
} from '@mui/material';

interface LoadingScreenProps {
  open: boolean;
  title?: string;
  description?: string;
  progress?: number;
  showProgress?: boolean;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({
  open,
  title = 'Chargement en cours...',
  description,
  progress,
  showProgress = true,
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
            
            {description && (
              <Typography variant="body2" color="text.secondary">
                {description}
              </Typography>
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