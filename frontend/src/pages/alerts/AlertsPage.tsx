// src/pages/alerts/AlertsPage.tsx
import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip, IconButton,
  Button, Select, MenuItem, FormControl, InputLabel, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, LinearProgress,
  Grid, Tooltip
} from '@mui/material';
import {
  Refresh, Visibility, CheckCircle, Search
} from '@mui/icons-material';
import { alertService } from '../../services/api/alerts';
import { Alert, AlertStatus, AlertSeverity } from '../../types';

const severityColors: Record<AlertSeverity, 'error' | 'warning' | 'info' | 'success' | 'default'> = {
  critical: 'error',
  high: 'error',
  medium: 'warning',
  low: 'info',
  info: 'default',
};

const statusColors: Record<AlertStatus, 'error' | 'warning' | 'info' | 'success' | 'default'> = {
  open: 'error',
  acknowledged: 'warning',
  investigating: 'info',
  resolved: 'success',
  closed: 'default',
  false_positive: 'default',
};

export const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [comment, setComment] = useState('');

  useEffect(() => {
    loadAlerts();
  }, [statusFilter, severityFilter]);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (statusFilter) params.status = statusFilter;
      if (severityFilter) params.severity = severityFilter;
      const response = await alertService.list(params);
      setAlerts(response.results);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (alertId: string, newStatus: AlertStatus) => {
    try {
      await alertService.updateStatus(alertId, newStatus);
      loadAlerts();
    } catch (err) {
      console.error('Failed to update alert:', err);
    }
  };

  const handleAddComment = async () => {
    if (selectedAlert && comment) {
      try {
        await alertService.addComment(selectedAlert.id, comment);
        setComment('');
        setOpenDialog(false);
        loadAlerts();
      } catch (err) {
        console.error('Failed to add comment:', err);
      }
    }
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Alerts</Typography>
          <Typography color="text.secondary">Manage security alerts</Typography>
        </Box>
        <Button startIcon={<Refresh />} onClick={loadAlerts}>Refresh</Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 4 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select value={statusFilter} label="Status" onChange={(e) => setStatusFilter(e.target.value)}>
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="open">Open</MenuItem>
                  <MenuItem value="acknowledged">Acknowledged</MenuItem>
                  <MenuItem value="investigating">Investigating</MenuItem>
                  <MenuItem value="resolved">Resolved</MenuItem>
                  <MenuItem value="closed">Closed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Severity</InputLabel>
                <Select value={severityFilter} label="Severity" onChange={(e) => setSeverityFilter(e.target.value)}>
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="low">Low</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Alerts Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Severity</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Assigned To</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {alerts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography color="text.secondary" sx={{ py: 3 }}>No alerts found</Typography>
                </TableCell>
              </TableRow>
            ) : (
              alerts.map((alert) => (
                <TableRow key={alert.id} hover>
                  <TableCell>
                    <Chip label={alert.severity} size="small" color={severityColors[alert.severity]} />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>{alert.title}</Typography>
                  </TableCell>
                  <TableCell>{alert.source}</TableCell>
                  <TableCell>
                    <Chip label={alert.status} size="small" color={statusColors[alert.status]} />
                  </TableCell>
                  <TableCell>{alert.assigned_to_name || '-'}</TableCell>
                  <TableCell>{new Date(alert.created_at).toLocaleString()}</TableCell>
                  <TableCell>
                    <Tooltip title="View Details">
                      <IconButton size="small" onClick={() => { setSelectedAlert(alert); setOpenDialog(true); }}>
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                    {alert.status === 'open' && (
                      <Tooltip title="Acknowledge">
                        <IconButton size="small" color="warning" onClick={() => handleStatusChange(alert.id, 'acknowledged')}>
                          <CheckCircle />
                        </IconButton>
                      </Tooltip>
                    )}
                    {(alert.status === 'open' || alert.status === 'acknowledged' || alert.status === 'investigating') && (
                      <Tooltip title="Resolve">
                        <IconButton size="small" color="success" onClick={() => handleStatusChange(alert.id, 'resolved')}>
                          <CheckCircle />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Alert Detail Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{selectedAlert?.title}</DialogTitle>
        <DialogContent>
          {selectedAlert && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2" sx={{ mb: 2 }}>{selectedAlert.description}</Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Chip label={`Severity: ${selectedAlert.severity}`} color={severityColors[selectedAlert.severity]} size="small" />
                <Chip label={`Status: ${selectedAlert.status}`} color={statusColors[selectedAlert.status]} size="small" />
                <Chip label={`Source: ${selectedAlert.source}`} size="small" />
              </Box>
              <TextField
                fullWidth
                multiline
                rows={2}
                placeholder="Add a comment..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Button variant="contained" onClick={handleAddComment} disabled={!comment}>
                Add Comment
              </Button>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};