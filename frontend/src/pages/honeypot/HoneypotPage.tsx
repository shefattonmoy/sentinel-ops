import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, Table,
  TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, LinearProgress, Button, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, Select, MenuItem,
  FormControl, InputLabel, IconButton,
} from '@mui/material';
import { Add, Refresh, PlayArrow, Pause, BugReport } from '@mui/icons-material';
import { apiClient } from '../../services/api/client';

export const HoneypotPage: React.FC = () => {
  const [honeypots, setHoneypots] = useState<any[]>([]);
  const [interactions, setInteractions] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [openCreate, setOpenCreate] = useState(false);
  const [newHoneypot, setNewHoneypot] = useState({ name: '', protocol: 'ssh', port: 2222, host: '0.0.0.0' });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [hpRes, intRes, statsRes] = await Promise.all([
        apiClient.get('/honeypot/honeypots/'),
        apiClient.get('/honeypot/interactions/?limit=50'),
        apiClient.get('/honeypot/stats/'),
      ]);
      setHoneypots(Array.isArray(hpRes) ? hpRes : []);
      setInteractions(Array.isArray(intRes) ? intRes : []);
      setStats(statsRes || {});
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleCreate = async () => {
    try {
      await apiClient.post('/honeypot/create/', newHoneypot);
      setOpenCreate(false);
      loadData();
    } catch (err) { console.error(err); }
  };

  const handleToggle = async (id: string) => {
    try {
      await apiClient.post('/honeypot/toggle/', { id });
      loadData();
    } catch (err) { console.error(err); }
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Honeypots</Typography>
          <Typography color="text.secondary">Deception technology & threat intelligence</Typography>
        </Box>
        <Box>
          <Button startIcon={<Refresh />} onClick={loadData} sx={{ mr: 1 }}>Refresh</Button>
          <Button variant="contained" startIcon={<Add />} onClick={() => setOpenCreate(true)}>Deploy Honeypot</Button>
        </Box>
      </Box>

      {/* Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card><CardContent sx={{ textAlign: 'center' }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>{stats.active_honeypots || 0}</Typography>
            <Typography variant="caption">Active Honeypots</Typography>
          </CardContent></Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card><CardContent sx={{ textAlign: 'center' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, color: 'error.main' }}>{stats.interactions_24h || 0}</Typography>
            <Typography variant="caption">Interactions (24h)</Typography>
          </CardContent></Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card><CardContent sx={{ textAlign: 'center' }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>{stats.unique_ips_24h || 0}</Typography>
            <Typography variant="caption">Unique Attackers</Typography>
          </CardContent></Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card><CardContent sx={{ textAlign: 'center' }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>{stats.interactions_7d || 0}</Typography>
            <Typography variant="caption">Interactions (7d)</Typography>
          </CardContent></Card>
        </Grid>
      </Grid>

      {/* Honeypots */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Deployed Honeypots</Typography>
          <Grid container spacing={2}>
            {honeypots.map((hp) => (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={hp.id}>
                <Paper variant="outlined" sx={{ p: 2, borderColor: hp.is_active ? 'success.main' : 'grey.500' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{hp.name}</Typography>
                    <Chip label={hp.is_active ? 'Active' : 'Paused'} size="small"
                      color={hp.is_active ? 'success' : 'default'} />
                  </Box>
                  <Typography variant="caption" sx={{ display: 'block' }}>Protocol: {hp.protocol.toUpperCase()}</Typography>
                  <Typography variant="caption" sx={{ display: 'block' }}>Port: {hp.port}</Typography>
                  <Typography variant="caption" sx={{ display: 'block' }}>Interactions: {hp.interaction_count || 0}</Typography>
                  <Button size="small" startIcon={hp.is_active ? <Pause /> : <PlayArrow />}
                    onClick={() => handleToggle(hp.id)} sx={{ mt: 1 }}>
                    {hp.is_active ? 'Pause' : 'Activate'}
                  </Button>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Interactions */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Recent Interactions</Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>Source IP</TableCell>
                  <TableCell>Honeypot</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Payload</TableCell>
                  <TableCell>Threat</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {interactions.map((intr) => (
                  <TableRow key={intr.id} hover>
                    <TableCell><Typography variant="caption">{new Date(intr.timestamp).toLocaleString()}</Typography></TableCell>
                    <TableCell><Chip label={intr.source_ip} size="small" variant="outlined" /></TableCell>
                    <TableCell>{intr.honeypot_name}</TableCell>
                    <TableCell>{intr.interaction_type}</TableCell>
                    <TableCell><Typography variant="caption" noWrap sx={{ maxWidth: 200 }}>{intr.payload || '-'}</Typography></TableCell>
                    <TableCell><Chip label={intr.threat_level} size="small" color="error" /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={openCreate} onClose={() => setOpenCreate(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Deploy Honeypot</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField label="Name" fullWidth value={newHoneypot.name}
              onChange={(e) => setNewHoneypot({ ...newHoneypot, name: e.target.value })} />
            <FormControl fullWidth>
              <InputLabel>Protocol</InputLabel>
              <Select value={newHoneypot.protocol} label="Protocol"
                onChange={(e) => setNewHoneypot({ ...newHoneypot, protocol: e.target.value })}>
                <MenuItem value="ssh">SSH</MenuItem>
                <MenuItem value="http">HTTP</MenuItem>
                <MenuItem value="ftp">FTP</MenuItem>
                <MenuItem value="mysql">MySQL</MenuItem>
                <MenuItem value="telnet">Telnet</MenuItem>
              </Select>
            </FormControl>
            <TextField label="Port" type="number" fullWidth value={newHoneypot.port}
              onChange={(e) => setNewHoneypot({ ...newHoneypot, port: parseInt(e.target.value) || 2222 })} />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreate(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate}>Deploy</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};