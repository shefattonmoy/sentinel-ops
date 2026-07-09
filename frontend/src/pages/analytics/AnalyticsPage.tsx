import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, Table,
  TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, LinearProgress, Button,
} from '@mui/material';
import { Refresh, Warning, Person, Assessment } from '@mui/icons-material';
import { apiClient } from '../../services/api/client';

export const AnalyticsPage: React.FC = () => {
  const [profiles, setProfiles] = useState<any[]>([]);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [profRes, anomRes, statsRes] = await Promise.all([
        apiClient.get('/analytics/users/'),
        apiClient.get('/analytics/anomalies/?limit=50'),
        apiClient.get('/analytics/stats/'),
      ]);
      setProfiles(Array.isArray(profRes) ? profRes : []);
      setAnomalies(Array.isArray(anomRes) ? anomRes : []);
      setStats(statsRes || {});
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleAnalyze = async () => {
    try {
      await apiClient.post('/analytics/analyze/');
      loadData();
    } catch (err) { console.error(err); }
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>User Analytics</Typography>
          <Typography color="text.secondary">Behavior analysis & anomaly detection</Typography>
        </Box>
        <Box>
          <Button startIcon={<Refresh />} onClick={loadData} sx={{ mr: 1 }}>Refresh</Button>
          <Button variant="contained" startIcon={<Assessment />} onClick={handleAnalyze}>Run Analysis</Button>
        </Box>
      </Box>

      {/* Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card><CardContent sx={{ textAlign: 'center' }}>
            <Person sx={{ fontSize: 36, color: 'primary.main', mb: 1 }} />
            <Typography variant="h5" sx={{ fontWeight: 700 }}>{stats.total_profiles || 0}</Typography>
            <Typography variant="caption">Users Analyzed</Typography>
          </CardContent></Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card><CardContent sx={{ textAlign: 'center' }}>
            <Warning sx={{ fontSize: 36, color: 'error.main', mb: 1 }} />
            <Typography variant="h5" sx={{ fontWeight: 700, color: 'error.main' }}>{stats.high_risk_users || 0}</Typography>
            <Typography variant="caption">High Risk Users</Typography>
          </CardContent></Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card><CardContent sx={{ textAlign: 'center' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, color: 'warning.main' }}>{stats.total_anomalies || 0}</Typography>
            <Typography variant="caption">Total Anomalies</Typography>
          </CardContent></Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card><CardContent sx={{ textAlign: 'center' }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>{stats.recent_anomalies_24h || 0}</Typography>
            <Typography variant="caption">Anomalies (24h)</Typography>
          </CardContent></Card>
        </Grid>
      </Grid>

      {/* User Profiles */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>User Risk Profiles</Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Risk Level</TableCell>
                  <TableCell>Anomaly Score</TableCell>
                  <TableCell>Sudo Frequency</TableCell>
                  <TableCell>Events Analyzed</TableCell>
                  <TableCell>Common IPs</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {profiles.map((p, i) => (
                  <TableRow key={i} hover>
                    <TableCell><Typography variant="body2" sx={{ fontWeight: 500 }}>{p.user}</Typography></TableCell>
                    <TableCell>
                      <Chip label={p.risk_level} size="small"
                        color={p.risk_level === 'high' ? 'error' : p.risk_level === 'medium' ? 'warning' : 'success'} />
                    </TableCell>
                    <TableCell>{p.anomaly_score}</TableCell>
                    <TableCell>{p.sudo_frequency}</TableCell>
                    <TableCell>{p.total_events}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        {p.common_ips?.slice(0, 3).map((ip: string, j: number) => (
                          <Chip key={j} label={ip} size="small" variant="outlined" sx={{ fontSize: '0.65rem' }} />
                        ))}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Anomalies */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Detected Anomalies</Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Severity</TableCell>
                  <TableCell>Confidence</TableCell>
                  <TableCell>Detected</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {anomalies.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Typography color="text.secondary" sx={{ py: 2 }}>No anomalies detected</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  anomalies.map((a) => (
                    <TableRow key={a.id} hover>
                      <TableCell>{a.user}</TableCell>
                      <TableCell><Chip label={a.type?.replace(/_/g, ' ')} size="small" variant="outlined" /></TableCell>
                      <TableCell><Typography variant="body2">{a.description}</Typography></TableCell>
                      <TableCell><Chip label={a.severity} size="small" color={a.severity === 'critical' ? 'error' : 'warning'} /></TableCell>
                      <TableCell>{Math.round(a.confidence * 100)}%</TableCell>
                      <TableCell>{new Date(a.detected_at).toLocaleString()}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};