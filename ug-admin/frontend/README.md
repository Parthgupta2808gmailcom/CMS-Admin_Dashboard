# UG Admin Dashboard - Frontend

A comprehensive React admin dashboard for managing student applications and communications.

## 🚀 Tech Stack

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Material-UI (MUI) 6** - React component library
- **React Router 6.27+** - Client-side routing
- **TanStack Query** - Data fetching and caching
- **Axios** - HTTP client with interceptors
- **Firebase SDK** - Authentication (Email/Password + Google)
- **Vitest** - Fast unit testing framework
- **React Testing Library** - Component testing utilities

## 📁 Project Structure

```
src/
├── app/                    # App-level configuration
│   ├── App.tsx            # Root component
│   ├── routes.tsx         # Route definitions
│   ├── layout/            # Layout components
│   └── providers/         # Context providers
├── auth/                  # Authentication
│   ├── LoginPage.tsx      # Login interface
│   ├── Guarded.tsx        # Route protection
│   ├── firebase.ts        # Firebase config
│   └── roles.ts           # RBAC utilities
├── api/                   # API layer
│   ├── axios.ts           # Axios configuration
│   ├── queryKeys.ts       # React Query keys
│   ├── students.ts        # Student API calls
│   ├── files.ts           # File API calls
│   ├── email.ts           # Email API calls
│   └── audits.ts          # Audit API calls
├── features/              # Feature modules
│   ├── students/          # Student management
│   ├── files/             # File management
│   ├── email/             # Email campaigns
│   └── insights/          # Analytics dashboard
├── components/            # Shared components
├── styles/                # Theme and styling
├── tests/                 # Test utilities
└── utils/                 # Utility functions
```

## 🛠 Setup Instructions

### Prerequisites

- Node.js 18+ and npm
- Firebase project with Authentication enabled
- Backend API running (see backend README)

### Environment Setup

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure Firebase:**
   ```env
   VITE_FIREBASE_API_KEY=your-api-key
   VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
   VITE_FIREBASE_PROJECT_ID=your-project-id
   VITE_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
   VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
   VITE_FIREBASE_APP_ID=1:123456789:web:abcdef
   ```

3. **Configure API:**
   ```env
   VITE_API_BASE_URL=/api/v1
   VITE_ENV=development
   ```

### Installation & Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

3. **Open browser:**
   Navigate to `http://localhost:5173`

## 🔐 Authentication & Authorization

### Login Methods

- **Email/Password**: Standard Firebase authentication
- **Google OAuth**: One-click Google sign-in

### User Roles

| Role  | Permissions |
|-------|-------------|
| **Admin** | Full access: CRUD students, bulk operations, email campaigns, audit logs, user management |
| **Staff** | Limited access: View/create students, send emails, view insights (no delete/bulk operations) |

### Token Flow

1. User authenticates with Firebase
2. Firebase ID token is obtained
3. Token is sent to backend for role verification
4. Backend returns user role and permissions
5. Frontend enforces role-based UI restrictions
6. Axios automatically includes token in API requests

## 📱 Features & Pages

### Dashboard (`/`)
- **KPI Cards**: Total students, active users, pending follow-ups
- **Status Breakdown**: Students by application stage
- **Country Analytics**: Geographic distribution
- **Quick Actions**: Common tasks and navigation

### Students Management (`/students`)
- **List View**: Paginated table with search and filters
- **Advanced Filters**: Status, country, date ranges, text search
- **Bulk Operations** (Admin only): CSV/JSON import/export
- **Sorting**: Multi-column sorting with persistence
- **URL State**: Filters persist in URL for sharing

### Student Detail (`/students/:id`)
- **Profile Tab**: Basic info editing (admin only)
- **Files Tab**: Document upload with drag & drop, file management
- **Activity Tab**: Audit logs, email history, quick actions

### Email Campaigns (`/campaigns`)
- **Recipient Selection**: Filter-based targeting
- **Template System**: Reusable email templates with variables
- **Preview**: Email preview with variable substitution
- **Campaign History**: Sent campaigns with delivery stats

