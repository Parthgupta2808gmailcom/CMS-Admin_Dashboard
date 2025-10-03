/**
 * Dashboard Layout Component
 * 
 * Main layout wrapper that provides the overall structure for the
 * admin dashboard with responsive navigation and content area.
 */

import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Box, Toolbar } from '@mui/material';
import { TopBar } from './TopBar';
import { SideNav } from './SideNav';

// Drawer width constant
const DRAWER_WIDTH = 280;

/**
 * Dashboard Layout Component
 */
export function DashboardLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);

  /**
   * Handle drawer toggle for mobile
   */
  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  /**
   * Handle drawer close
   */
  const handleDrawerClose = () => {
    setMobileOpen(false);
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      height: '100vh',
      overflow: 'hidden', // Prevent body scroll
    }}>
      {/* Top navigation bar */}
      <TopBar
        onMenuToggle={handleDrawerToggle}
        drawerWidth={DRAWER_WIDTH}
      />

      {/* Side navigation */}
      <SideNav
        open={mobileOpen}
        onClose={handleDrawerClose}
        drawerWidth={DRAWER_WIDTH}
      />

      {/* Main content area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { 
            xs: '100%', 
            sm: `calc(100% - ${DRAWER_WIDTH}px)` 
          },
          backgroundColor: 'background.default',
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Toolbar spacer */}
        <Toolbar sx={{ 
          minHeight: { xs: '56px', sm: '64px' } 
        }} />
        
        {/* Page content - scrollable area */}
        <Box
          sx={{
            flex: 1,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            p: { xs: 1, sm: 2, md: 3 },
          }}
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}

export default DashboardLayout;
