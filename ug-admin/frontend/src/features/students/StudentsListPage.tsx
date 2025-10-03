/**
 * Students List Page Component
 * 
 * Main page for viewing and managing students with search, filtering,
 * pagination, and bulk operations.
 */

import { useState, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TextField,
  InputAdornment,
  Chip,
  Stack,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  FileUpload as ImportIcon,
  FileDownload as ExportIcon,
  FilterList as FilterIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { useStudentsQuery, useBulkImportMutation } from './useStudentsQuery';
// StudentsTable component will be defined inline below
// Components will be defined inline below
import { useAuth } from '../../app/providers/AuthProvider';
import { canPerformAction } from '../../auth/roles';

/**
 * Simple placeholder components
 */
function StudentFilters() {
  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="body2" color="text.secondary">
        Advanced filters coming soon...
      </Typography>
    </Box>
  );
}

function BulkImportDialog({ open, onClose }: any) {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Bulk Import</DialogTitle>
      <DialogContent>
        <Typography>Bulk import functionality coming soon...</Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}

function CreateStudentDialog({ open, onClose }: any) {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Create Student</DialogTitle>
      <DialogContent>
        <Typography>Create student form coming soon...</Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}

/**
 * Simple Students Table Component
 */
interface StudentsTableProps {
  students: any[];
  loading: boolean;
  pageInfo: any;
  currentSort: string;
  currentOrder: 'asc' | 'desc';
  onStudentClick: (id: string) => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onSortChange: (sort: string, order: 'asc' | 'desc') => void;
}

