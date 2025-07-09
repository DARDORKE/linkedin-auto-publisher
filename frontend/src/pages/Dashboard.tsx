import { useQuery } from '@tanstack/react-query';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Stack,
  Chip,
  Avatar,
  Fade,
  Grow,
  IconButton,
} from '@mui/material';
import {
  PendingActions,
  CheckCircle,
  Publish,
  Storage,
  TrendingUp,
  TrendingDown,
  MoreVert,
  Refresh,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { postApi, domainApi } from '../services/api';

export default function Dashboard() {
  const { data: pendingPosts } = useQuery({
    queryKey: ['posts', 'pending'],
    queryFn: () => postApi.getPending(),
  });

  const { data: approvedPosts } = useQuery({
    queryKey: ['posts', 'approved'],
    queryFn: () => postApi.getApproved(),
  });

  const { data: domainsData } = useQuery({
    queryKey: ['domains'],
    queryFn: () => domainApi.getDomains(),
  });

  const pending = pendingPosts?.data.posts || [];
  const approved = approvedPosts?.data.posts || [];
  const domains = domainsData?.data.domains || {};

  // Données pour le graphique en secteurs
  const pieData = [
    { name: 'En attente', value: pending.length, color: '#ff9800' },
    { name: 'Approuvés', value: approved.length, color: '#4caf50' },
  ];

  // Données pour le graphique en barres par domaine
  const domainData = Object.entries(domains).map(([domain]) => ({
    domain: domain.charAt(0).toUpperCase() + domain.slice(1),
    pending: pending.filter(p => p.domain_name === domain).length,
    approved: approved.filter(p => p.domain_name === domain).length,
  }));

  const StatCard = ({ title, value, icon, color, subtitle, trend }: any) => (
    <Grow in={true} timeout={500}>
      <Card 
        sx={{ 
          position: 'relative',
          overflow: 'visible',
          '&:hover': {
            '& .stat-icon': {
              transform: 'scale(1.1) rotate(5deg)',
            }
          }
        }}
      >
        <CardContent sx={{ pb: { xs: 1.5, sm: 2 }, px: { xs: 2, sm: 3 } }}>
          <Stack direction="row" alignItems="flex-start" justifyContent="space-between" spacing={{ xs: 1, sm: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Typography 
                color="text.secondary" 
                variant="body2" 
                sx={{ fontWeight: 500, mb: 1, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
              >
                {title}
              </Typography>
              <Typography 
                variant="h3" 
                component="div" 
                sx={{ 
                  color, 
                  fontWeight: 700,
                  mb: 0.5,
                  background: `linear-gradient(45deg, ${color}, ${color}aa)`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontSize: { xs: '1.75rem', sm: '2rem', md: '2.5rem' }
                }}
              >
                {value}
              </Typography>
              {subtitle && (
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}>
                  {subtitle}
                </Typography>
              )}
              {trend && (
                <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mt: 1 }}>
                  {trend > 0 ? (
                    <TrendingUp sx={{ fontSize: { xs: 14, sm: 16 }, color: 'success.main' }} />
                  ) : (
                    <TrendingDown sx={{ fontSize: { xs: 14, sm: 16 }, color: 'error.main' }} />
                  )}
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      color: trend > 0 ? 'success.main' : 'error.main',
                      fontWeight: 600,
                      fontSize: { xs: '0.7rem', sm: '0.75rem' }
                    }}
                  >
                    {Math.abs(trend)}% vs hier
                  </Typography>
                </Stack>
              )}
            </Box>
            <Avatar 
              className="stat-icon"
              sx={{ 
                bgcolor: `${color}20`,
                color: color,
                width: { xs: 48, sm: 56 },
                height: { xs: 48, sm: 56 },
                transition: 'all 0.3s ease-in-out',
                boxShadow: `0 4px 20px ${color}30`,
              }}
            >
              {icon}
            </Avatar>
          </Stack>
        </CardContent>
      </Card>
    </Grow>
  );

  return (
    <Fade in={true} timeout={800}>
      <Box>
        <Box sx={{ mb: { xs: 2, sm: 3, md: 4 }, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexDirection: { xs: 'column', sm: 'row' }, gap: { xs: 2, sm: 0 } }}>
          <Box sx={{ textAlign: { xs: 'center', sm: 'left' } }}>
            <Typography 
              variant="h3" 
              sx={{ 
                fontWeight: 700, 
                background: 'linear-gradient(45deg, #0a66c2, #074a8b)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 1,
                fontSize: { xs: '1.5rem', sm: '2rem', md: '2.5rem' }
              }}
            >
              Tableau de bord
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
              Vue d'ensemble de votre système de génération de posts
            </Typography>
          </Box>
          <IconButton 
            sx={{ 
              bgcolor: 'primary.main', 
              color: 'white',
              '&:hover': { bgcolor: 'primary.dark' },
              size: { xs: 'small', sm: 'medium' }
            }}
          >
            <Refresh />
          </IconButton>
        </Box>

        <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ mb: { xs: 3, sm: 4 } }}>
          <Grid item xs={12} sm={6} lg={3}>
            <StatCard
              title="Posts en attente"
              value={pending.length}
              icon={<PendingActions />}
              color="#f59e0b"
              subtitle="À approuver"
              trend={12}
            />
          </Grid>
          <Grid item xs={12} sm={6} lg={3}>
            <StatCard
              title="Posts approuvés"
              value={approved.length}
              icon={<CheckCircle />}
              color="#10b981"
              subtitle="Prêts à publier"
              trend={8}
            />
          </Grid>
          <Grid item xs={12} sm={6} lg={3}>
            <StatCard
              title="Total posts"
              value={pending.length + approved.length}
              icon={<Storage />}
              color="#3b82f6"
              subtitle="Posts générés"
              trend={15}
            />
          </Grid>
          <Grid item xs={12} sm={6} lg={3}>
            <StatCard
              title="Domaines actifs"
              value={Object.keys(domains).length}
              icon={<Publish />}
              color="#8b5cf6"
              subtitle="Domaines configurés"
              trend={0}
            />
          </Grid>
        </Grid>

        <Grid container spacing={{ xs: 2, sm: 3 }}>
          <Grid item xs={12} lg={6}>
            <Grow in={true} timeout={1000}>
              <Card sx={{ height: '100%' }}>
                <CardContent sx={{ px: { xs: 2, sm: 3 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                      Répartition des posts
                    </Typography>
                    <IconButton size="small">
                      <MoreVert />
                    </IconButton>
                  </Box>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}`}
                        animationDuration={1500}
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{
                          backgroundColor: '#ffffff',
                          border: 'none',
                          borderRadius: '12px',
                          boxShadow: '0px 4px 6px -1px rgba(0, 0, 0, 0.1), 0px 2px 4px -1px rgba(0, 0, 0, 0.06)',
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grow>
          </Grid>

          <Grid item xs={12} lg={6}>
            <Grow in={true} timeout={1200}>
              <Card sx={{ height: '100%' }}>
                <CardContent sx={{ px: { xs: 2, sm: 3 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                      Posts par domaine
                    </Typography>
                    <IconButton size="small">
                      <MoreVert />
                    </IconButton>
                  </Box>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={domainData}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis 
                        dataKey="domain" 
                        axisLine={false}
                        tickLine={false}
                        style={{ fontSize: '12px', fill: '#64748b' }}
                      />
                      <YAxis 
                        axisLine={false}
                        tickLine={false}
                        style={{ fontSize: '12px', fill: '#64748b' }}
                      />
                      <Tooltip 
                        contentStyle={{
                          backgroundColor: '#ffffff',
                          border: 'none',
                          borderRadius: '12px',
                          boxShadow: '0px 4px 6px -1px rgba(0, 0, 0, 0.1), 0px 2px 4px -1px rgba(0, 0, 0, 0.06)',
                        }}
                      />
                      <Bar 
                        dataKey="pending" 
                        fill="url(#barGradient)" 
                        radius={[4, 4, 0, 0]}
                        animationDuration={1500}
                        name="En attente"
                      />
                      <Bar 
                        dataKey="approved" 
                        fill="url(#barGradient2)" 
                        radius={[4, 4, 0, 0]}
                        animationDuration={1500}
                        name="Approuvés"
                      />
                      <defs>
                        <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#f59e0b" />
                          <stop offset="100%" stopColor="#fbbf24" />
                        </linearGradient>
                        <linearGradient id="barGradient2" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#10b981" />
                          <stop offset="100%" stopColor="#34d399" />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grow>
          </Grid>

          <Grid item xs={12}>
            <Grow in={true} timeout={1400}>
              <Card>
                <CardContent sx={{ px: { xs: 2, sm: 3 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: { xs: 2, sm: 3 } }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                      État du système
                    </Typography>
                    <IconButton size="small">
                      <MoreVert />
                    </IconButton>
                  </Box>
                  <Stack spacing={{ xs: 2, sm: 3 }}>
                    <Box>
                      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                          Posts approuvés: {approved.length} / {pending.length + approved.length}
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main', fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                          {pending.length + approved.length > 0 ? Math.round((approved.length / (pending.length + approved.length)) * 100) : 0}%
                        </Typography>
                      </Stack>
                      <LinearProgress
                        variant="determinate"
                        value={pending.length + approved.length > 0 ? (approved.length / (pending.length + approved.length)) * 100 : 0}
                        sx={{ 
                          height: { xs: 10, sm: 12 }, 
                          borderRadius: 6,
                          backgroundColor: '#e2e8f0',
                          '& .MuiLinearProgress-bar': {
                            borderRadius: 6,
                            background: 'linear-gradient(90deg, #10b981, #34d399)',
                          }
                        }}
                      />
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontWeight: 500, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                        Domaines configurés
                      </Typography>
                      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                        {Object.entries(domains).map(([key, domain]) => (
                          <Chip
                            key={key}
                            label={domain.name}
                            variant="outlined"
                            size="small"
                            sx={{
                              borderRadius: 2,
                              fontWeight: 500,
                              borderColor: domain.color,
                              color: domain.color,
                              fontSize: { xs: '0.7rem', sm: '0.875rem' },
                              '&:hover': {
                                transform: 'translateY(-1px)',
                                boxShadow: '0px 4px 6px -1px rgba(0, 0, 0, 0.1)',
                                backgroundColor: `${domain.color}10`,
                              },
                              transition: 'all 0.2s ease-in-out',
                            }}
                          />
                        ))}
                      </Stack>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grow>
          </Grid>
        </Grid>
      </Box>
    </Fade>
  );
}