import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, Table,
  TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, LinearProgress, Button,
} from '@mui/material';
import { Refresh, Warning, Shield } from '@mui/icons-material';
import { apiClient } from '../../services/api/client';

interface AssetRisk {
  asset_name: string; hostname: string; asset_type: string;
  overall_risk: number; threat_risk: number; vulnerability_risk: number;
  exposure_risk: number; impact_risk: number;
  recent_attacks: number; critical_events: number; open_alerts: number;
}

export const RiskPage: React.FC = () => {
  const [assets, setAssets] = useState<AssetRisk[]>([]);
  const [dashboard, setDashboard] = useState<any>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [assetRes, dashRes] = await Promise.all([
        apiClient.get<AssetRisk[]>('/risks/assets/'),
        apiClient.get<any>('/risks/dashboard/'),
      ]);
      setAssets(Array.isArray(assetRes) ? assetRes : []);
      setDashboard(dashRes || {});
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const getRiskColor = (score: number) => {
    if (score >= 70) return 'error';
    if (score >= 40) return 'warning';
    return 'success';
  };

  const getRiskLevel = (score: number) => {
    if (score >= 70) return 'High';
    if (score >= 40) return 'Medium';
    return 'Low';
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Risk Scoring</Typography>
          <Typography color="text.secondary">Asset risk assessment dashboard</Typography>
        </Box>
        <Button startIcon={<Refresh />} onClick={loadData}>Refresh</Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Shield sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 700 }}>{dashboard.total_assets || 0}</Typography>
              <Typography color="text.secondary">Total Assets</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Warning sx={{ fontSize: 40, color: 'error.main', mb: 1 }} />
              <Typography variant="h4" sx={{ fontWeight: 700, color: 'error.main' }}>{dashboard.high_risk || 0}</Typography>
              <Typography color="text.secondary">High Risk</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 700, color: 'warning.main' }}>{dashboard.medium_risk || 0}</Typography>
              <Typography color="text.secondary">Medium Risk</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 700, color: 'success.main' }}>{dashboard.low_risk || 0}</Typography>
              <Typography color="text.secondary">Low Risk</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Risk Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Asset</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Overall Risk</TableCell>
              <TableCell>Threat</TableCell>
              <TableCell>Vulnerability</TableCell>
              <TableCell>Exposure</TableCell>
              <TableCell>Impact</TableCell>
              <TableCell>Open Alerts</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {assets.map((asset, i) => (
              <TableRow key={i} hover>
                <TableCell>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>{asset.asset_name}</Typography>
                  <Typography variant="caption" color="text.secondary">{asset.hostname}</Typography>
                </TableCell>
                <TableCell><Chip label={asset.asset_type} size="small" variant="outlined" /></TableCell>
                <TableCell>
                  <Chip label={`${asset.overall_risk} - ${getRiskLevel(asset.overall_risk)}`}
                    size="small" color={getRiskColor(asset.overall_risk)} />
                </TableCell>
                <TableCell>{asset.threat_risk}</TableCell>
                <TableCell>{asset.vulnerability_risk}</TableCell>
                <TableCell>{asset.exposure_risk}</TableCell>
                <TableCell>{asset.impact_risk}</TableCell>
                <TableCell>{asset.open_alerts}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};