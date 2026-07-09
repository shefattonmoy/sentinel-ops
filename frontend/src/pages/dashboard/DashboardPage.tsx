import React, { useState, useEffect } from "react";
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  LinearProgress,
  IconButton,
  useTheme,
} from "@mui/material";
import {
  Computer,
  Timeline,
  Warning,
  Gavel,
  Security,
  Refresh,
  TrendingUp,
  TrendingDown,
} from "@mui/icons-material";
import {
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { dashboardService } from "../../services/api/dashboard";
import { DashboardStats } from "../../types";

const COLORS = ["#ef4444", "#f97316", "#eab308", "#3b82f6", "#10b981"];

export const DashboardPage: React.FC = () => {
  const theme = useTheme();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [eventsChart, setEventsChart] = useState<any[]>([]);
  const [alertStats, setAlertStats] = useState<any>(null);
  const [topIps, setTopIps] = useState<any[]>([]);
  const [failedLogins, setFailedLogins] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const [overview, events, alerts, ips, logins] = await Promise.all([
        dashboardService.getOverview(),
        dashboardService.getEventsChart(24),
        dashboardService.getAlertStats(),
        dashboardService.getTopIps(24, 10),
        dashboardService.getFailedLogins(24),
      ]) as [DashboardStats, any[], any, any[], any];
      setStats(overview);
      setEventsChart(events);
      setAlertStats(alerts);
      setTopIps(ips);
      setFailedLogins(logins);
    } catch (err) {
      console.error("Failed to load dashboard:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            Security Dashboard
          </Typography>
          <Typography color="text.secondary">
            Overview of your security operations
          </Typography>
        </Box>
        <IconButton onClick={loadDashboard}>
          <Refresh />
        </IconButton>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Agents Online
                </Typography>
                <Computer color="primary" />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {stats?.agents_online}/{stats?.agents_total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Events Today
                </Typography>
                <Timeline color="info" />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {stats?.events_today?.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Critical Alerts
                </Typography>
                <Warning color="error" />
              </Box>
              <Typography
                variant="h4"
                sx={{ fontWeight: 700 }}
                color="error.main"
              >
                {stats?.critical_alerts}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Security Score
                </Typography>
                <Security color="success" />
              </Box>
              <Typography
                variant="h4"
                sx={{ fontWeight: 700 }}
                color="success.main"
              >
                {stats?.security_score}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Events Over Time
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={eventsChart}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" tick={{ fontSize: 12 }} />
                  <YAxis />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke={theme.palette.primary.main}
                    fill={theme.palette.primary.main}
                    fillOpacity={0.2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, lg: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Alert Severity
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={alertStats?.severity_distribution}
                    dataKey="count"
                    nameKey="severity"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                  >
                    {alertStats?.severity_distribution?.map(
                      (_: any, index: number) => (
                        <Cell
                          key={index}
                          fill={COLORS[index % COLORS.length]}
                        />
                      ),
                    )}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Top Source IPs
              </Typography>
              {topIps?.slice(0, 10).map((ip: any, i: number) => (
                <Box
                  key={i}
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    py: 1,
                    borderBottom: i < 9 ? 1 : 0,
                    borderColor: "divider",
                  }}
                >
                  <Typography variant="body2">{ip.source_ip}</Typography>
                  <Chip label={ip.count} size="small" color="error" />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Failed Logins by IP
              </Typography>
              {failedLogins?.by_ip?.slice(0, 10).map((item: any, i: number) => (
                <Box
                  key={i}
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    py: 1,
                    borderBottom: i < 9 ? 1 : 0,
                    borderColor: "divider",
                  }}
                >
                  <Typography variant="body2">
                    {item.source_ip || "N/A"}
                  </Typography>
                  <Chip label={item.count} size="small" color="warning" />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
