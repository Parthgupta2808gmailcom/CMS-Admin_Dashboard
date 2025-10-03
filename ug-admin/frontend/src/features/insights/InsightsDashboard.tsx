import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  People,
  PersonAdd,
  Email,
  TrendingUp,
  Public,
  Schedule,
  CheckCircle,
  Warning,
  Info,
  ArrowForward,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { StudentsApi } from '../../api/students';
import { queryKeys } from '../../api/queryKeys';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  onClick?: () => void;
}

function StatCard({ title, value, subtitle, icon, color = 'primary', onClick }: StatCardProps) {
  const content = (
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4" component="div" color={`${color}.main`}>
            {value}
          </Typography>
          <Typography variant="h6" color="text.secondary">
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box sx={{ color: `${color}.main`, opacity: 0.7 }}>
          {icon}
        </Box>
      </Box>
    </CardContent>
  );

  return (
    <Card sx={{ height: '100%' }}>
      {onClick ? (
        <CardActionArea onClick={onClick}>
          {content}
        </CardActionArea>
      ) : (
        content
      )}
    </Card>
  );
}

export function InsightsDashboard() {
  const navigate = useNavigate();

  // Fetch all students for analytics
  const { data: allStudentsData, isLoading, error } = useQuery({
    queryKey: queryKeys.students.list({ limit: 1000 }),
    queryFn: () => StudentsApi.getStudents({ limit: 1000 }),
  });

  // Fetch students by different statuses
  const { data: exploringStudents } = useQuery({
    queryKey: queryKeys.students.list({ status: 'Exploring' }),
    queryFn: () => StudentsApi.getStudents({ status: 'Exploring', limit: 1000 }),
  });

  const { data: shortlistingStudents } = useQuery({
    queryKey: queryKeys.students.list({ status: 'Shortlisting' }),
    queryFn: () => StudentsApi.getStudents({ status: 'Shortlisting', limit: 1000 }),
  });

  const { data: applyingStudents } = useQuery({
    queryKey: queryKeys.students.list({ status: 'Applying' }),
    queryFn: () => StudentsApi.getStudents({ status: 'Applying', limit: 1000 }),
  });

  const { data: submittedStudents } = useQuery({
    queryKey: queryKeys.students.list({ status: 'Submitted' }),
    queryFn: () => StudentsApi.getStudents({ status: 'Submitted', limit: 1000 }),
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;

  const students = allStudentsData?.students || [];
  const totalStudents = students.length;

  // Calculate metrics
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

  const recentlyActive = students.filter(student => 
    new Date(student.last_active || student.created_at) >= sevenDaysAgo
  ).length;

  const notContacted = students.filter(student => 
    student.application_status === 'Exploring' && 
    new Date(student.last_active || student.created_at) <= sevenDaysAgo
  ).length;

  // Country distribution
  const countryStats = students.reduce((acc, student) => {
    acc[student.country] = (acc[student.country] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const topCountries = Object.entries(countryStats)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5);

  const handleNavigateToStudents = (filters?: Record<string, any>) => {
    const searchParams = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) searchParams.set(key, value.toString());
      });
    }
    navigate(`/students?${searchParams.toString()}`);
  };

  return (
    <Box sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <Box sx={{ mb: { xs: 2, sm: 4 }, flexShrink: 0 }}>
        <Typography 
          variant="h4" 
          component="h1" 
          gutterBottom
          sx={{
            fontSize: { xs: '1.5rem', sm: '2.125rem' }
          }}
        >
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' } }}>
          Overview of student applications and engagement
        </Typography>
      </Box>

      {/* Scrollable Content */}
      <Box sx={{ 
        flex: 1, 
        overflow: 'auto',
        '&::-webkit-scrollbar': {
          width: '8px',
        },
        '&::-webkit-scrollbar-track': {
          backgroundColor: 'rgba(0,0,0,0.1)',
        },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor: 'rgba(0,0,0,0.2)',
          borderRadius: '4px',
        },
      }}>

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Total Students"
            value={totalStudents}
            icon={<People sx={{ fontSize: 40 }} />}
            color="primary"
            onClick={() => handleNavigateToStudents()}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Active (7d)"
            value={recentlyActive}
            subtitle={`${((recentlyActive / totalStudents) * 100).toFixed(1)}% of total`}
            icon={<TrendingUp sx={{ fontSize: 40 }} />}
            color="success"
            onClick={() => handleNavigateToStudents({ 
              lastActive: sevenDaysAgo.toISOString().split('T')[0] 
            })}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Not Contacted"
            value={notContacted}
            subtitle="Need follow-up"
            icon={<Warning sx={{ fontSize: 40 }} />}
            color="warning"
            onClick={() => handleNavigateToStudents({ 
              status: 'Exploring',
              lastActiveBefore: sevenDaysAgo.toISOString().split('T')[0]
            })}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Submitted"
            value={submittedStudents?.students?.length || 0}
            subtitle="Applications complete"
            icon={<CheckCircle sx={{ fontSize: 40 }} />}
            color="success"
            onClick={() => handleNavigateToStudents({ status: 'Submitted' })}
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Application Status Breakdown */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Application Status Breakdown
              </Typography>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <Info color="info" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Exploring"
                    secondary={`${exploringStudents?.students?.length || 0} students`}
                  />
                  <Button
                    size="small"
                    endIcon={<ArrowForward />}
                    onClick={() => handleNavigateToStudents({ status: 'Exploring' })}
                  >
                    View
                  </Button>
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemIcon>
                    <Schedule color="warning" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Shortlisting"
                    secondary={`${shortlistingStudents?.students?.length || 0} students`}
                  />
                  <Button
                    size="small"
                    endIcon={<ArrowForward />}
                    onClick={() => handleNavigateToStudents({ status: 'Shortlisting' })}
                  >
                    View
                  </Button>
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemIcon>
                    <PersonAdd color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Applying"
                    secondary={`${applyingStudents?.students?.length || 0} students`}
                  />
                  <Button
                    size="small"
                    endIcon={<ArrowForward />}
                    onClick={() => handleNavigateToStudents({ status: 'Applying' })}
                  >
                    View
                  </Button>
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemIcon>
                    <CheckCircle color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Submitted"
                    secondary={`${submittedStudents?.students?.length || 0} students`}
                  />
                  <Button
                    size="small"
                    endIcon={<ArrowForward />}
                    onClick={() => handleNavigateToStudents({ status: 'Submitted' })}
                  >
                    View
                  </Button>
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Countries */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Countries
              </Typography>
              <List>
                {topCountries.map(([country, count], index) => (
                  <React.Fragment key={country}>
                    <ListItem>
                      <ListItemIcon>
                        <Public color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={country}
                        secondary={`${count} students (${((count / totalStudents) * 100).toFixed(1)}%)`}
                      />
                      <Button
                        size="small"
                        endIcon={<ArrowForward />}
                        onClick={() => handleNavigateToStudents({ country })}
                      >
                        View
                      </Button>
                    </ListItem>
                    {index < topCountries.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<PersonAdd />}
                    onClick={() => navigate('/students/new')}
                  >
                    Add Student
                  </Button>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<Email />}
                    onClick={() => navigate('/campaigns')}
                  >
                    Send Campaign
                  </Button>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<Warning />}
                    onClick={() => handleNavigateToStudents({ 
                      status: 'Exploring',
                      lastActiveBefore: sevenDaysAgo.toISOString().split('T')[0]
                    })}
                  >
                    Follow Up Needed
                  </Button>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<People />}
                    onClick={() => navigate('/students')}
                  >
                    View All Students
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      </Box>
    </Box>
  );
}
