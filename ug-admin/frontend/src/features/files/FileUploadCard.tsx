import React, { useCallback, useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  LinearProgress,
  Alert,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import { Upload, CloudUpload, Cancel, CheckCircle, Error } from '@mui/icons-material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { filesApi } from '../../api/files';
import { queryKeys } from '../../api/queryKeys';

interface FileUploadCardProps {
  studentId: string;
}

interface UploadingFile {
  file: File;
  progress: number;
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

export function FileUploadCard({ studentId }: FileUploadCardProps) {
  const [dragActive, setDragActive] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: ({ file, metadata }: { file: File; metadata?: Record<string, any> }) =>
      filesApi.uploadFile(studentId, file, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.files.studentFiles(studentId) });
    },
  });

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files) return;

    const fileArray = Array.from(files);
    const newUploadingFiles: UploadingFile[] = fileArray.map(file => ({
      file,
      progress: 0,
      status: 'uploading' as const,
    }));

    setUploadingFiles(prev => [...prev, ...newUploadingFiles]);

    // Upload each file
    fileArray.forEach(async (file, index) => {
      try {
        // Simulate progress updates
        const progressInterval = setInterval(() => {
          setUploadingFiles(prev => prev.map((uf, i) => 
            i === prev.length - fileArray.length + index
              ? { ...uf, progress: Math.min(uf.progress + 10, 90) }
              : uf
          ));
        }, 200);

        await uploadMutation.mutateAsync({ file });

        clearInterval(progressInterval);
        setUploadingFiles(prev => prev.map((uf, i) => 
          i === prev.length - fileArray.length + index
            ? { ...uf, progress: 100, status: 'success' as const }
            : uf
        ));

        // Remove successful uploads after 2 seconds
        setTimeout(() => {
          setUploadingFiles(prev => prev.filter((_, i) => 
            i !== prev.length - fileArray.length + index
          ));
        }, 2000);

      } catch (error: any) {
        setUploadingFiles(prev => prev.map((uf, i) => 
          i === prev.length - fileArray.length + index
            ? { 
                ...uf, 
                progress: 0, 
                status: 'error' as const, 
                error: error.message || 'Upload failed' 
              }
            : uf
        ));
      }
    });
  }, [studentId, uploadMutation]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
  }, [handleFiles]);

  const removeUploadingFile = (index: number) => {
    setUploadingFiles(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Upload Files
        </Typography>
        
        {/* Drop Zone */}
        <Box
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          sx={{
            border: '2px dashed',
            borderColor: dragActive ? 'primary.main' : 'grey.300',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            backgroundColor: dragActive ? 'action.hover' : 'transparent',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            '&:hover': {
              borderColor: 'primary.main',
              backgroundColor: 'action.hover',
            },
          }}
        >
          <input
            type="file"
            multiple
            onChange={handleFileInput}
            style={{ display: 'none' }}
            id="file-upload-input"
            accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif"
          />
          <label htmlFor="file-upload-input" style={{ cursor: 'pointer' }}>
            <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
            <Typography variant="h6" gutterBottom>
              Drop files here or click to browse
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Supported formats: PDF, DOC, DOCX, TXT, JPG, PNG, GIF
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Maximum file size: 10MB
            </Typography>
          </label>
        </Box>

        {/* Upload Progress */}
        {uploadingFiles.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Uploading Files
            </Typography>
            <List dense>
              {uploadingFiles.map((uploadingFile, index) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={uploadingFile.file.name}
                    secondary={
                      <Box>
                        {uploadingFile.status === 'uploading' && (
                          <LinearProgress 
                            variant="determinate" 
                            value={uploadingFile.progress} 
                            sx={{ mt: 1 }}
                          />
                        )}
                        {uploadingFile.status === 'error' && (
                          <Alert severity="error" sx={{ mt: 1 }}>
                            {uploadingFile.error}
                          </Alert>
                        )}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    {uploadingFile.status === 'uploading' && (
                      <IconButton
                        edge="end"
                        onClick={() => removeUploadingFile(index)}
                      >
                        <Cancel />
                      </IconButton>
                    )}
                    {uploadingFile.status === 'success' && (
                      <CheckCircle color="success" />
                    )}
                    {uploadingFile.status === 'error' && (
                      <Error color="error" />
                    )}
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
