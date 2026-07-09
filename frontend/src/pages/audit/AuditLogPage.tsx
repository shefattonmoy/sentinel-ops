// src/pages/audit/AuditLogPage.tsx
import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip, TextField,
  FormControl, InputLabel, Select, MenuItem, LinearProgress,
  Grid, TablePagination, IconButton, Tooltip,
} from '@mui/material';
import { Refresh, Search, FilterList } from '@mui/icons-material';
import { apiClient } from '../../services/api/client';

interface AuditEntry {
  id: string;
  user: string | null;
  username: string;
  action: string;
  severity: string;
  description: string;
  object_repr: string;
  ip_address: string | null;
  timestamp: string;
}

const actionColors: Record<string, 'error' | 'warning' | 'info' | 'success' | 'default'> = {
  CREATE: 'success',
  UPDATE: 'info',
  DELETE: 'error',
  LOGIN: 'success',
  LOGOUT: 'default',
  LOGIN_FAILED: 'error',
  EXPORT: 'info',
  VIEW: 'default',
  CONFIG_CHANGE: 'warning',
  PERMISSION_CHANGE: 'warning',
  STATUS_CHANGE: 'info',
  PASSWORD_CHANGE: 'warning',
  AGENT_REGISTER: 'success',
  AGENT_DELETE: 'error',
  RULE_EXECUTE: 'info',
  ALERT_CREATE: 'error',
  INCIDENT_CREATE: 'warning',
  REPORT_GENERATE: 'info',
};

export const AuditLogPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [totalCount, setTotalCount] = useState(0);
  const [actionFilter, setActionFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadAuditLogs();
  }, [page, rowsPerPage, actionFilter]);

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const params: any = {
        page: page + 1,
        page_size: rowsPerPage,
      };
      if (actionFilter) params.action = actionFilter;
      
      const response = await apiClient.get<{ count: number; results: AuditEntry[] }>('/audit/', { params });
      setLogs(response.results || []);
      setTotalCount(response.count || 0);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = searchTerm
    ? logs.filter(log =>
        log.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.action.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : logs;

  const getActionColor = (action: string) => actionColors[action] || 'default';

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Audit Log</Typography>
          <Typography color="text.secondary">Track all system activities and changes</Typography>
        </Box>
        <IconButton onClick={loadAuditLogs}><Refresh /></IconButton>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} sx={{ alignItems: 'center' }}>
            <Grid size={{ xs: 12, sm: 4, md: 3 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Action Type</InputLabel>
                <Select value={actionFilter} label="Action Type" onChange={(e) => setActionFilter(e.target.value)}>
                  <MenuItem value="">All Actions</MenuItem>
                  <MenuItem value="CREATE">Create</MenuItem>
                  <MenuItem value="UPDATE">Update</MenuItem>
                  <MenuItem value="DELETE">Delete</MenuItem>
                  <MenuItem value="LOGIN">Login</MenuItem>
                  <MenuItem value="LOGIN_FAILED">Login Failed</MenuItem>
                  <MenuItem value="PASSWORD_CHANGE">Password Change</MenuItem>
                  <MenuItem value="ALERT_CREATE">Alert Create</MenuItem>
                  <MenuItem value="INCIDENT_CREATE">Incident Create</MenuItem>
                  <MenuItem value="REPORT_GENERATE">Report Generate</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 8, md: 6 }}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search audit logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                slotProps={{ input: { startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} /> } }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Audit Log Table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Timestamp</TableCell>
              <TableCell>User</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>IP Address</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredLogs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="text.secondary" sx={{ py: 3 }}>No audit logs found</Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredLogs.map((log) => (
                <TableRow key={log.id} hover>
                  <TableCell>
                    <Typography variant="body2" noWrap>
                      {new Date(log.timestamp).toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell>{log.username || 'System'}</TableCell>
                  <TableCell>
                    <Chip label={log.action.replace('_', ' ')} size="small" color={getActionColor(log.action)} />
                  </TableCell>
                  <TableCell>
                    <Chip label={log.severity} size="small" 
                      color={log.severity === 'critical' ? 'error' : log.severity === 'warning' ? 'warning' : 'default'} />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                      {log.description}
                    </Typography>
                  </TableCell>
                  <TableCell>{log.ip_address || '-'}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={totalCount}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </TableContainer>
    </Box>
  );
};