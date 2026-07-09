// src/pages/profile/ProfilePage.tsx
import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Avatar,
  Divider,
  Chip,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Paper,
  Badge,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from "@mui/material";
import {
  Save,
  Shield,
  Key,
  ContentCopy,
  Cancel,
  PhotoCamera,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../../services/api/client";
import { useAuth } from "../../context/AuthContext";

interface ProfileData {
  id?: string;
  username?: string;
  first_name: string;
  last_name: string;
  email: string;
  bio: string;
  phone: string;
  department: string;
  timezone: string;
  email_notifications: boolean;
  browser_notifications: boolean;
  two_factor_enabled?: boolean;
  avatar?: string | null;
  role?: string;
}

interface PasswordData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

function TabPanel({
  children,
  value,
  index,
}: {
  children?: React.ReactNode;
  value: number;
  index: number;
}) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [profile, setProfile] = useState<ProfileData>({
    first_name: "",
    last_name: "",
    email: "",
    bio: "",
    phone: "",
    department: "",
    timezone: "UTC",
    email_notifications: true,
    browser_notifications: true,
  });

  const [passwords, setPasswords] = useState<PasswordData>({
    old_password: "",
    new_password: "",
    confirm_password: "",
  });

  const API_BASE = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [qrCode, setQrCode] = useState("");
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [verifyToken, setVerifyToken] = useState("");
  const [disablePassword, setDisablePassword] = useState("");
  const [showQrDialog, setShowQrDialog] = useState(false);
  const [showCodesDialog, setShowCodesDialog] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await apiClient.get<ProfileData>("/auth/profile/");
      console.log("Profile loaded:", response); // Debug log
      setProfile(response);
      // FIX: Ensure boolean comparison
      setTwoFactorEnabled(response.two_factor_enabled === true);
      if (response.avatar) {
        setAvatarUrl(
          response.avatar.startsWith("http")
            ? response.avatar
            : `${API_BASE}${response.avatar}`,
        );
      } else {
        setAvatarUrl(null);
      }
    } catch (err) {
      console.error("Failed to load profile:", err);
    }
  };

  const handleProfileUpdate = async () => {
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const updateData = {
        first_name: profile.first_name,
        last_name: profile.last_name,
        email: profile.email,
        bio: profile.bio,
        phone: profile.phone,
        department: profile.department,
        timezone: profile.timezone,
        email_notifications: profile.email_notifications,
        browser_notifications: profile.browser_notifications,
      };

      const response = await apiClient.patch<{ user: ProfileData }>(
        "/auth/profile/update/",
        updateData,
      );
      setProfile(response.user || response);
      setMessage("Profile updated successfully");
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        JSON.stringify(err.response?.data) ||
        "Update failed";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Please select an image file");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError("Image size must be less than 5MB");
      return;
    }

    setUploadingAvatar(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("avatar", file);

      const response = await apiClient.post<{ avatar_url: string }>(
        "/auth/profile/avatar/",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } },
      );

      setAvatarUrl(response.avatar_url);
      setMessage("Avatar uploaded successfully");
    } catch (err: any) {
      setError("Failed to upload avatar");
    } finally {
      setUploadingAvatar(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  // FIX: Navigate to login after password change
  const handlePasswordChange = async () => {
    if (passwords.new_password !== passwords.confirm_password) {
      setError("Passwords do not match");
      return;
    }
    if (passwords.new_password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setLoading(true);
    setError("");
    setMessage("");
    try {
      await apiClient.post("/auth/profile/change-password/", passwords);
      setMessage("Password changed successfully. Redirecting to login...");

      // Clear auth and redirect to login after 2 seconds
      setTimeout(() => {
        logout();
        navigate("/login");
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.error || "Password change failed");
      setLoading(false);
    }
  };

  const handleSetup2FA = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await apiClient.post<{
        qr_code: string;
        backup_codes: string[];
      }>("/auth/profile/2fa/setup/");
      setQrCode(response.qr_code);
      setBackupCodes(response.backup_codes);
      setShowQrDialog(true);
    } catch (err: any) {
      setError("Failed to setup 2FA");
    } finally {
      setLoading(false);
    }
  };

  // FIX: Ensure state updates after verification
  const handleVerify2FA = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await apiClient.post("/auth/profile/2fa/verify/", {
        token: verifyToken,
      });
      console.log("2FA Verify response:", response); // Debug log

      setVerifyToken("");
      setShowQrDialog(false);
      setShowCodesDialog(true);

      // FIX: Update state immediately AND reload from server
      setTwoFactorEnabled(true);
      await loadProfile();

      setMessage("2FA enabled successfully");
    } catch (err: any) {
      setError("Invalid verification code");
    } finally {
      setLoading(false);
    }
  };

  // FIX: Ensure state updates after disabling
  const handleDisable2FA = async () => {
    setLoading(true);
    setError("");
    setMessage("");
    try {
      await apiClient.post("/auth/profile/2fa/disable/", {
        password: disablePassword,
      });
      setDisablePassword("");

      // FIX: Update state immediately AND reload from server
      setTwoFactorEnabled(false);
      await loadProfile();

      setMessage("2FA disabled");
    } catch (err: any) {
      setError("Failed to disable 2FA");
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCodes = () => {
    navigator.clipboard.writeText(backupCodes.join("\n"));
    setMessage("Backup codes copied to clipboard");
  };

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Profile
        </Typography>
        <Typography color="text.secondary">
          Manage your account and security settings
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

      <Card sx={{ mb: 3 }}>
        <CardContent>
          {/* User Info Header */}
          <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
            <Badge
              overlap="circular"
              anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
              badgeContent={
                <IconButton
                  size="small"
                  sx={{
                    bgcolor: "primary.main",
                    "&:hover": { bgcolor: "primary.dark" },
                  }}
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadingAvatar}
                >
                  <PhotoCamera sx={{ fontSize: 16, color: "white" }} />
                </IconButton>
              }
            >
              <Avatar
                src={avatarUrl || undefined}
                sx={{
                  width: 80,
                  height: 80,
                  fontSize: 32,
                  mr: 3,
                  bgcolor: "primary.main",
                }}
              >
                {user?.username?.[0]?.toUpperCase()}
              </Avatar>
            </Badge>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              hidden
              onChange={handleAvatarUpload}
            />
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 700 }}>
                {user?.username}
              </Typography>
              <Typography color="text.secondary">
                {profile.email || user?.email}
              </Typography>
              <Chip
                label={profile.role || user?.role}
                size="small"
                sx={{ mt: 0.5 }}
              />
              {uploadingAvatar && <CircularProgress size={16} sx={{ ml: 1 }} />}
            </Box>
          </Box>

          <Divider sx={{ mb: 2 }} />

          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
            <Tab label="Profile" />
            <Tab label="Security" />
            <Tab label="Two-Factor Auth" />
          </Tabs>

          {/* PROFILE TAB */}
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="First Name"
                  fullWidth
                  value={profile.first_name}
                  onChange={(e) =>
                    setProfile({ ...profile, first_name: e.target.value })
                  }
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="Last Name"
                  fullWidth
                  value={profile.last_name}
                  onChange={(e) =>
                    setProfile({ ...profile, last_name: e.target.value })
                  }
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="Email"
                  fullWidth
                  type="email"
                  value={profile.email}
                  onChange={(e) =>
                    setProfile({ ...profile, email: e.target.value })
                  }
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="Phone"
                  fullWidth
                  value={profile.phone}
                  onChange={(e) =>
                    setProfile({ ...profile, phone: e.target.value })
                  }
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField
                  label="Bio"
                  fullWidth
                  multiline
                  rows={3}
                  value={profile.bio || ""}
                  onChange={(e) =>
                    setProfile({ ...profile, bio: e.target.value })
                  }
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  label="Department"
                  fullWidth
                  value={profile.department}
                  onChange={(e) =>
                    setProfile({ ...profile, department: e.target.value })
                  }
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Timezone</InputLabel>
                  <Select
                    value={profile.timezone}
                    label="Timezone"
                    onChange={(e) =>
                      setProfile({ ...profile, timezone: e.target.value })
                    }
                  >
                    <MenuItem value="UTC">UTC</MenuItem>
                    <MenuItem value="US/Eastern">US/Eastern</MenuItem>
                    <MenuItem value="US/Pacific">US/Pacific</MenuItem>
                    <MenuItem value="Europe/London">Europe/London</MenuItem>
                    <MenuItem value="Asia/Kolkata">Asia/Kolkata</MenuItem>
                    <MenuItem value="Asia/Tokyo">Asia/Tokyo</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={profile.email_notifications}
                      onChange={(e) =>
                        setProfile({
                          ...profile,
                          email_notifications: e.target.checked,
                        })
                      }
                    />
                  }
                  label="Email Notifications"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={profile.browser_notifications}
                      onChange={(e) =>
                        setProfile({
                          ...profile,
                          browser_notifications: e.target.checked,
                        })
                      }
                    />
                  }
                  label="Browser Notifications"
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <Button
                  variant="contained"
                  startIcon={
                    loading ? <CircularProgress size={20} /> : <Save />
                  }
                  onClick={handleProfileUpdate}
                  disabled={loading}
                >
                  Save Changes
                </Button>
              </Grid>
            </Grid>
          </TabPanel>

          {/* SECURITY TAB */}
          <TabPanel value={tabValue} index={1}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Change Password
            </Typography>
            <Box sx={{ maxWidth: 500 }}>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12 }}>
                  <TextField
                    label="Current Password"
                    type="password"
                    fullWidth
                    value={passwords.old_password}
                    onChange={(e) =>
                      setPasswords({
                        ...passwords,
                        old_password: e.target.value,
                      })
                    }
                  />
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <TextField
                    label="New Password"
                    type="password"
                    fullWidth
                    value={passwords.new_password}
                    onChange={(e) =>
                      setPasswords({
                        ...passwords,
                        new_password: e.target.value,
                      })
                    }
                  />
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <TextField
                    label="Confirm New Password"
                    type="password"
                    fullWidth
                    value={passwords.confirm_password}
                    onChange={(e) =>
                      setPasswords({
                        ...passwords,
                        confirm_password: e.target.value,
                      })
                    }
                  />
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <Button
                    variant="contained"
                    startIcon={<Key />}
                    onClick={handlePasswordChange}
                    disabled={loading}
                  >
                    Change Password
                  </Button>
                </Grid>
              </Grid>
            </Box>
          </TabPanel>

          {/* 2FA TAB */}
          <TabPanel value={tabValue} index={2}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              <Shield sx={{ mr: 1, verticalAlign: "middle" }} />
              Two-Factor Authentication
            </Typography>
            {twoFactorEnabled ? (
              <Box sx={{ maxWidth: 500 }}>
                <Alert severity="success" sx={{ mb: 2 }}>
                  2FA is currently <strong>enabled</strong> on your account
                </Alert>
                <TextField
                  label="Enter password to disable"
                  type="password"
                  fullWidth
                  value={disablePassword}
                  sx={{ mb: 2 }}
                  onChange={(e) => setDisablePassword(e.target.value)}
                />
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<Cancel />}
                  onClick={handleDisable2FA}
                  disabled={loading || !disablePassword}
                >
                  Disable 2FA
                </Button>
              </Box>
            ) : (
              <Box>
                <Typography color="text.secondary" sx={{ mb: 2 }}>
                  Add an extra layer of security by enabling two-factor
                  authentication.
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<Shield />}
                  onClick={handleSetup2FA}
                  disabled={loading}
                >
                  Setup Two-Factor Authentication
                </Button>
              </Box>
            )}
          </TabPanel>
        </CardContent>
      </Card>

      {/* QR Code Dialog */}
      <Dialog
        open={showQrDialog}
        onClose={() => setShowQrDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Setup Two-Factor Authentication</DialogTitle>
        <DialogContent>
          <Box sx={{ textAlign: "center", py: 2 }}>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Scan this QR code with Google Authenticator or any TOTP app
            </Typography>
            {qrCode && (
              <Box
                component="img"
                src={`data:image/png;base64,${qrCode}`}
                alt="QR Code"
                sx={{ width: 200, height: 200 }}
              />
            )}
            <TextField
              label="Enter verification code"
              fullWidth
              value={verifyToken}
              onChange={(e) => setVerifyToken(e.target.value)}
              sx={{ mt: 2 }}
              placeholder="000000"
              slotProps={{ htmlInput: { maxLength: 6 } }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowQrDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleVerify2FA}
            disabled={!verifyToken || loading}
          >
            Verify & Enable
          </Button>
        </DialogActions>
      </Dialog>

      {/* Backup Codes Dialog */}
      <Dialog
        open={showCodesDialog}
        onClose={() => setShowCodesDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Backup Codes</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Save these backup codes in a safe place. Each code can only be used
            once.
          </Alert>
          <Grid container spacing={1}>
            {backupCodes.map((code, i) => (
              <Grid size={{ xs: 6 }} key={i}>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 1.5,
                    textAlign: "center",
                    fontFamily: "monospace",
                    fontSize: 18,
                    letterSpacing: 2,
                  }}
                >
                  {code}
                </Paper>
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCodesDialog(false)}>Close</Button>
          <Button
            variant="contained"
            startIcon={<ContentCopy />}
            onClick={handleCopyCodes}
          >
            Copy All
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
