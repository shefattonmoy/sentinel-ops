// src/pages/events/EventsPage.tsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tooltip,
  LinearProgress,
  TablePagination,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { Event } from '../../types';
import { eventService } from '../../services/api/events';

// Define EventFilters interface locally or import from types
interface EventFilters {
  severity?: string;
  source?: string;
  search?: string;
  start_date?: string;
  end_date?: string;
}

export const EventsPage: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<EventFilters>({});
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    loadEvents();
  }, [filters, page, rowsPerPage]);

  const loadEvents = async () => {
    setLoading(true);
    try {
      const response = await eventService.list({
        ...filters,
        page: page + 1,
        page_size: rowsPerPage,
      });
      setEvents(response.results);
      setTotalCount(response.count);
    } catch (error) {
      console.error('Failed to load events:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string): 'error' | 'warning' | 'info' | 'default' => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }} gutterBottom>
            Events Stream
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Real-time security event monitoring
          </Typography>
        </Box>
        <Button variant="outlined" startIcon={<RefreshIcon />} onClick={loadEvents}>
          Refresh
        </Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Severity</InputLabel>
                <Select
                  value={filters.severity || ''}
                  label="Severity"
                  onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="low">Low</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Source</InputLabel>
                <Select
                  value={filters.source || ''}
                  label="Source"
                  onChange={(e) => setFilters({ ...filters, source: e.target.value })}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="ssh">SSH</MenuItem>
                  <MenuItem value="nginx">Nginx</MenuItem>
                  <MenuItem value="docker">Docker</MenuItem>
                  <MenuItem value="system">System</MenuItem>
                  <MenuItem value="django">Django</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search events..."
                value={filters.search || ''}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                slotProps={{
                  input: {
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                  },
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <TextField
                fullWidth
                size="small"
                type="datetime-local"
                label="Start Date"
                value={filters.start_date || ''}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <TextField
                fullWidth
                size="small"
                type="datetime-local"
                label="End Date"
                value={filters.end_date || ''}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Events Table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Timestamp</TableCell>
              <TableCell>Event Type</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Source IP</TableCell>
              <TableCell>Username</TableCell>
              <TableCell>Message</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {events.length === 0 && !loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography color="text.secondary" sx={{ py: 3 }}>
                    No events found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              events.map((event) => (
                <TableRow key={event.id} hover>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                      {new Date(event.timestamp).toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {event.event_type}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={event.severity}
                      size="small"
                      color={getSeverityColor(event.severity)}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip label={event.source} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 120 }}>
                      {event.source_ip || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>{event.username || '-'}</TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 250 }}>
                      {event.message}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Tooltip title="View Details">
                      <IconButton size="small">
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
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
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[25, 50, 100]}
        />
      </TableContainer>
    </Box>
  );
};