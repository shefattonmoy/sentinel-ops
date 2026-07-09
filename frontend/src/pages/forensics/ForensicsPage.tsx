import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Chip,
  LinearProgress,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from "@mui/material";
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
} from "@mui/lab";
import { Search, Refresh } from "@mui/icons-material";
import { apiClient } from "../../services/api/client";

interface TimelineEntry {
  id: string;
  type: string;
  icon: string;
  timestamp: string;
  title: string;
  description: string;
  severity: string;
  source: string;
  source_ip?: string;
  status?: string;
}

export const ForensicsPage: React.FC = () => {
  const [host, setHost] = useState("");
  const [hours, setHours] = useState(24);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [hosts, setHosts] = useState<any[]>([]);

  useEffect(() => {
    loadHosts();
  }, []);

  const loadHosts = async () => {
    try {
      const response = await apiClient.get<any[]>("/forensics/hosts/");
      setHosts(response || []);
    } catch (err) {
      console.error(err);
    }
  };

  const searchTimeline = async () => {
    if (!host) return;
    setLoading(true);
    try {
      const response = await apiClient.get<{ timeline: TimelineEntry[] }>(
        `/forensics/timeline/?host=${encodeURIComponent(host)}&hours=${hours}`,
      );
      setTimeline(response.timeline || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "error";
      case "high":
        return "error";
      case "medium":
        return "warning";
      case "low":
        return "info";
      default:
        return "grey";
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "event":
        return "📊";
      case "alert":
        return "🚨";
      case "incident":
        return "🔴";
      default:
        return "📋";
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Digital Forensics
        </Typography>
        <Typography color="text.secondary">
          Forensic timeline and attack chain analysis
        </Typography>
      </Box>

      {/* Search */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} sx={{ alignItems: "center" }}>
            <Grid size={{ xs: 12, sm: 5 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Select Host</InputLabel>
                <Select
                  value={host}
                  label="Select Host"
                  onChange={(e) => setHost(e.target.value)}
                >
                  {hosts.map((h) => (
                    <MenuItem key={h.hostname} value={h.hostname || h.ip}>
                      {h.name} ({h.hostname})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 6, sm: 3 }}>
              <TextField
                label="Hours"
                type="number"
                size="small"
                fullWidth
                value={hours}
                onChange={(e) => setHours(parseInt(e.target.value) || 24)}
              />
            </Grid>
            <Grid size={{ xs: 6, sm: 4 }}>
              <Button
                variant="contained"
                startIcon={<Search />}
                onClick={searchTimeline}
                disabled={!host}
                fullWidth
              >
                Analyze
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Timeline */}
      {timeline.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Forensic Timeline ({timeline.length} entries)
            </Typography>
            <Timeline>
              {timeline.map((entry, index) => (
                <TimelineItem key={entry.id || index}>
                  <TimelineSeparator>
                    <TimelineDot
                      color={getSeverityColor(entry.severity) as any}
                    >
                      {getTypeIcon(entry.type)}
                    </TimelineDot>
                    {index < timeline.length - 1 && <TimelineConnector />}
                  </TimelineSeparator>
                  <TimelineContent>
                    <Paper variant="outlined" sx={{ p: 1.5, mb: 1 }}>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 0.5,
                        }}
                      >
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {entry.title}
                        </Typography>
                        <Box sx={{ display: "flex", gap: 0.5 }}>
                          <Chip
                            label={entry.type}
                            size="small"
                            variant="outlined"
                          />
                          <Chip
                            label={entry.severity}
                            size="small"
                            color={getSeverityColor(entry.severity) as any}
                          />
                        </Box>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {entry.description}
                      </Typography>
                      <Typography
                        variant="caption"
                        color="text.disabled"
                        sx={{ mt: 0.5, display: "block" }}
                      >
                        {new Date(entry.timestamp).toLocaleString()}
                        {entry.source_ip && ` • IP: ${entry.source_ip}`}
                      </Typography>
                    </Paper>
                  </TimelineContent>
                </TimelineItem>
              ))}
            </Timeline>
          </CardContent>
        </Card>
      )}

      {!loading && timeline.length === 0 && host && (
        <Card>
          <CardContent sx={{ textAlign: "center", py: 4 }}>
            <Typography color="text.secondary">
              No forensic data found for this host
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};
