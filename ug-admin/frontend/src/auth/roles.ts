/**
 * Role-based access control utilities
 * 
 * Provides type-safe role checking and permission utilities
 * for the admin dashboard UI components.
 */

// User roles matching backend enum
export const UserRole = {
  ADMIN: 'admin',
  STAFF: 'staff'
} as const;

export type UserRole = typeof UserRole[keyof typeof UserRole];

// User interface matching backend AuthenticatedUser
export interface AuthenticatedUser {
  uid: string;
  email: string;
  role: UserRole;
  displayName?: string;
  photoURL?: string;
}

// Permission definitions
export interface Permissions {
  // Student operations
  canCreateStudents: boolean;
  canViewStudents: boolean;
  canUpdateStudents: boolean;
  canDeleteStudents: boolean;
  
  // Bulk operations
  canImportStudents: boolean;
  canExportStudents: boolean;
  
  // File operations
  canUploadFiles: boolean;
  canViewFiles: boolean;
  canDeleteFiles: boolean;
  
  // Email operations
  canSendEmails: boolean;
  canViewEmailLogs: boolean;
  canSendBulkEmails: boolean;
  
  // Search operations
  canSearchStudents: boolean;
  canViewSearchFacets: boolean;
  
  // Admin operations
  canViewAuditLogs: boolean;
  canManageUsers: boolean;
  canViewInsights: boolean;
}

/**
 * Get user permissions based on role
 */
export function getUserPermissions(role: UserRole): Permissions {
  const basePermissions: Permissions = {
    // Staff permissions (base level)
    canCreateStudents: true,
    canViewStudents: true,
    canUpdateStudents: false,
    canDeleteStudents: false,
    
    canImportStudents: false,
    canExportStudents: true,
    
    canUploadFiles: true,
    canViewFiles: true,
    canDeleteFiles: true,
    
    canSendEmails: true,
    canViewEmailLogs: true,
    canSendBulkEmails: true,
    
    canSearchStudents: true,
    canViewSearchFacets: true,
    
    canViewAuditLogs: false,
    canManageUsers: false,
    canViewInsights: true,
  };

  if (role === UserRole.ADMIN) {
    // Admin gets all permissions
    return {
      ...basePermissions,
      canUpdateStudents: true,
      canDeleteStudents: true,
      canImportStudents: true,
      canViewAuditLogs: true,
      canManageUsers: true,
    };
  }

  return basePermissions;
}

/**
 * Check if user has admin role
 */
export function isAdmin(user: AuthenticatedUser | null): boolean {
  return user?.role === UserRole.ADMIN;
}

/**
 * Check if user has staff role (includes admin)
 */
export function isStaff(user: AuthenticatedUser | null): boolean {
  return user?.role === UserRole.STAFF || user?.role === UserRole.ADMIN;
}

/**
 * Check if user has any authenticated role
 */
export function isAuthenticated(user: AuthenticatedUser | null): boolean {
  return user !== null && Object.values(UserRole).includes(user.role);
}

/**
 * Check if user can perform a specific action
 */
export function canPerformAction(
  user: AuthenticatedUser | null, 
  action: keyof Permissions
): boolean {
  if (!user) return false;
  
  const permissions = getUserPermissions(user.role);
  return permissions[action];
}

/**
 * Get user role display name
 */
export function getRoleDisplayName(role: UserRole): string {
  switch (role) {
    case UserRole.ADMIN:
      return 'Administrator';
    case UserRole.STAFF:
      return 'Staff Member';
    default:
      return 'Unknown';
  }
}

/**
 * Get user role color for UI display
 */
export function getRoleColor(role: UserRole): 'error' | 'primary' | 'default' {
  switch (role) {
    case UserRole.ADMIN:
      return 'error';
    case UserRole.STAFF:
      return 'primary';
    default:
      return 'default';
  }
}

/**
 * Role-based route permissions
 */
export interface RoutePermission {
  path: string;
  roles: UserRole[];
  exact?: boolean;
}

export const routePermissions: RoutePermission[] = [
  // Public routes (no authentication required)
  { path: '/login', roles: [] },
  
  // Protected routes (authentication required)
  { path: '/', roles: [UserRole.ADMIN, UserRole.STAFF] },
  { path: '/students', roles: [UserRole.ADMIN, UserRole.STAFF] },
  { path: '/students/:id', roles: [UserRole.ADMIN, UserRole.STAFF] },
  { path: '/campaigns', roles: [UserRole.ADMIN, UserRole.STAFF] },
  { path: '/insights', roles: [UserRole.ADMIN, UserRole.STAFF] },
  
  // Admin-only routes
  { path: '/admin', roles: [UserRole.ADMIN] },
  { path: '/audit-logs', roles: [UserRole.ADMIN] },
  { path: '/user-management', roles: [UserRole.ADMIN] },
];

/**
 * Check if user can access a specific route
 */
export function canAccessRoute(user: AuthenticatedUser | null, path: string): boolean {
  const permission = routePermissions.find(p => {
    if (p.exact) {
      return p.path === path;
    }
    // Simple pattern matching for dynamic routes
    const pattern = p.path.replace(/:[^/]+/g, '[^/]+');
    const regex = new RegExp(`^${pattern}$`);
    return regex.test(path);
  });

  // If no permission defined, allow access (fallback)
  if (!permission) return true;

  // If no roles specified, route is public
  if (permission.roles.length === 0) return true;

  // Check if user has required role
  return user !== null && permission.roles.includes(user.role);
}

/**
 * Get navigation items based on user role
 */
export interface NavigationItem {
  label: string;
  path: string;
  icon: string;
  roles: UserRole[];
  badge?: string;
}

export function getNavigationItems(user: AuthenticatedUser | null): NavigationItem[] {
  const allItems: NavigationItem[] = [
    {
      label: 'Dashboard',
      path: '/',
      icon: 'dashboard',
      roles: [UserRole.ADMIN, UserRole.STAFF],
    },
    {
      label: 'Students',
      path: '/students',
      icon: 'people',
      roles: [UserRole.ADMIN, UserRole.STAFF],
    },
    {
      label: 'Email Campaigns',
      path: '/campaigns',
      icon: 'email',
      roles: [UserRole.ADMIN, UserRole.STAFF],
    },
    {
      label: 'Insights',
      path: '/insights',
      icon: 'analytics',
      roles: [UserRole.ADMIN, UserRole.STAFF],
    },
    {
      label: 'Audit Logs',
      path: '/audit-logs',
      icon: 'history',
      roles: [UserRole.ADMIN],
    },
    {
      label: 'User Management',
      path: '/user-management',
      icon: 'admin_panel_settings',
      roles: [UserRole.ADMIN],
    },
  ];

  // Filter items based on user role
  return allItems.filter(item => 
    user && item.roles.includes(user.role)
  );
}
