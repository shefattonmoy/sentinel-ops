import React, { useMemo } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Box,
  CircularProgress,
  Typography,
} from "@mui/material";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ThemeModeProvider, useThemeMode } from "./context/ThemeContext";
import { MainLayout } from "./components/layout/MainLayout";
import { LoginPage } from "./pages/auth/LoginPage";
import { DashboardPage } from "./pages/dashboard/DashboardPage";
import { AgentsPage } from "./pages/agents/AgentsPage";
import { EventsPage } from "./pages/events/EventsPage";
import { AlertsPage } from "./pages/alerts/AlertsPage";
import { IncidentsPage } from "./pages/incidents/IncidentsPage";
import { RulesPage } from "./pages/rules/RulesPage";
import { ReportsPage } from "./pages/reports/ReportsPage";
import { ProfilePage } from "./pages/profile/ProfilePage";
import { AuditLogPage } from "./pages/audit/AuditLogPage";
import { SettingsPage } from './pages/settings/SettingsPage';
import { ThreatIntelPage } from './pages/threatintel/ThreatIntelPage';
import { PlaybooksPage } from './pages/playbooks/PlaybooksPage';
import { SchedulerPage } from './pages/scheduler/SchedulerPage';
import { MitrePage } from './pages/mitre/MitrePage';
import { ForensicsPage } from './pages/forensics/ForensicsPage';
import { RiskPage } from './pages/risks/RiskPage';
import { HoneypotPage } from './pages/honeypot/HoneypotPage';
import { CompliancePage } from './pages/compliance/CompliancePage';
import { TopologyPage } from './pages/topology/TopologyPage';
import { ChatPage } from './pages/chat/ChatPage';
import { AnalyticsPage } from './pages/analytics/AnalyticsPage';
import { GamificationPage } from './pages/gamification/GamificationPage';


// Loading screen shown while checking auth
const LoadingScreen = () => (
  <Box
    sx={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "100vh",
      bgcolor: "background.default",
    }}
  >
    <CircularProgress size={48} sx={{ mb: 2 }} />
    <Typography variant="h6" color="text.secondary">
      Loading SentinelOps...
    </Typography>
  </Box>
);

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading screen while checking auth
  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

function AppRoutes() {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading screen during initial auth check
  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="agents" element={<AgentsPage />} />
        <Route path="events" element={<EventsPage />} />
        <Route path="alerts" element={<AlertsPage />} />
        <Route path="incidents" element={<IncidentsPage />} />
        <Route path="rules" element={<RulesPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="audit" element={<AuditLogPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="threat-intel" element={<ThreatIntelPage />} />
        <Route path="playbooks" element={<PlaybooksPage />} />
        <Route path="scheduler" element={<SchedulerPage />} />
        <Route path="mitre" element={<MitrePage />} />
        <Route path="forensics" element={<ForensicsPage />} />
        <Route path="risks" element={<RiskPage />} />
        <Route path="honeypot" element={<HoneypotPage />} />
        <Route path="compliance" element={<CompliancePage />} />
        <Route path="topology" element={<TopologyPage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="gamification" element={<GamificationPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

function AppContent() {
  const { mode } = useThemeMode();

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: { main: "#6366f1" },
          secondary: { main: "#ec4899" },
          background:
            mode === "dark"
              ? { default: "#0f172a", paper: "#1e293b" }
              : { default: "#f8fafc", paper: "#ffffff" },
        },
        components: {
          MuiButton: {
            styleOverrides: {
              root: { textTransform: "none", borderRadius: 8 },
            },
          },
          MuiCard: { styleOverrides: { root: { borderRadius: 12 } } },
        },
      }),
    [mode],
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppRoutes />
    </ThemeProvider>
  );
}

function App() {
  return (
    <ThemeModeProvider>
      <BrowserRouter>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </BrowserRouter>
    </ThemeModeProvider>
  );
}

export default App;
