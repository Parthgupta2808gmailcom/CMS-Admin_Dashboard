import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  CircularProgress,
} from '@mui/material';
import { Download, Delete, Visibility, InsertDriveFile } from '@mui/icons-material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { filesApi } from '../../api/files';
import type { StudentFile } from '../../api/files';
import { queryKeys } from '../../api/queryKeys';
import { useAuth } from '../../app/providers/AuthProvider';
import { isAdmin } from '../../auth/roles';

interface FileListProps {
  files: StudentFile[];
}

export function FileList({ files }: FileListProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [fileToDelete, setFileToDelete] = useState<StudentFile | null>(null);

  const userIsAdmin = user ? isAdmin(user) : false;

  const deleteMutation = useMutation({
    mutationFn: (file: StudentFile) => filesApi.deleteFile(file.studentId, file.id),
    onSuccess: (_, file) => {
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.files.studentFiles(file.studentId) 
      });
      setDeleteDialogOpen(false);
      setFileToDelete(null);
    },
  });

  const handleDownload = async (file: StudentFile) => {
    try {
      // For demo purposes, we'll use the downloadUrl directly
      // In a real app, you might want to get a fresh download URL
      const link = document.createElement('a');
      link.href = file.downloadUrl;
      link.download = file.originalName;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleDeleteClick = (file: StudentFile) => {
    setFileToDelete(file);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (fileToDelete) {
      deleteMutation.mutate(fileToDelete);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileTypeColor = (fileType: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    if (fileType.includes('pdf')) return 'error';
    if (fileType.includes('image')) return 'info';
    if (fileType.includes('document') || fileType.includes('word')) return 'primary';
    if (fileType.includes('text')) return 'secondary';
    return 'default';
  };

  if (files.length === 0) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <InsertDriveFile sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              No files uploaded yet
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Upload files using the form above
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Files ({files.length})
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Uploaded</TableCell>
                  <TableCell>Uploaded By</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {files.map((file) => (
                  <TableRow key={file.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <InsertDriveFile color="action" />
                        <Typography variant="body2">
                          {file.originalName}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={file.fileType.split('/')[1]?.toUpperCase() || 'FILE'}
                        size="small"
                        color={getFileTypeColor(file.fileType)}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatFileSize(file.fileSize)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(file.uploadedAt).toLocaleDateString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {file.uploadedBy}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <IconButton
                          size="small"
                          onClick={() => handleDownload(file)}
                          title="Download"
                        >
                          <Download />
                        </IconButton>
                        {userIsAdmin && (
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteClick(file)}
                            title="Delete"
                            color="error"
                          >
                            <Delete />
                          </IconButton>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete File</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{fileToDelete?.originalName}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? <CircularProgress size={20} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
