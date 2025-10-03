import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import { Send, Preview, Cancel } from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { emailApi, type EmailTemplate, type EmailRecipient } from '../../api/email';
import { queryKeys } from '../../api/queryKeys';

interface EmailComposerProps {
  recipients: EmailRecipient[];
  onSend?: () => void;
  onCancel?: () => void;
  preselectedTemplate?: string;
}

export function EmailComposer({ recipients, onSend, onCancel, preselectedTemplate }: EmailComposerProps) {
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState(preselectedTemplate || '');
  const [templateVariables, setTemplateVariables] = useState<Record<string, string>>({});
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewContent, setPreviewContent] = useState<{ subject: string; body: string } | null>(null);

  // Fetch email templates
  const { data: templates = [] } = useQuery({
    queryKey: queryKeys.email.templates(),
    queryFn: emailApi.getTemplates,
  });

  // Send email mutation
  const sendMutation = useMutation({
    mutationFn: emailApi.sendEmail,
    onSuccess: () => {
      onSend?.();
    },
  });

  // Preview email mutation
  const previewMutation = useMutation({
    mutationFn: ({ templateId, variables }: { templateId: string; variables: Record<string, any> }) =>
      emailApi.previewEmail(templateId, variables),
    onSuccess: (data) => {
      setPreviewContent(data);
      setPreviewOpen(true);
    },
  });

  // Update form when template changes
  useEffect(() => {
    const template = templates.find(t => t.id === selectedTemplate);
    if (template) {
      setSubject(template.subject);
      setBody(template.body);
      
      // Initialize template variables
      const initialVars: Record<string, string> = {};
      template.variables.forEach(variable => {
        initialVars[variable] = '';
      });
      setTemplateVariables(initialVars);
    } else {
      setSubject('');
      setBody('');
      setTemplateVariables({});
    }
  }, [selectedTemplate, templates]);

  const handleSend = () => {
    const emailData = {
      recipients: recipients.map(r => r.id),
      subject,
      body: selectedTemplate ? undefined : body,
      template: selectedTemplate || undefined,
      variables: Object.keys(templateVariables).length > 0 ? templateVariables : undefined,
    };

    sendMutation.mutate(emailData);
  };

  const handlePreview = () => {
    if (selectedTemplate) {
      previewMutation.mutate({
        templateId: selectedTemplate,
        variables: templateVariables,
      });
    } else {
      setPreviewContent({ subject, body });
      setPreviewOpen(true);
    }
  };

  const selectedTemplateData = templates.find(t => t.id === selectedTemplate);

  return (
    <Box>
      <Grid container spacing={3}>
        {/* Recipients */}
        <Grid size={{ xs: 12 }}>
          <Typography variant="h6" gutterBottom>
            Recipients ({recipients.length})
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
            {recipients.slice(0, 10).map((recipient) => (
              <Chip
                key={recipient.id}
                label={`${recipient.name} (${recipient.email})`}
                size="small"
              />
            ))}
            {recipients.length > 10 && (
              <Chip
                label={`+${recipients.length - 10} more`}
                size="small"
                variant="outlined"
              />
            )}
          </Box>
        </Grid>

        {/* Template Selection */}
        <Grid size={{ xs: 12 }}>
          <TextField
            fullWidth
            select
            label="Email Template"
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            helperText="Select a template or leave blank to compose manually"
          >
            <MenuItem value="">
              <em>No Template (Manual Compose)</em>
            </MenuItem>
            {templates.map((template) => (
              <MenuItem key={template.id} value={template.id}>
                {template.name}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        {/* Template Variables */}
        {selectedTemplateData && selectedTemplateData.variables.length > 0 && (
          <Grid size={{ xs: 12 }}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Template Variables
                </Typography>
                <Grid container spacing={2}>
                  {selectedTemplateData.variables.map((variable) => (
                    <Grid size={{ xs: 12, sm: 6 }} key={variable}>
                      <TextField
                        fullWidth
                        label={variable}
                        value={templateVariables[variable] || ''}
                        onChange={(e) => setTemplateVariables(prev => ({
                          ...prev,
                          [variable]: e.target.value,
                        }))}
                        placeholder={`Enter value for ${variable}`}
                      />
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Subject */}
        <Grid size={{ xs: 12 }}>
          <TextField
            fullWidth
            label="Subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={!!selectedTemplate}
            helperText={selectedTemplate ? 'Subject is controlled by the selected template' : ''}
          />
        </Grid>

        {/* Body */}
        <Grid size={{ xs: 12 }}>
          <TextField
            fullWidth
            multiline
            rows={8}
            label="Email Body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            disabled={!!selectedTemplate}
            helperText={selectedTemplate ? 'Body is controlled by the selected template' : ''}
          />
        </Grid>

        {/* Actions */}
        <Grid size={{ xs: 12 }}>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            {onCancel && (
              <Button
                variant="outlined"
                startIcon={<Cancel />}
                onClick={onCancel}
              >
                Cancel
              </Button>
            )}
            <Button
              variant="outlined"
              startIcon={<Preview />}
              onClick={handlePreview}
              disabled={previewMutation.isPending}
            >
              {previewMutation.isPending ? <CircularProgress size={20} /> : 'Preview'}
            </Button>
            <Button
              variant="contained"
              startIcon={<Send />}
              onClick={handleSend}
              disabled={sendMutation.isPending || !subject.trim() || (!body.trim() && !selectedTemplate)}
            >
              {sendMutation.isPending ? <CircularProgress size={20} /> : 'Send Email'}
            </Button>
          </Box>
        </Grid>

        {/* Success/Error Messages */}
        {sendMutation.isSuccess && (
          <Grid size={{ xs: 12 }}>
            <Alert severity="success">
              Email sent successfully to {recipients.length} recipient(s)!
            </Alert>
          </Grid>
        )}
        {sendMutation.isError && (
          <Grid size={{ xs: 12 }}>
            <Alert severity="error">
              Failed to send email: {sendMutation.error?.message}
            </Alert>
          </Grid>
        )}
      </Grid>

      {/* Preview Dialog */}
      <Dialog
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Email Preview</DialogTitle>
        <DialogContent>
          {previewContent && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Subject:
              </Typography>
              <Typography variant="body1" sx={{ mb: 2, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
                {previewContent.subject}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle1" gutterBottom>
                Body:
              </Typography>
              <Box
                sx={{
                  p: 2,
                  bgcolor: 'grey.50',
                  borderRadius: 1,
                  border: '1px solid',
                  borderColor: 'grey.300',
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                }}
              >
                {previewContent.body}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
