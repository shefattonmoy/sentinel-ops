import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, Table,
  TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, LinearProgress, Button, IconButton, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, Select,
  MenuItem, FormControl, InputLabel, Tooltip, Alert,
} from '@mui/material';
import {
  Add, Refresh, PlayArrow, Delete, Pause, Schedule,
} from '@mui/icons-material';
import { apiClient } from '../../services/api/client';

interface ExportSchedule {
  id: string;
  name: string;
  export_type: string;
  format: string;
  frequency: string;
  destination: string;
  is_active: boolean;
  last_run: string | null;
  next_run: string | null;
  created_at: string;
}

export const SchedulerPage: React.FC = () => {
  const [schedules, setSchedules] = useState<ExportSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [openCreate, setOpenCreate] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const [newSchedule, setNewSchedule] = useState<{
    name: string;
    export_type: string;
    format: string;
    frequency: string;
    destination: string;
    destination_config: {
      emails?: string[];
      url?: string;
    };
    filters: Record<string, any>;
  }>({
    name: '', export_type: 'events', format: 'csv',
    frequency: 'daily', destination: 'email',
    destination_config: { emails: [''] },
    filters: {},
  });

  useEffect(() => { loadSchedules(); }, []);

  const loadSchedules = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<{ results: ExportSchedule[] }>('/scheduler/');
      setSchedules(response.results || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleCreate = async () => {
    setError('');
    try {
      await apiClient.post('/scheduler/', newSchedule);
      setOpenCreate(false);
      setNewSchedule({
        name: '', export_type: 'events', format: 'csv',
        frequency: 'daily', destination: 'email',
        destination_config: { emails: [''] },
        filters: {},
      });
      setMessage('Schedule created successfully');
      loadSchedules();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create schedule');
    }
  };

  const handleRunNow = async (id: string) => {
    try {
      await apiClient.post(`/scheduler/${id}/run_now/`);
      setMessage('Export executed successfully');
      loadSchedules();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to run export');
    }
  };

  const handleToggle = async (schedule: ExportSchedule) => {
    try {
      await apiClient.post(`/scheduler/${schedule.id}/toggle/`);
      loadSchedules();
    } catch (err) { console.error(err); }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Delete this schedule?')) {
      try {
        await apiClient.delete(`/scheduler/${id}/`);
        loadSchedules();
      } catch (err) { console.error(err); }
    }
  };

  const getFrequencyColor = (freq: string) => {
    switch (freq) {
      case 'hourly': return 'error';
      case 'daily': return 'warning';
      case 'weekly': return 'info';
      case 'monthly': return 'success';
      default: return 'default';
    }
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Export Scheduler</Typography>
          <Typography color="text.secondary">Schedule automated data exports</Typography>
        </Box>
        <Box>
          <Button startIcon={<Refresh />} onClick={loadSchedules} sx={{ mr: 1 }}>Refresh</Button>
          <Button variant="contained" startIcon={<Add />} onClick={() => setOpenCreate(true)}>Create Schedule</Button>
        </Box>
      </Box>

      {message && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMessage('')}>{message}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Schedule sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 700 }}>{schedules.length}</Typography>
              <Typography color="text.secondary">Total Schedules</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <PlayArrow sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {schedules.filter(s => s.is_active).length}
              </Typography>
              <Typography color="text.secondary">Active</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Pause sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {schedules.filter(s => !s.is_active).length}
              </Typography>
              <Typography color="text.secondary">Paused</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Schedules Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Export Type</TableCell>
              <TableCell>Format</TableCell>
              <TableCell>Frequency</TableCell>
              <TableCell>Destination</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Next Run</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {schedules.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography color="text.secondary" sx={{ py: 3 }}>No schedules created yet</Typography>
                </TableCell>
              </TableRow>
            ) : (
              schedules.map((s) => (
                <TableRow key={s.id} hover>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>{s.name}</Typography>
                  </TableCell>
                  <TableCell><Chip label={s.export_type} size="small" variant="outlined" /></TableCell>
                  <TableCell><Chip label={s.format.toUpperCase()} size="small" /></TableCell>
                  <TableCell>
                    <Chip label={s.frequency} size="small" color={getFrequencyColor(s.frequency) as any} />
                  </TableCell>
                  <TableCell><Chip label={s.destination} size="small" variant="outlined" /></TableCell>
                  <TableCell>
                    <Chip label={s.is_active ? 'Active' : 'Paused'} size="small"
                      color={s.is_active ? 'success' : 'default'} />
                  </TableCell>
                  <TableCell>
                    {s.next_run ? new Date(s.next_run).toLocaleString() : '-'}
                  </TableCell>
                  <TableCell>
                    <Tooltip title="Run Now">
                      <IconButton size="small" color="primary" onClick={() => handleRunNow(s.id)}>
                        <PlayArrow />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={s.is_active ? 'Pause' : 'Activate'}>
                      <IconButton size="small" onClick={() => handleToggle(s)}>
                        <Pause />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton size="small" color="error" onClick={() => handleDelete(s.id)}>
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Schedule Dialog */}
      <Dialog open={openCreate} onClose={() => setOpenCreate(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Export Schedule</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Schedule Name" fullWidth value={newSchedule.name}
                  onChange={(e) => setNewSchedule({ ...newSchedule, name: e.target.value })} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Export Type</InputLabel>
                  <Select value={newSchedule.export_type} label="Export Type"
                    onChange={(e) => setNewSchedule({ ...newSchedule, export_type: e.target.value })}>
                    <MenuItem value="events">Events</MenuItem>
                    <MenuItem value="alerts">Alerts</MenuItem>
                    <MenuItem value="incidents">Incidents</MenuItem>
                    <MenuItem value="report">Report</MenuItem>
                    <MenuItem value="audit">Audit Log</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <FormControl fullWidth>
                  <InputLabel>Format</InputLabel>
                  <Select value={newSchedule.format} label="Format"
                    onChange={(e) => setNewSchedule({ ...newSchedule, format: e.target.value })}>
                    <MenuItem value="csv">CSV</MenuItem>
                    <MenuItem value="json">JSON</MenuItem>
                    <MenuItem value="pdf">PDF</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <FormControl fullWidth>
                  <InputLabel>Frequency</InputLabel>
                  <Select value={newSchedule.frequency} label="Frequency"
                    onChange={(e) => setNewSchedule({ ...newSchedule, frequency: e.target.value })}>
                    <MenuItem value="hourly">Every Hour</MenuItem>
                    <MenuItem value="daily">Daily</MenuItem>
                    <MenuItem value="weekly">Weekly</MenuItem>
                    <MenuItem value="monthly">Monthly</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <FormControl fullWidth>
                  <InputLabel>Destination</InputLabel>
                  <Select value={newSchedule.destination} label="Destination"
                    onChange={(e) => setNewSchedule({ ...newSchedule, destination: e.target.value })}>
                    <MenuItem value="email">Email</MenuItem>
                    <MenuItem value="webhook">Webhook</MenuItem>
                    <MenuItem value="local">Local Storage</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              {newSchedule.destination === 'email' && (
                <Grid size={{ xs: 12 }}>
                  <TextField label="Email Addresses (comma separated)" fullWidth
                    value={newSchedule.destination_config.emails?.join(', ')}
                    onChange={(e) => setNewSchedule({
                      ...newSchedule,
                      destination_config: { emails: e.target.value.split(',').map(s => s.trim()) }
                    })} />
                </Grid>
              )}
              {newSchedule.destination === 'webhook' && (
                <Grid size={{ xs: 12 }}>
                  <TextField label="Webhook URL" fullWidth
                    value={newSchedule.destination_config.url || ''}
                    onChange={(e) => setNewSchedule({
                      ...newSchedule,
                      destination_config: { url: e.target.value }
                    })} />
                </Grid>
              )}
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreate(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={!newSchedule.name}>Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};