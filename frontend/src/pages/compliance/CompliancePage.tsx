import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, LinearProgress,
  Button, Chip, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Select, MenuItem, FormControl, InputLabel,
} from '@mui/material';
import { Refresh, CheckCircle, Cancel, Gavel } from '@mui/icons-material';
import { apiClient } from '../../services/api/client';

interface FrameworkData {
  id: string; name: string; total_controls: number;
  covered_controls: number; compliance_pct: number; controls: any[];
}

export const CompliancePage: React.FC = () => {
  const [frameworks, setFrameworks] = useState<FrameworkData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFramework, setSelectedFramework] = useState('SOC2');
  const [generating, setGenerating] = useState(false);

  useEffect(() => { loadFrameworks(); }, []);

  const loadFrameworks = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<FrameworkData[]>('/compliance/frameworks/');
      setFrameworks(Array.isArray(response) ? response : []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await apiClient.post('/compliance/generate-evidence/', { framework: selectedFramework });
      loadFrameworks();
    } catch (err) { console.error(err); }
    finally { setGenerating(false); }
  };

  if (loading) return <LinearProgress />;

  const framework = frameworks.find(f => f.name === selectedFramework);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Compliance</Typography>
          <Typography color="text.secondary">SOC2 & ISO27001 compliance tracking</Typography>
        </Box>
        <Box>
          <FormControl size="small" sx={{ mr: 1, minWidth: 120 }}>
            <Select value={selectedFramework} onChange={(e) => setSelectedFramework(e.target.value)}>
              <MenuItem value="SOC2">SOC2</MenuItem>
              <MenuItem value="ISO27001">ISO 27001</MenuItem>
            </Select>
          </FormControl>
          <Button variant="contained" startIcon={<Gavel />} onClick={handleGenerate} disabled={generating}>
            {generating ? 'Generating...' : 'Generate Evidence'}
          </Button>
        </Box>
      </Box>

      {/* Framework Overview */}
      {framework && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>{framework.name} Overview</Typography>
            <Grid container spacing={3}>
              <Grid size={{ xs: 4, sm: 2 }}>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>{framework.total_controls}</Typography>
                <Typography variant="caption" color="text.secondary">Total Controls</Typography>
              </Grid>
              <Grid size={{ xs: 4, sm: 2 }}>
                <Typography variant="h4" sx={{ fontWeight: 700, color: 'success.main' }}>{framework.covered_controls}</Typography>
                <Typography variant="caption" color="text.secondary">Covered</Typography>
              </Grid>
              <Grid size={{ xs: 4, sm: 2 }}>
                <Typography variant="h4" sx={{ fontWeight: 700, color: 'error.main' }}>
                  {framework.total_controls - framework.covered_controls}
                </Typography>
                <Typography variant="caption" color="text.secondary">Gaps</Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Typography variant="h4" sx={{ fontWeight: 700, color: framework.compliance_pct > 70 ? 'success.main' : 'warning.main' }}>
                  {framework.compliance_pct}%
                </Typography>
                <Typography variant="caption" color="text.secondary">Compliance Score</Typography>
                <LinearProgress variant="determinate" value={framework.compliance_pct} 
                  sx={{ mt: 1, height: 8, borderRadius: 4 }}
                  color={framework.compliance_pct > 70 ? 'success' : 'warning'} />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Controls Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Control ID</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Evidence</TableCell>
              <TableCell>Last Updated</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {framework?.controls?.map((ctrl) => (
              <TableRow key={ctrl.control_id} hover>
                <TableCell><Chip label={ctrl.control_id} size="small" variant="outlined" /></TableCell>
                <TableCell><Typography variant="body2" sx={{ fontWeight: 500 }}>{ctrl.title}</Typography></TableCell>
                <TableCell>{ctrl.category}</TableCell>
                <TableCell>
                  {ctrl.covered ? (
                    <Chip icon={<CheckCircle />} label="Compliant" size="small" color="success" />
                  ) : (
                    <Chip icon={<Cancel />} label="Non-Compliant" size="small" color="error" />
                  )}
                </TableCell>
                <TableCell>{ctrl.evidence_count}</TableCell>
                <TableCell>
                  {ctrl.last_evidence ? new Date(ctrl.last_evidence).toLocaleString() : 'Never'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};