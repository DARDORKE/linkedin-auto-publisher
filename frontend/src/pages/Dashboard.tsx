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

  const { data: cacheStats } = useQuery({
    queryKey: ['cache', 'stats'],
    queryFn: () => domainApi.getCacheStats(),
  });

  const { data: cacheByDomains } = useQuery({
    queryKey: ['cache', 'domains'],
    queryFn: () => domainApi.getCacheByDomains(),
  });

  const pending = pendingPosts?.data.posts || [];
  const approved = approvedPosts?.data.posts || [];
  const cache = cacheStats?.data;
  const domainCache = cacheByDomains?.data;

  // Données pour le graphique en secteurs
  const pieData = [
    { name: 'En attente', value: pending.length, color: '#ff9800' },
    { name: 'Approuvés', value: approved.length, color: '#4caf50' },
  ];

  // Données pour le graphique en barres par domaine
  const domainData = domainCache ? Object.entries(domainCache).map(([domain, stats]) => ({
    domain: domain.charAt(0).toUpperCase() + domain.slice(1),
    articles: stats.cached_count,
    sources: stats.sources_count,
  })) : [];

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
        <CardContent sx={{ pb: 2 }}>
          <Stack direction="row" alignItems="flex-start" justifyContent="space-between" spacing={2}>
            <Box sx={{ flex: 1 }}>
              <Typography 
                color="text.secondary" 
                variant="body2" 
                sx={{ fontWeight: 500, mb: 1, textTransform: 'uppercase', letterSpacing: 0.5 }}
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
                }}
              >
                {value}
              </Typography>
              {subtitle && (
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                  {subtitle}
                </Typography>
              )}
              {trend && (
                <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mt: 1 }}>
                  {trend > 0 ? (
                    <TrendingUp sx={{ fontSize: 16, color: 'success.main' }} />
                  ) : (
                    <TrendingDown sx={{ fontSize: 16, color: 'error.main' }} />
                  )}
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      color: trend > 0 ? 'success.main' : 'error.main',
                      fontWeight: 600 
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
                width: 56,
                height: 56,
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
        <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography 
              variant="h3" 
              sx={{ 
                fontWeight: 700, 
                background: 'linear-gradient(45deg, #0a66c2, #074a8b)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 1
              }}
            >
              Tableau de bord
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Vue d'ensemble de votre système de publication LinkedIn
            </Typography>
          </Box>
          <IconButton 
            sx={{ 
              bgcolor: 'primary.main', 
              color: 'white',
              '&:hover': { bgcolor: 'primary.dark' }
            }}
          >
            <Refresh />
          </IconButton>
        </Box>

        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Posts en attente"
              value={pending.length}
              icon={<PendingActions />}
              color="#f59e0b"
              subtitle="À approuver"
              trend={12}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Posts approuvés"
              value={approved.length}
              icon={<CheckCircle />}
              color="#10b981"
              subtitle="Prêts à publier"
              trend={8}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Articles en cache"
              value={cache?.fresh_articles || 0}
              icon={<Storage />}
              color="#3b82f6"
              subtitle={`${cache?.total_articles || 0} au total`}
              trend={-3}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Taux de cache"
              value={cache ? `${Math.round((cache.fresh_articles / cache.total_articles) * 100)}%` : '0%'}
              icon={<Publish />}
              color="#8b5cf6"
              subtitle="Articles frais"
              trend={5}
            />
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Grow in={true} timeout={1000}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
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

          <Grid item xs={12} md={6}>
            <Grow in={true} timeout={1200}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      Articles par domaine
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
                        dataKey="articles" 
                        fill="url(#barGradient)" 
                        radius={[4, 4, 0, 0]}
                        animationDuration={1500}
                      />
                      <defs>
                        <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#0a66c2" />
                          <stop offset="100%" stopColor="#4791db" />
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
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      État du cache système
                    </Typography>
                    <IconButton size="small">
                      <MoreVert />
                    </IconButton>
                  </Box>
                  <Stack spacing={3}>
                    <Box>
                      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                          Articles frais: {cache?.fresh_articles || 0} / {cache?.total_articles || 0}
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                          {cache ? Math.round((cache.fresh_articles / cache.total_articles) * 100) : 0}%
                        </Typography>
                      </Stack>
                      <LinearProgress
                        variant="determinate"
                        value={cache ? (cache.fresh_articles / cache.total_articles) * 100 : 0}
                        sx={{ 
                          height: 12, 
                          borderRadius: 6,
                          backgroundColor: '#e2e8f0',
                          '& .MuiLinearProgress-bar': {
                            borderRadius: 6,
                            background: 'linear-gradient(90deg, #0a66c2, #4791db)',
                          }
                        }}
                      />
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontWeight: 500 }}>
                        Distribution par domaine
                      </Typography>
                      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                        {domainData.map((domain) => (
                          <Chip
                            key={domain.domain}
                            label={`${domain.domain}: ${domain.articles} articles`}
                            variant="outlined"
                            size="medium"
                            sx={{
                              borderRadius: 2,
                              fontWeight: 500,
                              '&:hover': {
                                transform: 'translateY(-1px)',
                                boxShadow: '0px 4px 6px -1px rgba(0, 0, 0, 0.1)',
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