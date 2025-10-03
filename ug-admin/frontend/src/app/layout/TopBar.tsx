/**
 * Top Navigation Bar Component
 * 
 * Provides the main navigation bar with user menu, notifications,
 * and global actions for the admin dashboard.
 */

import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Box,
  Chip,
  Divider,
  ListItemIcon,
  ListItemText,
  Badge,
} from '@mui/material';
import {
  Menu as MenuIcon,
  AccountCircle,
  Logout,
  Settings,
  Notifications,
  School as SchoolIcon,
} from '@mui/icons-material';
import { useAuth } from '../providers/AuthProvider';
import { getRoleDisplayName, getRoleColor } from '../../auth/roles';

interface TopBarProps {
  onMenuToggle: () => void;
  drawerWidth: number;
}

/**
 * Top Bar Component
 */
export function TopBar({ onMenuToggle, drawerWidth }: TopBarProps) {
  const { user, signOut } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  /**
   * Handle user menu open
   */
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  /**
   * Handle user menu close
   */
  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  /**
   * Handle sign out
   */
  const handleSignOut = async () => {
    handleMenuClose();
    try {
      await signOut();
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        width: { sm: `calc(100% - ${drawerWidth}px)` },
        ml: { sm: `${drawerWidth}px` },
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar>
        {/* Mobile menu button */}
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={onMenuToggle}
          sx={{ mr: 2, display: { sm: 'none' } }}
        >
          <MenuIcon />
        </IconButton>

        {/* Logo and title */}
        <Box display="flex" alignItems="center" sx={{ flexGrow: 1 }}>
          <SchoolIcon sx={{ mr: 1, display: { xs: 'none', sm: 'block' } }} />
          <Typography variant="h6" noWrap component="div">
            Undergraduation Admin
          </Typography>
        </Box>

        {/* Right side actions */}
        <Box display="flex" alignItems="center" gap={1}>
          {/* Notifications */}
          <IconButton color="inherit">
            <Badge badgeContent={3} color="error">
              <Notifications />
            </Badge>
          </IconButton>

          {/* User info and role */}
          {user && (
            <Box display="flex" alignItems="center" gap={1} sx={{ ml: 1 }}>
              <Box display={{ xs: 'none', md: 'flex' }} flexDirection="column" alignItems="flex-end">
                <Typography variant="body2" sx={{ lineHeight: 1.2 }}>
                  {user.displayName || user.email}
                </Typography>
                <Chip
                  label={getRoleDisplayName(user.role)}
                  size="small"
                  color={getRoleColor(user.role)}
                  sx={{ height: 20, fontSize: '0.75rem' }}
                />
              </Box>

              {/* User avatar and menu */}
              <IconButton
                size="large"
                aria-label="account of current user"
                aria-controls="user-menu"
                aria-haspopup="true"
                onClick={handleMenuOpen}
                color="inherit"
              >
                <Avatar
                  src={user.photoURL}
                  alt={user.displayName || user.email}
                  sx={{ width: 32, height: 32 }}
                >
                  {(user.displayName || user.email).charAt(0).toUpperCase()}
                </Avatar>
              </IconButton>
            </Box>
          )}
        </Box>

        {/* User menu */}
        <Menu
          id="user-menu"
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          onClick={handleMenuClose}
          PaperProps={{
            elevation: 0,
            sx: {
              overflow: 'visible',
              filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
              mt: 1.5,
              minWidth: 200,
              '& .MuiAvatar-root': {
                width: 32,
                height: 32,
                ml: -0.5,
                mr: 1,
              },
              '&:before': {
                content: '""',
                display: 'block',
                position: 'absolute',
                top: 0,
                right: 14,
                width: 10,
                height: 10,
                bgcolor: 'background.paper',
                transform: 'translateY(-50%) rotate(45deg)',
                zIndex: 0,
              },
            },
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          {/* User info in menu */}
          {user && (
            <>
              <MenuItem disabled>
                <Avatar src={user.photoURL} />
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    {user.displayName || user.email}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {getRoleDisplayName(user.role)}
                  </Typography>
                </Box>
              </MenuItem>
              <Divider />
            </>
          )}

          {/* Menu items */}
          <MenuItem onClick={handleMenuClose}>
            <ListItemIcon>
              <AccountCircle fontSize="small" />
            </ListItemIcon>
            <ListItemText>Profile</ListItemText>
          </MenuItem>

          <MenuItem onClick={handleMenuClose}>
            <ListItemIcon>
              <Settings fontSize="small" />
            </ListItemIcon>
            <ListItemText>Settings</ListItemText>
          </MenuItem>

          <Divider />

          <MenuItem onClick={handleSignOut}>
            <ListItemIcon>
              <Logout fontSize="small" />
            </ListItemIcon>
            <ListItemText>Sign Out</ListItemText>
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
}

export default TopBar;