function StudentsTable({
  students,
  pageInfo,
  onStudentClick,
  onPageChange,
  onPageSizeChange,
}: StudentsTableProps) {
  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%',
      overflow: 'hidden'
    }}>
      <TableContainer sx={{ 
        flex: 1, 
        overflow: 'auto',
        '&::-webkit-scrollbar': {
          width: '8px',
          height: '8px',
        },
        '&::-webkit-scrollbar-track': {
          backgroundColor: 'rgba(0,0,0,0.1)',
        },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor: 'rgba(0,0,0,0.2)',
          borderRadius: '4px',
        },
      }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>Name</TableCell>
              <TableCell sx={{ display: { xs: 'table-cell', md: 'none' } }}>Student</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Email</TableCell>
              <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' } }}>Country</TableCell>
              <TableCell>Status</TableCell>
              <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>Last Active</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {students.map((student) => (
              <TableRow key={student.id} hover onClick={() => onStudentClick(student.id)} sx={{ cursor: 'pointer' }}>
                {/* Desktop Name Column */}
                <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                  {student.name}
                </TableCell>
                
                {/* Mobile Combined Column */}
                <TableCell sx={{ display: { xs: 'table-cell', md: 'none' } }}>
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      {student.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {student.email}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        {student.country}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                  {student.email}
                </TableCell>
                <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' } }}>
                  {student.country}
                </TableCell>
                <TableCell>
                  <Chip 
                    label={student.application_status} 
                    size="small"
                    color={student.application_status === 'Submitted' ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                  {student.last_active ? new Date(student.last_active).toLocaleDateString() : 'Never'}
                </TableCell>
                <TableCell align="right">
                  <IconButton 
                    size="small" 
                    onClick={(e) => {
                      e.stopPropagation();
                      onStudentClick(student.id);
                    }}
                    title="View Details"
                  >
                    <ViewIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      <TablePagination
        component="div"
        count={pageInfo.total_count || 0}
        page={(pageInfo.current_page || 1) - 1}
        onPageChange={(_, newPage) => onPageChange(newPage + 1)}
        rowsPerPage={pageInfo.limit || 25}
        onRowsPerPageChange={(e) => onPageSizeChange(parseInt(e.target.value, 10))}
        rowsPerPageOptions={[10, 25, 50, 100]}
        sx={{ 
          flexShrink: 0,
          borderTop: 1,
          borderColor: 'divider',
          '& .MuiTablePagination-toolbar': {
            minHeight: { xs: '52px', sm: '64px' }
          }
        }}
      />
    </Box>
  );
}

/**
 * Students List Page Component
 */
export function StudentsListPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();

  // Local state
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [showFilters, setShowFilters] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  // Parse URL parameters
  const currentParams = useMemo(() => ({
    page: parseInt(searchParams.get('page') || '1', 10),
    limit: parseInt(searchParams.get('limit') || '25', 10),
    search: searchParams.get('search') || '',
    status: searchParams.get('status') || '',
    country: searchParams.get('country') || '',
    sort: searchParams.get('sort') || 'created_at',
    order: (searchParams.get('order') || 'desc') as 'asc' | 'desc',
  }), [searchParams]);

  // Queries
  const studentsQuery = useStudentsQuery(currentParams);
  const bulkImportMutation = useBulkImportMutation();

  // Permissions
  const canCreate = canPerformAction(user, 'canCreateStudents');
  const canImport = canPerformAction(user, 'canImportStudents');
  const canExport = canPerformAction(user, 'canExportStudents');

  /**
   * Update URL parameters
   */
  const updateParams = (newParams: Partial<typeof currentParams>) => {
    const updatedParams = { ...currentParams, ...newParams };
    
    // Remove empty values
    Object.keys(updatedParams).forEach(key => {
      const value = updatedParams[key as keyof typeof updatedParams];
      if (!value || value === '' || (key === 'page' && value === 1)) {
        searchParams.delete(key);
      } else {
        searchParams.set(key, value.toString());
      }
    });

    setSearchParams(searchParams);
  };

  /**
   * Handle search input
   */
  const handleSearch = (value: string) => {
    setSearchQuery(value);
    updateParams({ search: value, page: 1 });
  };

  /**
   * Handle filter changes
   */
  const handleFilterChange = (filters: { status?: string; country?: string }) => {
    updateParams({ ...filters, page: 1 });
  };

  /**
   * Handle pagination
   */
  const handlePageChange = (page: number) => {
    updateParams({ page });
  };

  /**
   * Handle page size change
   */
  const handlePageSizeChange = (limit: number) => {
    updateParams({ limit, page: 1 });
  };

  /**
   * Handle sorting
   */
  const handleSortChange = (sort: string, order: 'asc' | 'desc') => {
    updateParams({ sort, order });
  };

  /**
   * Handle export
   */
  const handleExport = async () => {
    try {
      const exportParams = {
        format_type: 'csv' as const,
        ...(currentParams.status && { application_status: currentParams.status }),
        ...(currentParams.country && { country: currentParams.country }),
      };
      
      // This will trigger download
      await import('../../api/students').then(({ StudentsApi }) =>
        StudentsApi.exportStudents(exportParams)
      );
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  /**
   * Handle student row click
   */
  const handleStudentClick = (studentId: string) => {
    navigate(`/students/${studentId}`);
  };

  // Loading state
  if (studentsQuery.isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <Typography>Loading students...</Typography>
      </Box>
    );
  }

  // Error state
  if (studentsQuery.error) {
    return (
      <Box display="flex" flexDirection="column" alignItems="center" minHeight="200px" gap={2}>
        <Typography color="error">Failed to load students</Typography>
        <Button onClick={() => studentsQuery.refetch()}>Retry</Button>
      </Box>
    );
  }

  const { students, total_count, page_info } = studentsQuery.data || {
    students: [],
    total_count: 0,
    page_info: {
      limit: 25,
      offset: 0,
      current_page: 1,
      total_pages: 1,
      has_next: false,
      has_previous: false,
    },
  };

  return (
    <Box sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* Page Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={{ xs: 2, sm: 3 }} sx={{ flexShrink: 0 }}>
        <Box>
          <Typography 
            variant="h4" 
            gutterBottom
            sx={{
              fontSize: { xs: '1.5rem', sm: '2.125rem' }
            }}
          >
            Students
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' } }}>
            Manage student applications and profiles
          </Typography>
        </Box>

        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
          {canExport && (
            <Button
              variant="outlined"
              startIcon={<ExportIcon />}
              onClick={handleExport}
              sx={{ 
                fontSize: { xs: '0.75rem', sm: '0.875rem' },
                minHeight: { xs: '32px', sm: '36px' },
                px: { xs: 1, sm: 2 }
              }}
            >
              Export
            </Button>
          )}
          
          {canImport && (
            <Button
              variant="outlined"
              startIcon={<ImportIcon />}
              onClick={() => setShowImportDialog(true)}
              sx={{ 
                fontSize: { xs: '0.75rem', sm: '0.875rem' },
                minHeight: { xs: '32px', sm: '36px' },
                px: { xs: 1, sm: 2 }
              }}
            >
              Import
            </Button>
          )}
          
          {canCreate && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setShowCreateDialog(true)}
              sx={{ 
                fontSize: { xs: '0.75rem', sm: '0.875rem' },
                minHeight: { xs: '32px', sm: '36px' },
                px: { xs: 1, sm: 2 }
              }}
            >
              <Box sx={{ display: { xs: 'none', sm: 'block' } }}>Add Student</Box>
              <Box sx={{ display: { xs: 'block', sm: 'none' } }}>Add</Box>
            </Button>
          )}
        </Stack>
      </Box>

      {/* Scrollable Content Area */}
      <Box sx={{ 
        flex: 1, 
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: { xs: 2, sm: 3 }
      }}>
        {/* Search and Filters */}
        <Card sx={{ flexShrink: 0 }}>
          <CardContent>
          <Stack spacing={2}>
            {/* Search Bar */}
            <TextField
              fullWidth
              placeholder="Search students by name or email..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />

            {/* Quick Filters */}
            <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
              <Button
                size="small"
                startIcon={<FilterIcon />}
                onClick={() => setShowFilters(!showFilters)}
                variant={showFilters ? 'contained' : 'outlined'}
              >
                Filters
              </Button>

              {/* Active Filter Chips */}
              {currentParams.status && (
                <Chip
                  label={`Status: ${currentParams.status}`}
                  onDelete={() => handleFilterChange({ status: '' })}
                  size="small"
                />
              )}
              
              {currentParams.country && (
                <Chip
                  label={`Country: ${currentParams.country}`}
                  onDelete={() => handleFilterChange({ country: '' })}
                  size="small"
                />
              )}

              {/* Results Count */}
              <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                {total_count} students found
              </Typography>
            </Box>

            {/* Expanded Filters */}
            {showFilters && (
              <>
                <Divider />
                <StudentFilters />
              </>
            )}
          </Stack>
        </CardContent>
      </Card>

        {/* Students Table */}
        <Card sx={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          minHeight: 0 // Important for flex child to shrink
        }}>
          <StudentsTable
            students={students}
            loading={studentsQuery.isFetching}
            pageInfo={page_info}
            currentSort={currentParams.sort}
            currentOrder={currentParams.order}
            onStudentClick={handleStudentClick}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
            onSortChange={handleSortChange}
          />
        </Card>
      </Box>

      {/* Dialogs */}
      {showImportDialog && (
        <BulkImportDialog
          open={showImportDialog}
          onClose={() => setShowImportDialog(false)}
          onImport={bulkImportMutation.mutate}
          loading={bulkImportMutation.isPending}
        />
      )}

      {showCreateDialog && (
        <CreateStudentDialog
          open={showCreateDialog}
          onClose={() => setShowCreateDialog(false)}
        />
      )}
    </Box>
  );
}

export default StudentsListPage;
