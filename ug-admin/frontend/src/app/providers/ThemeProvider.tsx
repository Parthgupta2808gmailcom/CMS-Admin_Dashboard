/**
 * Theme Provider Component
 * 
 * Wraps the application with MUI theme provider and provides
 * consistent theming throughout the admin dashboard.
 */

import React from 'react';
import { ThemeProvider as MuiThemeProvider, CssBaseline } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { theme } from '../../styles/theme';

interface ThemeProviderProps {
  children: React.ReactNode;
}

/**
 * Theme Provider component that sets up MUI theme and date picker localization
 */
export function ThemeProvider({ children }: ThemeProviderProps) {
  return (
    <MuiThemeProvider theme={theme}>
      {/* CssBaseline provides consistent CSS reset across browsers */}
      <CssBaseline />
      
      {/* LocalizationProvider for date pickers */}
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        {children}
      </LocalizationProvider>
    </MuiThemeProvider>
  );
}

export default ThemeProvider;
