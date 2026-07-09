import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
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
  Tooltip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
} from "@mui/material";
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  Computer as ComputerIcon,
  CheckCircle as OnlineIcon,
  Cancel as OfflineIcon,
  Warning as WarningIcon,
} from "@mui/icons-material";
import { Agent } from "../../types";
import { agentService } from "../../services/api/agents";

export const AgentsPage: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [openRegisterDialog, setOpenRegisterDialog] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [openViewDialog, setOpenViewDialog] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  const [newAgent, setNewAgent] = useState({
    name: "",
    hostname: "",
    version: "1.0.0",
  });

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    setLoading(true);
    try {
      const response = await agentService.list();
      setAgents(response.results);
    } catch (error) {
      console.error("Failed to load agents:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    try {
      await agentService.register({
        name: newAgent.name,
        hostname: newAgent.hostname,
        version: newAgent.version,
      });
      setOpenRegisterDialog(false);
      setNewAgent({ name: "", hostname: "", version: "1.0.0" });
      loadAgents();
    } catch (error) {
      console.error("Failed to register agent:", error);
    }
  };

  const handleDeleteClick = (agent: Agent) => {
    setSelectedAgent(agent);
    setDeleteError("");
    setOpenDeleteDialog(true);
  };

  const handleDeleteConfirm = async () => {
    if (!selectedAgent) return;
    setDeleteLoading(true);
    setDeleteError("");
    try {
      await agentService.delete(selectedAgent.id);
      setOpenDeleteDialog(false);
      setSelectedAgent(null);
      loadAgents();
    } catch (error: any) {
      setDeleteError(error?.response?.data?.detail || "Failed to delete agent");
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleViewClick = (agent: Agent) => {
    setSelectedAgent(agent);
    setOpenViewDialog(true);
  };

  if (loading) return <LinearProgress />;

  const onlineCount = agents.filter((a) => a.status === "online").length;
  const offlineCount = agents.filter((a) => a.status === "offline").length;
  const degradedCount = agents.filter((a) => a.status === "degraded").length;

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }} gutterBottom>
            Agents Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor and manage your security agents
          </Typography>
        </Box>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadAgents}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenRegisterDialog(true)}
          >
            Register Agent
          </Button>
        </Box>
      </Box>

      {/* Agent Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography
                variant="subtitle2"
                color="text.secondary"
                gutterBottom
              >
                Total Agents
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {agents.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography
                variant="subtitle2"
                color="text.secondary"
                gutterBottom
              >
                Online
              </Typography>
              <Typography
                variant="h4"
                sx={{ fontWeight: 700 }}
                color="success.main"
              >
                {onlineCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography
                variant="subtitle2"
                color="text.secondary"
                gutterBottom
              >
                Offline
              </Typography>
              <Typography
                variant="h4"
                sx={{ fontWeight: 700 }}
                color="error.main"
              >
                {offlineCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography
                variant="subtitle2"
                color="text.secondary"
                gutterBottom
              >
                Degraded
              </Typography>
              <Typography
                variant="h4"
                sx={{ fontWeight: 700 }}
                color="warning.main"
              >
                {degradedCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Agents Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Status</TableCell>
              <TableCell>Agent Name</TableCell>
              <TableCell>Hostname</TableCell>
              <TableCell>Version</TableCell>
              <TableCell>Last Heartbeat</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {agents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="text.secondary" sx={{ py: 3 }}>
                    No agents registered yet
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              agents.map((agent) => (
                <TableRow key={agent.id} hover>
                  <TableCell>
                    {agent.status === "online" ? (
                      <OnlineIcon color="success" />
                    ) : agent.status === "degraded" ? (
                      <WarningIcon color="warning" />
                    ) : (
                      <OfflineIcon color="error" />
                    )}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: "flex", alignItems: "center" }}>
                      <ComputerIcon sx={{ mr: 1, color: "text.secondary" }} />
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {agent.name}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{agent.hostname}</TableCell>
                  <TableCell>
                    <Chip label={`v${agent.version}`} size="small" />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {agent.last_heartbeat
                        ? new Date(agent.last_heartbeat).toLocaleString()
                        : "Never"}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleViewClick(agent)}
                      >
                        <VisibilityIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Agent">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteClick(agent)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Register Agent Dialog */}
      <Dialog
        open={openRegisterDialog}
        onClose={() => setOpenRegisterDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Register New Agent</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: "flex", flexDirection: "column", gap: 2 }}>
            <TextField
              label="Agent Name"
              fullWidth
              value={newAgent.name}
              onChange={(e) =>
                setNewAgent({ ...newAgent, name: e.target.value })
              }
              placeholder="e.g., Production Web Server 1"
            />
            <TextField
              label="Hostname"
              fullWidth
              value={newAgent.hostname}
              onChange={(e) =>
                setNewAgent({ ...newAgent, hostname: e.target.value })
              }
              placeholder="e.g., web-prod-01"
            />
            <TextField
              label="Version"
              fullWidth
              value={newAgent.version}
              onChange={(e) =>
                setNewAgent({ ...newAgent, version: e.target.value })
              }
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenRegisterDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleRegister}
            disabled={!newAgent.name || !newAgent.hostname}
          >
            Register
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={openDeleteDialog}
        onClose={() => setOpenDeleteDialog(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Delete Agent</DialogTitle>
        <DialogContent>
          {deleteError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {deleteError}
            </Alert>
          )}
          <Typography>
            Are you sure you want to delete agent{" "}
            <strong>"{selectedAgent?.name}"</strong>?
          </Typography>
          <Typography color="text.secondary" variant="body2" sx={{ mt: 1 }}>
            Hostname: {selectedAgent?.hostname}
            <br />
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setOpenDeleteDialog(false)}
            disabled={deleteLoading}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleDeleteConfirm}
            disabled={deleteLoading}
          >
            {deleteLoading ? "Deleting..." : "Delete Agent"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Agent Details Dialog */}
      <Dialog
        open={openViewDialog}
        onClose={() => setOpenViewDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Agent Details</DialogTitle>
        <DialogContent>
          {selectedAgent && (
            <Box sx={{ pt: 1 }}>
              <Typography variant="h6" gutterBottom>
                {selectedAgent.name}
              </Typography>
              <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
                <Chip
                  label={selectedAgent.status}
                  color={
                    selectedAgent.status === "online"
                      ? "success"
                      : selectedAgent.status === "degraded"
                        ? "warning"
                        : "error"
                  }
                  size="small"
                />
                <Chip
                  label={`v${selectedAgent.version}`}
                  size="small"
                  variant="outlined"
                />
                <Chip
                  label={selectedAgent.agent_type || "linux"}
                  size="small"
                  variant="outlined"
                />
              </Box>
              <Grid container spacing={2}>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    Hostname
                  </Typography>
                  <Typography>{selectedAgent.hostname}</Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    Agent ID
                  </Typography>
                  <Typography variant="body2">
                    {selectedAgent.agent_id}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    IP Address
                  </Typography>
                  <Typography>{selectedAgent.ip_address || "N/A"}</Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    Last Heartbeat
                  </Typography>
                  <Typography>
                    {selectedAgent.last_heartbeat
                      ? new Date(selectedAgent.last_heartbeat).toLocaleString()
                      : "Never"}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    CPU Usage
                  </Typography>
                  <Typography>
                    {selectedAgent.cpu_usage
                      ? `${selectedAgent.cpu_usage}%`
                      : "N/A"}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    Memory Usage
                  </Typography>
                  <Typography>
                    {selectedAgent.memory_usage
                      ? `${selectedAgent.memory_usage}%`
                      : "N/A"}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    Disk Usage
                  </Typography>
                  <Typography>
                    {selectedAgent.disk_usage
                      ? `${selectedAgent.disk_usage}%`
                      : "N/A"}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    Logs Collected
                  </Typography>
                  <Typography>
                    {selectedAgent.total_logs_collected?.toLocaleString() ||
                      "0"}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <Typography variant="body2" color="text.secondary">
                    Tags
                  </Typography>
                  <Box
                    sx={{
                      display: "flex",
                      gap: 0.5,
                      flexWrap: "wrap",
                      mt: 0.5,
                    }}
                  >
                    {selectedAgent.tags?.length > 0 ? (
                      selectedAgent.tags.map((tag, i) => (
                        <Chip
                          key={i}
                          label={tag}
                          size="small"
                          variant="outlined"
                        />
                      ))
                    ) : (
                      <Typography variant="body2">No tags</Typography>
                    )}
                  </Box>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenViewDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
