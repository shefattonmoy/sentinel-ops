import React, { useState } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from "@mui/material";
import { Save } from "@mui/icons-material";
import { apiClient } from "../../services/api/client";
import { useAuth } from "../../context/AuthContext";

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [settings, setSettings] = useState({
    email_notifications: true,
    browser_notifications: true,
    slack_webhook_url: "",
    discord_webhook_url: "",
    timezone: "UTC",
    session_timeout: 30,
    auto_logout: true,
    dark_mode: true,
  });

  const handleSave = async () => {
    setLoading(true);
    setError("");
    setMessage("");
    try {
      await apiClient.patch("/auth/profile/update/", settings);

      localStorage.setItem(
        "session_timeout",
        settings.session_timeout.toString(),
      );

      setMessage("Settings saved successfully");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save settings");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Settings
        </Typography>
        <Typography color="text.secondary">
          Configure application settings and integrations
        </Typography>
      </Box>

      {message && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMessage("")}>
          {message}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      {/* Notifications Settings */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            Notifications
          </Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.email_notifications}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        email_notifications: e.target.checked,
                      })
                    }
                  />
                }
                label="Email Notifications"
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.browser_notifications}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        browser_notifications: e.target.checked,
                      })
                    }
                  />
                }
                label="Browser Notifications"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Integrations */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            Integrations
          </Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <TextField
                label="Slack Webhook URL"
                fullWidth
                value={settings.slack_webhook_url}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    slack_webhook_url: e.target.value,
                  })
                }
                placeholder="https://hooks.slack.com/services/..."
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                label="Discord Webhook URL"
                fullWidth
                value={settings.discord_webhook_url}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    discord_webhook_url: e.target.value,
                  })
                }
                placeholder="https://discord.com/api/webhooks/..."
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* General Settings */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            General
          </Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Timezone</InputLabel>
                <Select
                  value={settings.timezone}
                  label="Timezone"
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      timezone: e.target.value as string,
                    })
                  }
                >
                  <MenuItem value="UTC">UTC</MenuItem>
                  <MenuItem value="US/Eastern">US/Eastern (EST/EDT)</MenuItem>
                  <MenuItem value="US/Central">US/Central (CST/CDT)</MenuItem>
                  <MenuItem value="US/Mountain">US/Mountain (MST/MDT)</MenuItem>
                  <MenuItem value="US/Pacific">US/Pacific (PST/PDT)</MenuItem>
                  <MenuItem value="Europe/London">
                    Europe/London (GMT/BST)
                  </MenuItem>
                  <MenuItem value="Europe/Paris">
                    Europe/Paris (CET/CEST)
                  </MenuItem>
                  <MenuItem value="Europe/Berlin">
                    Europe/Berlin (CET/CEST)
                  </MenuItem>
                  <MenuItem value="Asia/Kolkata">Asia/Kolkata (IST)</MenuItem>
                  <MenuItem value="Asia/Singapore">
                    Asia/Singapore (SGT)
                  </MenuItem>
                  <MenuItem value="Asia/Tokyo">Asia/Tokyo (JST)</MenuItem>
                  <MenuItem value="Australia/Sydney">
                    Australia/Sydney (AEST/AEDT)
                  </MenuItem>
                  <MenuItem value="Pacific/Auckland">
                    Pacific/Auckland (NZST/NZDT)
                  </MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                label="Session Timeout (minutes)"
                fullWidth
                type="number"
                value={settings.session_timeout}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    session_timeout: parseInt(e.target.value) || 30,
                  })
                }
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.auto_logout}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        auto_logout: e.target.checked,
                      })
                    }
                  />
                }
                label="Auto logout on inactivity"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Button
        variant="contained"
        startIcon={loading ? <CircularProgress size={20} /> : <Save />}
        onClick={handleSave}
        disabled={loading}
      >
        Save Settings
      </Button>
    </Box>
  );
};
