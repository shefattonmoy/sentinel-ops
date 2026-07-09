import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, Table,
  TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, LinearProgress, Button, IconButton, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, Select,
  MenuItem, FormControl, InputLabel, Tooltip, Alert,
} from '@mui/material';
import {
  Add, Refresh, PlayArrow, Delete, Visibility,
  Stop as StopIcon,
} from '@mui/icons-material';
import { apiClient } from '../../services/api/client';

interface Playbook {
  id: string;
  name: string;
  description: string;
  trigger_type: string;
  is_active: boolean;
  times_executed: number;
  last_executed: string | null;
  actions: any[];
  created_at: string;
}

export const PlaybooksPage: React.FC = () => {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [loading, setLoading] = useState(true);
  const [openCreate, setOpenCreate] = useState(false);
  const [openExecute, setOpenExecute] = useState(false);
  const [selectedPlaybook, setSelectedPlaybook] = useState<Playbook | null>(null);
  const [executeResult, setExecuteResult] = useState<any>(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const [newPlaybook, setNewPlaybook] = useState({
    name: '', description: '', trigger_type: 'alert',
    trigger_conditions: { event_type: '', threshold: 1, timeframe_minutes: 5 },
    actions: [{ type: 'create_alert', config: { title: '', severity: 'high' } }],
  });

  useEffect(() => { loadPlaybooks(); }, []);

  const loadPlaybooks = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<{ results: Playbook[] }>('/playbooks/');
      setPlaybooks(response.results || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleCreate = async () => {
    setError('');
    try {
      await apiClient.post('/playbooks/', newPlaybook);
      setOpenCreate(false);
      setNewPlaybook({
        name: '', description: '', trigger_type: 'alert',
        trigger_conditions: { event_type: '', threshold: 1, timeframe_minutes: 5 },
        actions: [{ type: 'create_alert', config: { title: '', severity: 'high' } }],
      });
      setMessage('Playbook created successfully');
      loadPlaybooks();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create playbook');
    }
  };

  const handleExecute = async () => {
    if (!selectedPlaybook) return;
    setError('');
    try {
      const response = await apiClient.post(`/playbooks/${selectedPlaybook.id}/execute/`);
      setExecuteResult(response);
      setOpenExecute(true);
      loadPlaybooks();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to execute playbook');
    }
  };

  const handleToggle = async (playbook: Playbook) => {
    try {
      await apiClient.patch(`/playbooks/${playbook.id}/`, { is_active: !playbook.is_active });
      loadPlaybooks();
    } catch (err) { console.error(err); }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Delete this playbook?')) {
      try {
        await apiClient.delete(`/playbooks/${id}/`);
        loadPlaybooks();
      } catch (err) { console.error(err); }
    }
  };

  const applyTemplate = (template: any) => {
    setNewPlaybook({
      name: template.name,
      description: template.description,
      trigger_type: template.trigger_type,
      trigger_conditions: template.trigger_conditions,
      actions: template.actions,
    });
    setOpenCreate(true);
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Playbooks</Typography>
          <Typography color="text.secondary">Automated response workflows</Typography>
        </Box>
        <Box>
          <Button startIcon={<Refresh />} onClick={loadPlaybooks} sx={{ mr: 1 }}>Refresh</Button>
          <Button variant="contained" startIcon={<Add />} onClick={() => setOpenCreate(true)}>Create Playbook</Button>
        </Box>
      </Box>

      {message && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMessage('')}>{message}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      {/* Templates */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Quick Templates</Typography>
          <Grid container spacing={1}>
            {[
              { name: 'Brute Force Response', desc: 'Auto-block IP on brute force', trigger: 'alert' },
              { name: 'Container Failure Response', desc: 'Create incident on container crash', trigger: 'threshold' },
              { name: 'Suspicious Activity Alert', desc: 'Alert on sudo commands', trigger: 'alert' },
            ].map((tpl, i) => (
              <Grid size={{ xs: 12, sm: 4 }} key={i}>
                <Paper variant="outlined" sx={{ p: 2, cursor: 'pointer', '&:hover': { borderColor: 'primary.main' } }}
                  onClick={() => applyTemplate({
                    name: tpl.name, description: tpl.desc, trigger_type: tpl.trigger,
                    trigger_conditions: { event_type: '', threshold: 3, timeframe_minutes: 5 },
                    actions: [{ type: 'create_alert', config: { title: tpl.name, severity: 'high' } }],
                  })}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>{tpl.name}</Typography>
                  <Typography variant="caption" color="text.secondary">{tpl.desc}</Typography>
                  <Chip label={tpl.trigger} size="small" sx={{ mt: 0.5 }} />
                </Paper>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Playbooks Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Trigger</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Executions</TableCell>
              <TableCell>Last Executed</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {playbooks.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="text.secondary" sx={{ py: 3 }}>No playbooks created yet</Typography>
                </TableCell>
              </TableRow>
            ) : (
              playbooks.map((pb) => (
                <TableRow key={pb.id} hover>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>{pb.name}</Typography>
                  </TableCell>
                  <TableCell><Chip label={pb.trigger_type} size="small" variant="outlined" /></TableCell>
                  <TableCell>
                    <Chip label={pb.is_active ? 'Active' : 'Paused'} size="small"
                      color={pb.is_active ? 'success' : 'default'} />
                  </TableCell>
                  <TableCell>{pb.times_executed}</TableCell>
                  <TableCell>{pb.last_executed ? new Date(pb.last_executed).toLocaleString() : 'Never'}</TableCell>
                  <TableCell>
                    <Tooltip title="Execute Now">
                      <IconButton size="small" color="primary" onClick={() => { setSelectedPlaybook(pb); handleExecute(); }}>
                        <PlayArrow />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={pb.is_active ? 'Pause' : 'Activate'}>
                      <IconButton size="small" onClick={() => handleToggle(pb)}>
                        <StopIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton size="small" color="error" onClick={() => handleDelete(pb.id)}>
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

      {/* Create Playbook Dialog */}
      <Dialog open={openCreate} onClose={() => setOpenCreate(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Playbook</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Name" fullWidth value={newPlaybook.name}
                  onChange={(e) => setNewPlaybook({ ...newPlaybook, name: e.target.value })} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Trigger Type</InputLabel>
                  <Select value={newPlaybook.trigger_type} label="Trigger Type"
                    onChange={(e) => setNewPlaybook({ ...newPlaybook, trigger_type: e.target.value })}>
                    <MenuItem value="alert">On Alert</MenuItem>
                    <MenuItem value="threshold">On Threshold</MenuItem>
                    <MenuItem value="schedule">On Schedule</MenuItem>
                    <MenuItem value="manual">Manual Only</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField label="Description" fullWidth multiline rows={2} value={newPlaybook.description}
                  onChange={(e) => setNewPlaybook({ ...newPlaybook, description: e.target.value })} />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <TextField label="Event Type" fullWidth value={newPlaybook.trigger_conditions.event_type}
                  onChange={(e) => setNewPlaybook({
                    ...newPlaybook,
                    trigger_conditions: { ...newPlaybook.trigger_conditions, event_type: e.target.value }
                  })} placeholder="FAILED_LOGIN" />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <TextField label="Threshold" type="number" fullWidth value={newPlaybook.trigger_conditions.threshold}
                  onChange={(e) => setNewPlaybook({
                    ...newPlaybook,
                    trigger_conditions: { ...newPlaybook.trigger_conditions, threshold: parseInt(e.target.value) || 1 }
                  })} />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <TextField label="Timeframe (min)" type="number" fullWidth value={newPlaybook.trigger_conditions.timeframe_minutes}
                  onChange={(e) => setNewPlaybook({
                    ...newPlaybook,
                    trigger_conditions: { ...newPlaybook.trigger_conditions, timeframe_minutes: parseInt(e.target.value) || 5 }
                  })} />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Action</Typography>
                <FormControl fullWidth size="small">
                  <Select value={newPlaybook.actions[0]?.type || 'create_alert'}
                    onChange={(e) => setNewPlaybook({
                      ...newPlaybook,
                      actions: [{ type: e.target.value, config: { title: '', severity: 'high' } }]
                    })}>
                    <MenuItem value="create_alert">Create Alert</MenuItem>
                    <MenuItem value="create_incident">Create Incident</MenuItem>
                    <MenuItem value="block_ip">Block IP</MenuItem>
                    <MenuItem value="send_notification">Send Notification</MenuItem>
                    <MenuItem value="webhook">Call Webhook</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreate(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={!newPlaybook.name}>Create</Button>
        </DialogActions>
      </Dialog>

      {/* Execute Result Dialog */}
      <Dialog open={openExecute} onClose={() => setOpenExecute(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Execution Result</DialogTitle>
        <DialogContent>
          {executeResult && (
            <Box>
              <Chip label={executeResult.status} color={executeResult.status === 'completed' ? 'success' : 'error'} sx={{ mb: 2 }} />
              {executeResult.results?.map((r: any, i: number) => (
                <Box key={i} sx={{ p: 1, mb: 1, borderRadius: 1, bgcolor: r.success ? 'success.dark' : 'error.dark', opacity: 0.8 }}>
                  <Typography variant="body2">Step {r.step}: {r.action}</Typography>
                  <Typography variant="caption">{r.message}</Typography>
                </Box>
              ))}
            </Box>
          )}
        </DialogContent>
        <DialogActions><Button onClick={() => setOpenExecute(false)}>Close</Button></DialogActions>
      </Dialog>
    </Box>
  );
};