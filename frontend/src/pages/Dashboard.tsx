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
} from '@mui/material';
import {
  PendingActions,
  CheckCircle,
  Publish,
  Storage,
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

  const StatCard = ({ title, value, icon, color, subtitle }: any) => (
    <Card>
      <CardContent>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="text.secondary" gutterBottom variant="h6">
              {title}
            </Typography>
            <Typography variant="h4" component="div" sx={{ color }}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box sx={{ color, fontSize: '3rem' }}>
            {icon}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Tableau de bord
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Posts en attente"
            value={pending.length}
            icon={<PendingActions />}
            color="#ff9800"
            subtitle="À approuver"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Posts approuvés"
            value={approved.length}
            icon={<CheckCircle />}
            color="#4caf50"
            subtitle="Prêts à publier"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Articles en cache"
            value={cache?.fresh_articles || 0}
            icon={<Storage />}
            color="#2196f3"
            subtitle={`${cache?.total_articles || 0} au total`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Taux de cache"
            value={cache ? `${Math.round((cache.fresh_articles / cache.total_articles) * 100)}%` : '0%'}
            icon={<Publish />}
            color="#9c27b0"
            subtitle="Articles frais"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Répartition des posts
              </Typography>
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
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Articles par domaine
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={domainData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="domain" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="articles" fill="#0a66c2" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                État du cache
              </Typography>
              <Stack spacing={2}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Articles frais: {cache?.fresh_articles || 0} / {cache?.total_articles || 0}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={cache ? (cache.fresh_articles / cache.total_articles) * 100 : 0}
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {domainData.map((domain) => (
                    <Chip
                      key={domain.domain}
                      label={`${domain.domain}: ${domain.articles} articles`}
                      variant="outlined"
                      size="small"
                    />
                  ))}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}