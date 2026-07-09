import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, Table,
  TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, LinearProgress, TextField, Button, IconButton,
  Dialog, DialogTitle, DialogContent, DialogActions,
} from '@mui/material';
import { Search, Shield, Warning, Refresh } from '@mui/icons-material';
import { apiClient } from '../../services/api/client';

export const ThreatIntelPage: React.FC = () => {
  const [threats, setThreats] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ipInput, setIpInput] = useState('');
  const [scoreResult, setScoreResult] = useState<any>(null);
  const [openDialog, setOpenDialog] = useState(false);

  useEffect(() => { loadThreats(); }, []);

  const loadThreats = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/threat-intel/top-threats/?limit=20') as any[];
      setThreats(response || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const scoreIP = async () => {
    try {
      const response = await apiClient.post('/threat-intel/score-ip/', { ip: ipInput });
      setScoreResult(response);
      setOpenDialog(true);
    } catch (err) { console.error(err); }
  };

  const getColor = (level: string) => {
    switch (level) {
      case 'critical': return 'error';
      case 'high': return 'error';
      case 'medium': return 'warning';
      default: return 'success';
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Threat Intelligence</Typography>
          <Typography color="text.secondary">AI-powered threat scoring and IP reputation</Typography>
        </Box>
        <IconButton onClick={loadThreats}><Refresh /></IconButton>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Check IP Reputation</Typography>
          <Grid container spacing={2} sx={{ alignItems: 'center' }}>
            <Grid size={{ xs: 12, sm: 8 }}>
              <TextField fullWidth size="small" placeholder="Enter IP address..." value={ipInput}
                onChange={(e) => setIpInput(e.target.value)} />
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Button variant="contained" startIcon={<Search />} onClick={scoreIP} fullWidth>
                Score IP
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {loading ? <LinearProgress /> : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Source IP</TableCell>
                <TableCell>Threat Score</TableCell>
                <TableCell>Risk Level</TableCell>
                <TableCell>Events</TableCell>
                <TableCell>Frequency</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>Pattern</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {threats.map((threat, i) => (
                <TableRow key={i} hover>
                  <TableCell><Typography variant="body2" sx={{ fontWeight: 500, fontFamily: 'monospace' }}>{threat.source_ip}</Typography></TableCell>
                  <TableCell><Typography variant="body2" sx={{ fontWeight: 700 }}>{threat.threat_score}</Typography></TableCell>
                  <TableCell><Chip label={threat.risk_level} size="small" color={getColor(threat.risk_level)} /></TableCell>
                  <TableCell>{threat.total_events}</TableCell>
                  <TableCell>{threat.frequency_score}</TableCell>
                  <TableCell>{threat.severity_score}</TableCell>
                  <TableCell>{threat.pattern_score}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>IP Score Result</DialogTitle>
        <DialogContent>
          {scoreResult && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="h3" sx={{ fontWeight: 700, textAlign: 'center', color: scoreResult.threat_score > 70 ? 'error.main' : scoreResult.threat_score > 40 ? 'warning.main' : 'success.main' }}>
                {scoreResult.threat_score}
              </Typography>
              <Typography align="center" color="text.secondary">Threat Score</Typography>
              <Grid container spacing={2} sx={{ mt: 2 }}>
                <Grid size={{ xs: 6 }}><Typography variant="body2" color="text.secondary">Risk Level</Typography><Chip label={scoreResult.risk_level} color={getColor(scoreResult.risk_level)} size="small" /></Grid>
                <Grid size={{ xs: 6 }}><Typography variant="body2" color="text.secondary">Total Events</Typography><Typography>{scoreResult.total_events}</Typography></Grid>
                <Grid size={{ xs: 6 }}><Typography variant="body2" color="text.secondary">Frequency Score</Typography><Typography>{scoreResult.frequency_score}</Typography></Grid>
                <Grid size={{ xs: 6 }}><Typography variant="body2" color="text.secondary">Severity Score</Typography><Typography>{scoreResult.severity_score}</Typography></Grid>
                <Grid size={{ xs: 6 }}><Typography variant="body2" color="text.secondary">Pattern Score</Typography><Typography>{scoreResult.pattern_score}</Typography></Grid>
                <Grid size={{ xs: 6 }}><Typography variant="body2" color="text.secondary">Reputation Score</Typography><Typography>{scoreResult.reputation_score}</Typography></Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions><Button onClick={() => setOpenDialog(false)}>Close</Button></DialogActions>
      </Dialog>
    </Box>
  );
};