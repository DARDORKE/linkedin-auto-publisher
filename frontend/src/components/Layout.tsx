import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  useTheme,
  useMediaQuery,
  Avatar,
  Divider,
  Badge,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Pending as PendingIcon,
  CheckCircle as ApprovedIcon,
  Search as SearchIcon,
  LinkedIn as LinkedInIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';

const drawerWidth = 280;

interface Props {
  children: React.ReactNode;
}

const menuItems = [
  { text: 'Tableau de bord', icon: <DashboardIcon />, path: '/dashboard', badge: null },
  { text: 'Posts en attente', icon: <PendingIcon />, path: '/posts/pending', badge: 'pending' },
  { text: 'Posts approuvés', icon: <ApprovedIcon />, path: '/posts/approved', badge: 'approved' },
  { text: 'Scraping manuel', icon: <SearchIcon />, path: '/scraping', badge: null },
];

export default function Layout({ children }: Props) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const location = useLocation();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: { xs: 2, sm: 3 }, borderBottom: '1px solid #e2e8f0' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1.5, sm: 2 }, mb: 2 }}>
          <Avatar sx={{ bgcolor: 'primary.main', width: { xs: 36, sm: 40 }, height: { xs: 36, sm: 40 } }}>
            <LinkedInIcon />
          </Avatar>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600, color: 'text.primary', lineHeight: 1.2, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              LinkedIn
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', lineHeight: 1.2, fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
              Auto Publisher
            </Typography>
          </Box>
        </Box>
      </Box>
      
      <Box sx={{ flex: 1, py: 2 }}>
        <List sx={{ px: { xs: 1, sm: 2 } }}>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                component={Link}
                to={item.path}
                selected={location.pathname === item.path}
                onClick={() => isMobile && setMobileOpen(false)}
                sx={{
                  borderRadius: 2,
                  minHeight: { xs: 44, sm: 48 },
                  px: { xs: 1.5, sm: 2 },
                  '&.Mui-selected': {
                    backgroundColor: 'primary.main',
                    color: 'white',
                    '&:hover': {
                      backgroundColor: 'primary.dark',
                    },
                    '& .MuiListItemIcon-root': {
                      color: 'white',
                    },
                  },
                  '&:hover': {
                    backgroundColor: 'action.hover',
                    borderRadius: 2,
                  },
                }}
              >
                <ListItemIcon 
                  sx={{ 
                    minWidth: { xs: 36, sm: 40 },
                    color: location.pathname === item.path ? 'white' : 'text.secondary',
                  }}
                >
                  {item.badge ? (
                    <Badge 
                      badgeContent={item.badge === 'pending' ? '3' : item.badge === 'approved' ? '2' : 0} 
                      color={item.badge === 'pending' ? 'warning' : 'success'}
                      variant="dot"
                    >
                      {item.icon}
                    </Badge>
                  ) : (
                    item.icon
                  )}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text} 
                  primaryTypographyProps={{
                    fontSize: { xs: '0.8rem', sm: '0.875rem' },
                    fontWeight: location.pathname === item.path ? 600 : 500,
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>

      <Divider />
      
      <Box sx={{ p: { xs: 1.5, sm: 2 } }}>
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: { xs: 0.5, sm: 1 }, 
          p: { xs: 1.5, sm: 2 }, 
          backgroundColor: 'success.light', 
          borderRadius: 2,
          color: 'success.dark'
        }}>
          <TrendingUpIcon sx={{ fontSize: { xs: 18, sm: 20 } }} />
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, lineHeight: 1.2, fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
              Système actif
            </Typography>
            <Typography variant="caption" sx={{ lineHeight: 1.2, fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
              Tout fonctionne bien
            </Typography>
          </Box>
        </Box>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            {menuItems.find((item) => item.path === location.pathname)?.text || 'LinkedIn Auto Publisher'}
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant={isMobile ? 'temporary' : 'permanent'}
          open={isMobile ? mobileOpen : true}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: { xs: 260, sm: drawerWidth },
              backgroundColor: '#ffffff',
              borderRight: '1px solid #e2e8f0',
              boxShadow: '0px 4px 6px -1px rgba(0, 0, 0, 0.1), 0px 2px 4px -1px rgba(0, 0, 0, 0.06)',
            },
          }}
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 1, sm: 2, md: 3, lg: 4 },
          width: { md: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          backgroundColor: 'background.default',
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}