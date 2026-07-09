import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, Table,
  TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, LinearProgress, Button, IconButton, Tooltip,
  Tabs, Tab,
} from '@mui/material';
import { Refresh, Security, CheckCircle, Cancel } from '@mui/icons-material';
import { apiClient } from '../../services/api/client';

interface MitreTechnique {
  technique_id: string; name: string; tactic: string; platform: string;
  is_covered: boolean; detected_events: number; last_detected: string | null;
}

interface TacticStats {
  total: number; covered: number; percentage: number; techniques: any[];
}

export const MitrePage: React.FC = () => {
  const [techniques, setTechniques] = useState<MitreTechnique[]>([]);
  const [matrix, setMatrix] = useState<Record<string, TacticStats>>({});
  const [stats, setStats] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [techRes, matrixRes, statsRes] = await Promise.all([
        apiClient.get<MitreTechnique[]>('/mitre/techniques/'),
        apiClient.get<Record<string, TacticStats>>('/mitre/matrix/'),
        apiClient.get<any>('/mitre/stats/'),
      ]);
      setTechniques(Array.isArray(techRes) ? techRes : []);
      setMatrix(matrixRes || {});
      setStats(statsRes || {});
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const getTacticColor = (tactic: string) => {
    const colors: Record<string, string> = {
      'Reconnaissance': '#3b82f6', 'Resource Development': '#6366f1',
      'Initial Access': '#ef4444', 'Execution': '#f97316',
      'Persistence': '#eab308', 'Privilege Escalation': '#f59e0b',
      'Defense Evasion': '#84cc16', 'Credential Access': '#ef4444',
      'Discovery': '#06b6d4', 'Lateral Movement': '#8b5cf6',
      'Collection': '#ec4899', 'Command and Control': '#f43f5e',
      'Exfiltration': '#dc2626', 'Impact': '#991b1b',
    };
    return colors[tactic] || '#6b7280';
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>MITRE Attack</Typography>
          <Typography color="text.secondary">Framework coverage mapping</Typography>
        </Box>
        <Button startIcon={<Refresh />} onClick={loadData}>Refresh</Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Security sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 700 }}>{stats.total_techniques || 0}</Typography>
              <Typography color="text.secondary">Total Techniques</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <CheckCircle sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 700 }}>{stats.covered_techniques || 0}</Typography>
              <Typography color="text.secondary">Covered</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 700, color: stats.coverage_pct > 50 ? 'success.main' : 'warning.main' }}>
                {stats.coverage_pct || 0}%
              </Typography>
              <Typography color="text.secondary">Coverage</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 2 }}>
        <Tab label="Matrix View" />
        <Tab label="Techniques List" />
      </Tabs>

      {/* Matrix View */}
      {tabValue === 0 && (
        <Grid container spacing={2}>
          {Object.entries(matrix).map(([tactic, data]) => (
            <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={tactic}>
              <Card sx={{ borderTop: `3px solid ${getTacticColor(tactic)}` }}>
                <CardContent>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: getTacticColor(tactic) }}>
                    {tactic}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                    <Chip label={`${data.covered}/${data.total}`} size="small" color={data.percentage > 50 ? 'success' : 'warning'} />
                    <Chip label={`${data.percentage}%`} size="small" variant="outlined" />
                  </Box>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {data.techniques?.slice(0, 8).map((t: any) => (
                      <Tooltip key={t.id} title={t.name}>
                        <Box sx={{
                          width: 12, height: 12, borderRadius: 0.5,
                          bgcolor: t.covered ? 'success.main' : 'action.disabled',
                          border: '1px solid', borderColor: 'divider',
                        }} />
                      </Tooltip>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Techniques List */}
      {tabValue === 1 && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Tactic</TableCell>
                <TableCell>Platform</TableCell>
                <TableCell>Covered</TableCell>
                <TableCell>Events</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {techniques.slice(0, 100).map((tech) => (
                <TableRow key={tech.technique_id} hover>
                  <TableCell>
                    <Chip label={tech.technique_id} size="small" color="primary" variant="outlined" />
                  </TableCell>
                  <TableCell><Typography variant="body2" sx={{ fontWeight: 500 }}>{tech.name}</Typography></TableCell>
                  <TableCell>
                    <Chip label={tech.tactic} size="small" sx={{ bgcolor: getTacticColor(tech.tactic), color: 'white' }} />
                  </TableCell>
                  <TableCell><Typography variant="caption">{tech.platform}</Typography></TableCell>
                  <TableCell>
                    {tech.is_covered ? <CheckCircle color="success" fontSize="small" /> : <Cancel color="disabled" fontSize="small" />}
                  </TableCell>
                  <TableCell>{tech.detected_events}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};