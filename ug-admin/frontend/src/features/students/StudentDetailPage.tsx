import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Button,
  Card,
  CardContent,
  Chip,
  TextField,
  MenuItem,
  Alert,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
} from '@mui/material'; 

import {
  ArrowBack,
  Edit,
  Save,
  Cancel,
  Upload,
  Download,
  Email,
  History,
  Delete,
  Person,
  AttachFile,
  Send,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { StudentsApi } from '../../api/students';
import { filesApi } from '../../api/files';
import { emailApi } from '../../api/email';
import { auditsApi } from '../../api/audits';
import { queryKeys } from '../../api/queryKeys';
import { useAuth } from '../../app/providers/AuthProvider'; 
import { isAdmin, isStaff } from '../../auth/roles';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { FileUploadCard } from '../../features/files/FileUploadCard';
import { FileList } from '../../features/files/FileList';
import { EmailComposer } from '../../features/email/EmailComposer';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`student-tabpanel-${index}`}
      aria-labelledby={`student-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const APPLICATION_STATUSES = [
  'Exploring',
  'Shortlisting', 
  'Applying',
  'Submitted'
];

export function StudentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [tabValue, setTabValue] = useState(0);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<any>({});
  const [emailDialogOpen, setEmailDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const userIsAdmin = user ? isAdmin(user) : false;
  const userIsStaff = user ? isStaff(user) : false;

  // Fetch student data
  const { data: student, isLoading, error } = useQuery({
    queryKey: queryKeys.students.detail(id!),
    queryFn: () => StudentsApi.getStudent(id!),
    enabled: !!id,
  });

  // Fetch student files
  const { data: files } = useQuery({
    queryKey: queryKeys.files.studentFiles(id!),
    queryFn: () => filesApi.getStudentFiles(id!),
    enabled: !!id,
  });

  // Fetch student audit logs
  const { data: auditLogs } = useQuery({
    queryKey: queryKeys.audits.byTarget(id!),
    queryFn: () => auditsApi.getAuditLogs({ target: id!, limit: 10 }),
    enabled: !!id,
  });

  // Update student mutation
  const updateMutation = useMutation({
    mutationFn: (data: any) => StudentsApi.updateStudent(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.students.detail(id!) });
      queryClient.invalidateQueries({ queryKey: queryKeys.students.list() });
      setIsEditing(false);
    },
  });

  // Delete student mutation
  const deleteMutation = useMutation({
    mutationFn: () => StudentsApi.deleteStudent(id!),
    onSuccess: () => {
      navigate('/students');
    },
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleEditStart = () => {
    setEditForm({ ...student });
    setIsEditing(true);
  };

  const handleEditCancel = () => {
    setIsEditing(false);
    setEditForm({});
  };

  const handleEditSave = () => {
    updateMutation.mutate(editForm);
  };

  const handleDelete = () => {
    deleteMutation.mutate();
  };

  const handleFormChange = (field: string, value: any) => {
    setEditForm((prev: any) => ({ ...prev, [field]: value }));
  };

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!student) return <ErrorState error={new Error('Student not found')} />;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate('/students')}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
          {student.student.name}
        </Typography>
        {userIsAdmin && (
          <Box sx={{ display: 'flex', gap: 1 }}>
            {!isEditing ? (
              <Button
                variant="outlined"
                startIcon={<Edit />}
                onClick={handleEditStart}
              >
                Edit
              </Button>
            ) : (
              <>
                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={handleEditSave}
                  disabled={updateMutation.isPending}
                >
                  Save
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Cancel />}
                  onClick={handleEditCancel}
                >
                  Cancel
                </Button>
              </>
            )}
            <Button
              variant="outlined"
              color="error"
              startIcon={<Delete />}
              onClick={() => setDeleteDialogOpen(true)}
            >
              Delete
            </Button>
          </Box>
        )}
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab icon={<Person />} label="Profile" />
          <Tab icon={<AttachFile />} label="Files" />
          <Tab icon={<History />} label="Activity" />
        </Tabs>

        {/* Profile Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Basic Information
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <TextField
                        fullWidth
                        label="Name"
                        value={isEditing ? editForm.name : student.student.name}
                        onChange={(e) => handleFormChange('name', e.target.value)}
                        disabled={!isEditing}
                      />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <TextField
                        fullWidth
                        label="Email"
                        value={isEditing ? editForm.email : student.student.email}
                        onChange={(e) => handleFormChange('email', e.target.value)}
                        disabled={!isEditing}
                      />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <TextField
                        fullWidth
                        label="Phone"
                        value={isEditing ? editForm.phone || '' : student.student.phone || ''}
                        onChange={(e) => handleFormChange('phone', e.target.value)}
                        disabled={!isEditing}
                      />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <TextField
                        fullWidth
                        label="Country"
                        value={isEditing ? editForm.country : student.student.country}
                        onChange={(e) => handleFormChange('country', e.target.value)}
                        disabled={!isEditing}
                      />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <TextField
                        fullWidth
                        label="Grade"
                        value={isEditing ? editForm.grade || '' : student.student.grade || ''}
                        onChange={(e) => handleFormChange('grade', e.target.value)}
                        disabled={!isEditing}
                      />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <TextField
                        fullWidth
                        select
                        label="Application Status"
                        value={isEditing ? editForm.applicationStatus : student.student.application_status}
                        onChange={(e) => handleFormChange('applicationStatus', e.target.value)}
                        disabled={!isEditing}
                      >
                        {APPLICATION_STATUSES.map((status) => (
                          <MenuItem key={status} value={status}>
                            {status}
                          </MenuItem>
                        ))}
                      </TextField>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Status
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Chip
                      label={student.student.application_status}
                      color={
                        student.student.application_status === 'Submitted' ? 'success' :
                        student.student.application_status === 'Applying' ? 'warning' :
                        'default'
                      }
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Last Active: {new Date(student.student.last_active || '').toLocaleDateString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Created: {new Date(student.student.created_at || '').toLocaleDateString()}
                  </Typography>
                  {student.student.ai_summary && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        AI Summary
                      </Typography>
                      <Typography variant="body2">
                        {student.student.ai_summary}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Files Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <FileUploadCard studentId={id!} />
            </Grid>
            <Grid size={12}>
              <FileList files={files || []} />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Activity Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 8 }}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">
                      Recent Activity
                    </Typography>
                    {(userIsAdmin || userIsStaff) && (
                      <Button
                        variant="outlined"
                        startIcon={<Send />}
                        onClick={() => setEmailDialogOpen(true)}
                      >
                        Send Email
                      </Button>
                    )}
                  </Box>
                  <List>
                    {auditLogs?.entries?.map((log: any) => (
                      <ListItem key={log.id}>
                        <ListItemIcon>
                          <History />
                        </ListItemIcon>
                        <ListItemText
                          primary={log.action}
                          secondary={`${log.user} • ${new Date(log.timestamp).toLocaleString()}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Quick Actions
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Button
                      variant="outlined"
                      startIcon={<Email />}
                      onClick={() => setEmailDialogOpen(true)}
                      disabled={!userIsAdmin && !userIsStaff}
                    >
                      Send Follow-up
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<Upload />}
                      disabled={!userIsAdmin && !userIsStaff}
                    >
                      Upload Document
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* Email Dialog */}
      <Dialog
        open={emailDialogOpen}
        onClose={() => setEmailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Send Email to {student.student.name}</DialogTitle>
        <DialogContent>
          <EmailComposer
            recipients={[student.student]}
            onSend={() => setEmailDialogOpen(false)}
            onCancel={() => setEmailDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Student</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete {student.student.name}? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDelete}
            color="error"
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? <CircularProgress size={20} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
