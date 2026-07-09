import React, { useState, useEffect, useCallback } from "react";
import {
  IconButton,
  Badge,
  Popover,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
  Box,
  Chip,
  Divider,
  Button,
} from "@mui/material";
import { Notifications as NotificationsIcon } from "@mui/icons-material";
import { apiClient } from "../../services/api/client";
import { useNavigate } from "react-router-dom";

interface AppNotification {
  id: string;
  title: string;
  message: string;
  priority: string;
  is_read: boolean;
  created_at: string;
  action_url: string | null;
  trigger_type: string;
}

const priorityColors: Record<string, "error" | "warning" | "info" | "success"> =
  {
    critical: "error",
    urgent: "error",
    high: "warning",
    medium: "info",
    low: "success",
  };

export const NotificationBell: React.FC = () => {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();

  const loadNotifications = useCallback(async () => {
    try {
      const response = await apiClient.get<{
        count: number;
        notifications: AppNotification[];
      }>("/notifications/unread/");
      setUnreadCount(response.count);
      setNotifications(response.notifications || []);
    } catch (err) {
      // Silently fail - notifications are non-critical
    }
  }, []);

  useEffect(() => {
    loadNotifications();
    // Poll every 30 seconds
    const interval = setInterval(loadNotifications, 30000);
    return () => clearInterval(interval);
  }, [loadNotifications]);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleMarkRead = async (id: string) => {
    try {
      await apiClient.post(`/notifications/${id}/read/`);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error("Failed to mark as read:", err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await apiClient.post("/notifications/mark-all-read/");
      setNotifications([]);
      setUnreadCount(0);
    } catch (err) {
      console.error("Failed to mark all read:", err);
    }
  };

  const handleNotificationClick = (notification: AppNotification) => {
    handleMarkRead(notification.id);
    if (notification.action_url) {
      navigate(notification.action_url);
    }
    handleClose();
  };

  const open = Boolean(anchorEl);

  return (
    <>
      <IconButton color="inherit" onClick={handleClick}>
        <Badge badgeContent={unreadCount} color="error">
          <NotificationsIcon />
        </Badge>
      </IconButton>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        slotProps={{ paper: { sx: { width: 380, maxHeight: 500 } } }}
      >
        <Box
          sx={{
            p: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            Notifications
          </Typography>
          {unreadCount > 0 && (
            <Button size="small" onClick={handleMarkAllRead}>
              Mark all read
            </Button>
          )}
        </Box>
        <Divider />

        {notifications.length === 0 ? (
          <Box sx={{ p: 3, textAlign: "center" }}>
            <Typography color="text.secondary">No new notifications</Typography>
          </Box>
        ) : (
          <List dense sx={{ maxHeight: 400, overflow: "auto" }}>
            {notifications.map((notification) => (
              <ListItem key={notification.id} disablePadding>
                <ListItemButton
                  onClick={() => handleNotificationClick(notification)}
                >
                  <ListItemText
                    primary={
                      <Box
                        sx={{ display: "flex", alignItems: "center", gap: 1 }}
                      >
                        <Typography
                          variant="body2"
                          sx={{ fontWeight: 600, flex: 1 }}
                        >
                          {notification.title}
                        </Typography>
                        <Chip
                          label={notification.priority}
                          size="small"
                          color={
                            priorityColors[notification.priority] || "default"
                          }
                          sx={{ height: 18, fontSize: "0.6rem" }}
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          noWrap
                        >
                          {notification.message?.substring(0, 100)}
                        </Typography>
                        <Typography
                          variant="caption"
                          color="text.disabled"
                          sx={{ display: "block" }}
                        >
                          {new Date(notification.created_at).toLocaleString()}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </Popover>
    </>
  );
};
