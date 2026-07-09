// src/pages/reports/ReportsPage.tsx
import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Button, Grid,
  Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, Paper, Chip, LinearProgress, Select, MenuItem,
  FormControl, InputLabel, Dialog, DialogTitle, DialogContent,
  DialogActions,
} from '@mui/material';
import { Download, Description, Assessment } from '@mui/icons-material';
import { apiClient } from '../../services/api/client';

const API_BASE = 'http://127.0.0.1:8000/api';

const reportTypes = [
  { value: 'daily_soc', label: 'Daily SOC Report' },
  { value: 'weekly', label: 'Weekly Report' },
  { value: 'monthly', label: 'Monthly Report' },
  { value: 'executive', label: 'Executive Summary' },
];

export const ReportsPage: React.FC = () => {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [reportType, setReportType] = useState('daily_soc');
  const [generating, setGenerating] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [openPreview, setOpenPreview] = useState(false);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<any[]>('/reports/list/');
      setReports(Array.isArray(response) ? response : []);
    } catch (err) {
      console.error('Failed to load reports:', err);
      setReports([]);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setGenerating(true);
    try {
      const response = await apiClient.post('/reports/generate/', {
        report_type: reportType,
      });
      setPreviewData(response);
      setOpenPreview(true);
      loadReports();
    } catch (err) {
      console.error('Failed to generate report:', err);
    } finally {
      setGenerating(false);
    }
  };

  const downloadReport = (reportId: string, format: string) => {
    const url = `${API_BASE}/reports/${reportId}/${format}/`;
    window.open(url, '_blank');
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Reports</Typography>
          <Typography color="text.secondary">Generate and download security reports</Typography>
        </Box>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Generate New Report</Typography>
          <Grid container spacing={2} sx={{ alignItems: 'center' }}>
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Report Type</InputLabel>
                <Select value={reportType} label="Report Type" onChange={(e) => setReportType(e.target.value)}>
                  {reportTypes.map((rt) => (
                    <MenuItem key={rt.value} value={rt.value}>{rt.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <Button variant="contained" startIcon={<Assessment />} onClick={generateReport} disabled={generating} fullWidth>
                {generating ? 'Generating...' : 'Generate Report'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Generated Reports</Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Generated At</TableCell>
                  <TableCell>Download</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {reports.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      <Typography color="text.secondary" sx={{ py: 2 }}>No reports generated yet</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  reports.map((report) => (
                    <TableRow key={report.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Description fontSize="small" color="primary" />
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>{report.name}</Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip label={report.report_type?.replace(/_/g, ' ')} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        <Chip label={report.status || 'completed'} size="small" color="success" />
                      </TableCell>
                      <TableCell>{new Date(report.generated_at || report.created_at).toLocaleString()}</TableCell>
                      <TableCell>
                        <Button size="small" onClick={() => downloadReport(report.id, 'json')}>JSON</Button>
                        <Button size="small" onClick={() => downloadReport(report.id, 'csv')}>CSV</Button>
                        <Button size="small" onClick={() => downloadReport(report.id, 'pdf')}>PDF</Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <Dialog open={openPreview} onClose={() => setOpenPreview(false)} maxWidth="lg" fullWidth>
        <DialogTitle>Report Generated</DialogTitle>
        <DialogContent>
          {previewData && (
            <Box>
              <Typography variant="h6" gutterBottom>{previewData.name}</Typography>
              <Box sx={{ mt: 1, maxHeight: 500, overflow: 'auto', bgcolor: 'background.default', p: 2, borderRadius: 1 }}>
                <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', margin: 0 }}>
                  {JSON.stringify(previewData.data, null, 2)}
                </pre>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPreview(false)}>Close</Button>
          <Button variant="contained" onClick={() => previewData && downloadReport(previewData.id, 'pdf')}>Download PDF</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};