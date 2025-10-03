/**
 * Side Navigation Component
 * 
 * Provides the main navigation sidebar with role-based menu items
 * and responsive drawer functionality.
 */

import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Box,
  Typography,
  Divider,
  Badge,
} from '@mui/material';
import {
  Dashboard,
  People,
  Email,
  Analytics,
  History,
  AdminPanelSettings,
  School as SchoolIcon,
} from '@mui/icons-material';
import { useAuth } from '../providers/AuthProvider';
import { getNavigationItems } from '../../auth/roles';

interface SideNavProps {
  open: boolean;
  onClose: () => void;
  drawerWidth: number;
}

// Icon mapping for navigation items
const iconMap: Record<string, React.ReactElement> = {
  dashboard: <Dashboard />,
  people: <People />,
  email: <Email />,
  analytics: <Analytics />,
  history: <History />,
  admin_panel_settings: <AdminPanelSettings />,
};

/**
 * Side Navigation Component
 */
export function SideNav({ open, onClose, drawerWidth }: SideNavProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // Get navigation items based on user role
  const navigationItems = getNavigationItems(user);

  /**
   * Handle navigation item click
   */
  const handleNavigation = (path: string) => {
    navigate(path);
    // Close drawer on mobile after navigation
    onClose();
  };

  /**
   * Check if current path matches navigation item
   */
  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  /**
   * Drawer content
   */
  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Logo and title */}
      <Toolbar>
        <Box display="flex" alignItems="center" gap={1}>
          <SchoolIcon color="primary" />
          <Typography variant="h6" noWrap>
            UG Admin
          </Typography>
        </Box>
      </Toolbar>

      <Divider />

      {/* Navigation items */}
      <List sx={{ flexGrow: 1, px: 1 }}>
        {navigationItems.map((item) => {
          const active = isActive(item.path);
          
          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => handleNavigation(item.path)}
                selected={active}
                sx={{
                  borderRadius: 1,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.main',
                    color: 'primary.contrastText',
                    '&:hover': {
                      backgroundColor: 'primary.dark',
                    },
                    '& .MuiListItemIcon-root': {
                      color: 'primary.contrastText',
                    },
                  },
                }}
              >
                <ListItemIcon>
                  {iconMap[item.icon] || <Dashboard />}
                </ListItemIcon>
                <ListItemText 
                  primary={item.label}
                  primaryTypographyProps={{
                    fontWeight: active ? 600 : 400,
                  }}
                />
                {item.badge && (
                  <Badge
                    badgeContent={item.badge}
                    color="error"
                    sx={{
                      '& .MuiBadge-badge': {
                        fontSize: '0.75rem',
                        height: 18,
                        minWidth: 18,
                      },
                    }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      {/* Footer */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Typography variant="caption" color="text.secondary" display="block">
          Undergraduation.com
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Admin Dashboard v1.0
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box
      component="nav"
      sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
    >
      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={open}
        onClose={onClose}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile
        }}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
          },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', sm: 'block' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
          },
        }}
        open
      >
        {drawerContent}
      </Drawer>
    </Box>
  );
}

export default SideNav;