### File Management
- **Upload Interface**: Drag & drop with progress indicators
- **File Types**: PDF, DOC, images with validation
- **Metadata**: Upload tracking, file size, timestamps
- **Download**: Secure file access with authentication

## 🧪 Testing

### Test Commands

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests once (CI mode)
npm run test:run

# Generate coverage report
npm run test:coverage

# Interactive test UI
npm run test:ui
```

### Test Structure

- **Unit Tests**: Component behavior and logic
- **Integration Tests**: Feature workflows
- **Mock Services**: API and Firebase mocking
- **Test Utilities**: Shared helpers and providers

### Key Test Files

```
src/
├── auth/
│   ├── LoginPage.test.tsx      # Login flow testing
│   └── Guarded.test.tsx        # Route protection
├── features/
│   ├── students/
│   │   ├── StudentsListPage.test.tsx
│   │   └── StudentDetailPage.test.tsx
│   └── email/
│       └── CampaignsPage.test.tsx
└── tests/
    ├── setup.ts               # Global test setup
    └── utils.tsx              # Test utilities
```

## 🎨 UI/UX Guidelines

### Design System

- **Theme**: Material Design with custom branding
- **Colors**: Primary blue, semantic colors for status
- **Typography**: Roboto font family with consistent scales
- **Spacing**: 8px grid system
- **Elevation**: Consistent shadow depths

### Accessibility

- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: Proper ARIA labels and roles
- **Color Contrast**: WCAG AA compliance
- **Focus Management**: Visible focus indicators

### Responsive Design

- **Mobile First**: Progressive enhancement
- **Breakpoints**: xs, sm, md, lg, xl
- **Navigation**: Collapsible sidebar on mobile
- **Tables**: Horizontal scroll on small screens

## 🔧 Development Guidelines

### Code Style

- **TypeScript**: Strict mode enabled
- **ESLint**: Configured for React and TypeScript
- **Prettier**: Consistent code formatting
- **Imports**: Absolute imports with path mapping

### State Management

- **React Query**: Server state and caching
- **React Context**: Authentication and theme
- **Local State**: Component-specific state with hooks
- **URL State**: Filter and pagination persistence

### Error Handling

- **Error Boundaries**: Graceful error recovery
- **API Errors**: Consistent error mapping
- **User Feedback**: Toast notifications and alerts
- **Retry Logic**: Automatic retry for failed requests

## 🚀 Build & Deployment

### Build Commands

```bash
# Type checking
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

### Build Output

- **Static Assets**: Optimized bundles in `dist/`
- **Code Splitting**: Automatic route-based splitting
- **Tree Shaking**: Unused code elimination
- **Asset Optimization**: Image and font optimization

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_FIREBASE_*` | Firebase configuration | Required |
| `VITE_API_BASE_URL` | Backend API base URL | `/api/v1` |
| `VITE_ENV` | Environment mode | `development` |

## 📊 Performance

### Optimization Strategies

- **Code Splitting**: Route-based lazy loading
- **React Query**: Intelligent caching and background updates
- **Image Optimization**: WebP format with fallbacks
- **Bundle Analysis**: Webpack bundle analyzer integration

### Performance Metrics

- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

## 🐛 Troubleshooting

### Common Issues

1. **Firebase Connection**:
   - Check environment variables
   - Verify Firebase project configuration
   - Ensure authentication is enabled

2. **API Connection**:
   - Verify backend is running
   - Check CORS configuration
   - Validate API base URL

3. **Build Errors**:
   - Clear node_modules and reinstall
   - Check TypeScript errors
   - Verify environment variables

### Debug Mode

Enable debug logging:
```env
VITE_DEBUG=true
```

## 📚 Additional Resources

- [React Documentation](https://react.dev)
- [Material-UI Documentation](https://mui.com)
- [TanStack Query Documentation](https://tanstack.com/query)
- [Firebase Documentation](https://firebase.google.com/docs)
- [Vite Documentation](https://vitejs.dev)

## 🤝 Contributing

1. Follow the established code style
2. Write tests for new features
3. Update documentation as needed
4. Use conventional commit messages
5. Ensure all tests pass before submitting

---

For backend setup and API documentation, see the [Backend README](../backend/README.md).