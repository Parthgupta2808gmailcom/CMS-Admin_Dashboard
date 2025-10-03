import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  MenuItem,
  Fab,
  Paper,
  Divider,
} from '@mui/material';
import {
  Add,
  Send,
  Visibility,
  FilterList,
  Search,
  Email,
  Schedule,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { emailApi } from '../../api/email';
import type { EmailCampaign } from '../../api/email';
import { StudentsApi } from '../../api/students';
import { queryKeys } from '../../api/queryKeys';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { EmailComposer } from './EmailComposer';

const APPLICATION_STATUSES = ['Exploring', 'Shortlisting', 'Applying', 'Submitted'];

export function CampaignsPage() {
  const [composeDialogOpen, setComposeDialogOpen] = useState(false);
  const [selectedStudents, setSelectedStudents] = useState<any[]>([]);
  const [filters, setFilters] = useState({
    status: '',
    country: '',
    search: '',
  });

  // Fetch campaigns
  const { data: campaignsData, isLoading: campaignsLoading, error: campaignsError } = useQuery({
    queryKey: queryKeys.email.campaigns(),
    queryFn: () => emailApi.getCampaigns({ limit: 50 }),
  });

  // Fetch students for recipient selection
  const { data: studentsData } = useQuery({
    queryKey: queryKeys.students.list(filters),
    queryFn: () => StudentsApi.getStudents({
      ...filters,
      limit: 1000, // Get all students for selection
    }),
  });

  const handleComposeNew = () => {
    // Apply current filters to get recipient list
    const filteredStudents = studentsData?.students || [];
    setSelectedStudents(filteredStudents);
    setComposeDialogOpen(true);
  };

  const handleFilterChange = (field: string, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (status) {
      case 'completed': return 'success';
      case 'sending': return 'info';
      case 'failed': return 'error';
      case 'draft': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle />;
      case 'sending': return <Schedule />;
      case 'failed': return <Error />;
      case 'draft': return <Email />;
      default: return <Email />;
    }
  };

  if (campaignsLoading) return <LoadingState />;
  if (campaignsError) return <ErrorState error={campaignsError} />;

  const campaigns = campaignsData?.campaigns || [];

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Email Campaigns
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleComposeNew}
        >
          New Campaign
        </Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recipient Filters
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Configure filters to select recipients for your email campaign
          </Typography>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField
                fullWidth
                label="Search Students"
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                placeholder="Name or email..."
                InputProps={{
                  startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField
                fullWidth
                select
                label="Application Status"
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
              >
                <MenuItem value="">All Statuses</MenuItem>
                {APPLICATION_STATUSES.map((status) => (
                  <MenuItem key={status} value={status}>
                    {status}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <TextField
                fullWidth
                label="Country"
                value={filters.country}
                onChange={(e) => handleFilterChange('country', e.target.value)}
                placeholder="Filter by country..."
              />
            </Grid>
          </Grid>
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Selected Recipients: {studentsData?.students?.length || 0} students
            </Typography>
            <Button
              variant="outlined"
              size="small"
              startIcon={<Send />}
              onClick={handleComposeNew}
              disabled={!studentsData?.students?.length}
            >
              Compose Email
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Campaigns List */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Campaigns
          </Typography>
          {campaigns.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Email sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No campaigns yet
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Create your first email campaign to get started
              </Typography>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Subject</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Recipients</TableCell>
                    <TableCell>Sent</TableCell>
                    <TableCell>Failed</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Created By</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {campaigns.map((campaign) => (
                    <TableRow key={campaign.id} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {campaign.subject}
                        </Typography>
                        {campaign.template && (
                          <Typography variant="caption" color="text.secondary">
                            Template: {campaign.template}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={getStatusIcon(campaign.status)}
                          label={campaign.status.charAt(0).toUpperCase() + campaign.status.slice(1)}
                          color={getStatusColor(campaign.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {campaign.recipients}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="success.main">
                          {campaign.sent}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="error.main">
                          {campaign.failed}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {new Date(campaign.createdAt).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {campaign.createdBy}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <IconButton size="small" title="View Details">
                          <Visibility />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Compose Email Dialog */}
      <Dialog
        open={composeDialogOpen}
        onClose={() => setComposeDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Send />
            New Email Campaign
          </Box>
        </DialogTitle>
        <DialogContent>
          <EmailComposer
            recipients={selectedStudents.map(student => ({
              id: student.id,
              name: student.name,
              email: student.email,
            }))}
            onSend={() => {
              setComposeDialogOpen(false);
              // Refresh campaigns list
              // queryClient.invalidateQueries({ queryKey: queryKeys.email.campaigns() });
            }}
            onCancel={() => setComposeDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
}
