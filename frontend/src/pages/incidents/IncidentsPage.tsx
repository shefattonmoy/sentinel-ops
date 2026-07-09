// src/pages/incidents/IncidentsPage.tsx
import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  LinearProgress,
  Grid,
  Tooltip,
} from "@mui/material";
import { Refresh, Visibility, Add, Gavel } from "@mui/icons-material";
import { incidentService } from "../../services/api/incidents";
import {
  Incident,
  IncidentStatus,
  AlertSeverity,
  IncidentType,
} from "../../types";

const severityColors: Record<
  AlertSeverity,
  "error" | "warning" | "info" | "success" | "default"
> = {
  critical: "error",
  high: "error",
  medium: "warning",
  low: "info",
  info: "default",
};

const statusColors: Record<
  IncidentStatus,
  "error" | "warning" | "info" | "success" | "default"
> = {
  new: "error",
  triaging: "warning",
  investigating: "info",
  containment: "error",
  eradication: "warning",
  recovery: "info",
  resolved: "success",
  closed: "default",
  false_positive: "default",
};

export const IncidentsPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(
    null,
  );
  const [openDialog, setOpenDialog] = useState(false);
  const [newIncident, setNewIncident] = useState<{
    title: string;
    description: string;
    severity: AlertSeverity;
    incident_type: IncidentType;
  }>({
    title: "",
    description: "",
    severity: "medium",
    incident_type: "other",
  });
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  useEffect(() => {
    loadIncidents();
  }, [statusFilter]);

  const loadIncidents = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (statusFilter) params.status = statusFilter;
      const response = await incidentService.list(params);
      setIncidents(response.results);
    } catch (err) {
      console.error("Failed to load incidents:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateIncident = async () => {
    try {
      await incidentService.create(newIncident);
      setShowCreateDialog(false);
      setNewIncident({
        title: "",
        description: "",
        severity: "medium",
        incident_type: "other",
      });
      loadIncidents();
    } catch (err) {
      console.error("Failed to create incident:", err);
    }
  };

  const handleCorrelate = async () => {
    try {
      await incidentService.correlate();
      loadIncidents();
    } catch (err) {
      console.error("Failed to correlate:", err);
    }
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            Incidents
          </Typography>
          <Typography color="text.secondary">
            Manage security incidents
          </Typography>
        </Box>
        <Box>
          <Button
            startIcon={<Gavel />}
            onClick={handleCorrelate}
            sx={{ mr: 1 }}
          >
            Run Correlation
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setShowCreateDialog(true)}
          >
            Create Incident
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 4 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="new">New</MenuItem>
                  <MenuItem value="triaging">Triaging</MenuItem>
                  <MenuItem value="investigating">Investigating</MenuItem>
                  <MenuItem value="containment">Containment</MenuItem>
                  <MenuItem value="resolved">Resolved</MenuItem>
                  <MenuItem value="closed">Closed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Incidents Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Priority</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Assigned To</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {incidents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography color="text.secondary" sx={{ py: 3 }}>
                    No incidents found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              incidents.map((incident) => (
                <TableRow key={incident.id} hover>
                  <TableCell>
                    <Chip
                      label={incident.priority?.toUpperCase()}
                      size="small"
                      color={
                        incident.priority === "p1"
                          ? "error"
                          : incident.priority === "p2"
                            ? "warning"
                            : "default"
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {incident.title}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {incident.incident_type?.replace(/_/g, " ")}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={incident.severity}
                      size="small"
                      color={severityColors[incident.severity]}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={incident.status}
                      size="small"
                      color={statusColors[incident.status]}
                    />
                  </TableCell>
                  <TableCell>{incident.assigned_to_name || "-"}</TableCell>
                  <TableCell>
                    {new Date(incident.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedIncident(incident);
                          setOpenDialog(true);
                        }}
                      >
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Incident Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Incident</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: "flex", flexDirection: "column", gap: 2 }}>
            <TextField
              label="Title"
              fullWidth
              value={newIncident.title}
              onChange={(e) =>
                setNewIncident({ ...newIncident, title: e.target.value })
              }
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={newIncident.description}
              onChange={(e) =>
                setNewIncident({ ...newIncident, description: e.target.value })
              }
            />
            <FormControl fullWidth>
              <InputLabel>Incident Type</InputLabel>
              <Select
                value={newIncident.incident_type}
                label="Incident Type"
                onChange={(e) =>
                  setNewIncident({
                    ...newIncident,
                    incident_type: e.target.value as IncidentType,
                  })
                }
              >
                <MenuItem value="brute_force">Brute Force</MenuItem>
                <MenuItem value="malware">Malware</MenuItem>
                <MenuItem value="data_breach">Data Breach</MenuItem>
                <MenuItem value="unauthorized_access">
                  Unauthorized Access
                </MenuItem>
                <MenuItem value="privilege_escalation">
                  Privilege Escalation
                </MenuItem>
                <MenuItem value="system_compromise">System Compromise</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Severity</InputLabel>
              <Select
                value={newIncident.severity}
                label="Severity"
                onChange={(e) =>
                  setNewIncident({
                    ...newIncident,
                    severity: e.target.value as AlertSeverity,
                  })
                }
              >
                <MenuItem value="critical">Critical</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="low">Low</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateIncident}
            disabled={!newIncident.title}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Incident Dialog */}
      <Dialog
        open={openDialog}
        onClose={() => setOpenDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{selectedIncident?.title}</DialogTitle>
        <DialogContent>
          {selectedIncident && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2" sx={{ mb: 2 }}>
                {selectedIncident.description}
              </Typography>
              <Box sx={{ display: "flex", gap: 1, mb: 2, flexWrap: "wrap" }}>
                <Chip
                  label={`Priority: ${selectedIncident.priority?.toUpperCase()}`}
                  color="error"
                  size="small"
                />
                <Chip
                  label={`Severity: ${selectedIncident.severity}`}
                  color={severityColors[selectedIncident.severity]}
                  size="small"
                />
                <Chip
                  label={`Status: ${selectedIncident.status}`}
                  color={statusColors[selectedIncident.status]}
                  size="small"
                />
                <Chip
                  label={`Type: ${selectedIncident.incident_type}`}
                  size="small"
                  variant="outlined"
                />
              </Box>
              {selectedIncident.source_ip && (
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Source IP: {selectedIncident.source_ip}
                </Typography>
              )}
              <Typography variant="body2">
                Alerts: {selectedIncident.alerts_count ?? 0}
              </Typography>
              <Typography variant="body2">
                Events: {selectedIncident.events_count ?? 0}
              </Typography>
              {selectedIncident.time_to_detect && (
                <Typography variant="body2">
                  Time to Detect: {selectedIncident.time_to_detect} min
                </Typography>
              )}
              {selectedIncident.time_to_resolve && (
                <Typography variant="body2">
                  Time to Resolve: {selectedIncident.time_to_resolve} min
                </Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
