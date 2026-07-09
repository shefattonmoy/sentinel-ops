import React, { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Menu,
  MenuItem,
  useTheme,
  Chip,
  Collapse,
} from "@mui/material";
import {
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  Dashboard as DashboardIcon,
  Computer as ComputerIcon,
  Timeline as TimelineIcon,
  Warning as WarningIcon,
  Shield as ShieldIcon,
  Gavel as GavelIcon,
  Assessment as AssessmentIcon,
  History as HistoryIcon,
  Person as PersonIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  Logout as LogoutIcon,
  Settings as SettingsIcon,
  Security as SecurityIcon,
  PlayCircle as PlayCircleIcon,
  Schedule as ScheduleIcon,
  ExpandLess,
  ExpandMore,
  BugReport as BugReportIcon,
  Search as SearchIcon,
  Hub as HubIcon,
  Storage as StorageIcon,
  SmartToy as SmartToyIcon,
  Analytics as AnalyticsIcon,
  EmojiEvents as EmojiEventsIcon,
} from "@mui/icons-material";
import { useAuth } from "../../context/AuthContext";
import { useThemeMode } from "../../context/ThemeContext";
import { SearchBar } from "../common/SearchBar";
import { NotificationBell } from "../common/NotificationBell";
import { SessionTimeout } from "../common/SessionTimeout";

const drawerWidth = 240;

interface MenuGroup {
  text: string;
  icon: React.ReactNode;
  children?: { text: string; icon: React.ReactNode; path: string }[];
  path?: string;
}

const menuGroups: MenuGroup[] = [
  {
    text: "Dashboard",
    icon: <DashboardIcon sx={{ fontSize: 20 }} />,
    path: "/dashboard",
  },
  {
    text: "Monitoring",
    icon: <ComputerIcon sx={{ fontSize: 20 }} />,
    children: [
      {
        text: "Agents",
        icon: <StorageIcon sx={{ fontSize: 18 }} />,
        path: "/agents",
      },
      {
        text: "Events",
        icon: <TimelineIcon sx={{ fontSize: 18 }} />,
        path: "/events",
      },
      {
        text: "Topology",
        icon: <HubIcon sx={{ fontSize: 18 }} />,
        path: "/topology",
      },
    ],
  },
  {
    text: "Threats & Attacks",
    icon: <SecurityIcon sx={{ fontSize: 20 }} />,
    children: [
      {
        text: "Threat Intel",
        icon: <SecurityIcon sx={{ fontSize: 18 }} />,
        path: "/threat-intel",
      },
      {
        text: "MITRE Attack",
        icon: <ShieldIcon sx={{ fontSize: 18 }} />,
        path: "/mitre",
      },
      {
        text: "Honeypots",
        icon: <BugReportIcon sx={{ fontSize: 18 }} />,
        path: "/honeypot",
      },
    ],
  },
  {
    text: "Detection & Response",
    icon: <WarningIcon sx={{ fontSize: 20 }} />,
    children: [
      {
        text: "Alerts",
        icon: <WarningIcon sx={{ fontSize: 18 }} />,
        path: "/alerts",
      },
      {
        text: "Rules",
        icon: <ShieldIcon sx={{ fontSize: 18 }} />,
        path: "/rules",
      },
      {
        text: "Incidents",
        icon: <GavelIcon sx={{ fontSize: 18 }} />,
        path: "/incidents",
      },
      {
        text: "Playbooks",
        icon: <PlayCircleIcon sx={{ fontSize: 18 }} />,
        path: "/playbooks",
      },
    ],
  },
  {
    text: "Analysis",
    icon: <SearchIcon sx={{ fontSize: 20 }} />,
    children: [
      {
        text: "Forensics",
        icon: <SearchIcon sx={{ fontSize: 18 }} />,
        path: "/forensics",
      },
      {
        text: "Risks",
        icon: <AssessmentIcon sx={{ fontSize: 18 }} />,
        path: "/risks",
      },
      {
        text: "Audit Log",
        icon: <HistoryIcon sx={{ fontSize: 18 }} />,
        path: "/audit",
      },
    ],
  },
  {
    text: "Reports & Compliance",
    icon: <AssessmentIcon sx={{ fontSize: 20 }} />,
    children: [
      {
        text: "Reports",
        icon: <AssessmentIcon sx={{ fontSize: 18 }} />,
        path: "/reports",
      },
      {
        text: "Compliance",
        icon: <GavelIcon sx={{ fontSize: 18 }} />,
        path: "/compliance",
      },
      {
        text: "Scheduler",
        icon: <ScheduleIcon sx={{ fontSize: 18 }} />,
        path: "/scheduler",
      },
      {
        text: "AI Assistant",
        icon: <SmartToyIcon sx={{ fontSize: 18 }} />,
        path: "/chat",
      },
      {
        text: "Analytics",
        icon: <AnalyticsIcon sx={{ fontSize: 18 }} />,
        path: "/analytics",
      },
      {
        text: "Gamification",
        icon: <EmojiEventsIcon sx={{ fontSize: 18 }} />,
        path: "/gamification",
      },
    ],
  },
];

export const MainLayout: React.FC = () => {
  const [open, setOpen] = useState(true);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(
    {
      Monitoring: true,
      "Threats & Attacks": false,
      "Detection & Response": true,
      Analysis: false,
      "Reports & Compliance": false,
    },
  );

  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { toggleColorMode, mode } = useThemeMode();

  const handleDrawerToggle = () => setOpen(!open);
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) =>
    setAnchorEl(event.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  const handleNavigate = (path: string) => {
    navigate(path);
    handleMenuClose();
  };

  const handleLogout = () => {
    handleMenuClose();
    logout();
    navigate("/login");
  };

  const toggleGroup = (groupName: string) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [groupName]: !prev[groupName],
    }));
  };

  const isGroupActive = (group: MenuGroup) => {
    if (group.path) return location.pathname.startsWith(group.path);
    if (group.children) {
      return group.children.some((child) =>
        location.pathname.startsWith(child.path),
      );
    }
    return false;
  };

  const isChildActive = (path: string) => location.pathname.startsWith(path);

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      {/* ============ APP BAR ============ */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: theme.zIndex.drawer + 1,
          background: theme.palette.background.paper,
          color: theme.palette.text.primary,
          boxShadow: "none",
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Toolbar sx={{ gap: 1 }}>
          <IconButton color="inherit" onClick={handleDrawerToggle} edge="start">
            {open ? <ChevronLeftIcon /> : <MenuIcon />}
          </IconButton>

          <Typography
            variant="h6"
            noWrap
            sx={{
              fontWeight: 700,
              cursor: "pointer",
              display: { xs: "none", md: "block" },
              mr: 2,
            }}
            onClick={() => navigate("/dashboard")}
          >
            <Box component="span" sx={{ color: theme.palette.primary.main }}>
              Sentinel
            </Box>
            Ops
          </Typography>

          <Box
            sx={{ flex: 1, display: "flex", justifyContent: "center", mx: 2 }}
          >
            <SearchBar />
          </Box>

          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <NotificationBell />
            <IconButton onClick={toggleColorMode} color="inherit">
              {mode === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>

            <Box
              onClick={handleMenuOpen}
              sx={{
                display: "flex",
                alignItems: "center",
                cursor: "pointer",
                "&:hover": { opacity: 0.8 },
                ml: 1,
                borderRadius: 2,
                px: 1,
                py: 0.5,
              }}
            >
              <Avatar
                sx={{
                  width: 32,
                  height: 32,
                  bgcolor: theme.palette.primary.main,
                  fontSize: "0.8rem",
                }}
              >
                {user?.username?.[0]?.toUpperCase() || "U"}
              </Avatar>
              <Box sx={{ display: { xs: "none", md: "block" }, ml: 1 }}>
                <Typography
                  variant="body2"
                  sx={{ fontWeight: 600, lineHeight: 1.2, fontSize: "0.8rem" }}
                >
                  {user?.username || "User"}
                </Typography>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ lineHeight: 1, fontSize: "0.65rem" }}
                >
                  {user?.role || "Viewer"}
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* User Dropdown */}
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
            transformOrigin={{ vertical: "top", horizontal: "right" }}
            slotProps={{ paper: { sx: { minWidth: 200, mt: 1 } } }}
          >
            <Box sx={{ px: 2, py: 1 }}>
              <Typography
                variant="subtitle2"
                sx={{ fontWeight: 600, fontSize: "0.85rem" }}
              >
                {user?.username}
              </Typography>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ fontSize: "0.7rem" }}
              >
                {user?.email || "No email"}
              </Typography>
              <Box sx={{ mt: 0.5 }}>
                <Chip
                  label={user?.role}
                  size="small"
                  sx={{ fontSize: "0.6rem", height: 18 }}
                />
              </Box>
            </Box>
            <Divider />
            <MenuItem
              onClick={() => handleNavigate("/profile")}
              sx={{ fontSize: "0.85rem", py: 0.8 }}
            >
              <PersonIcon sx={{ mr: 1 }} fontSize="small" /> Profile
            </MenuItem>
            <MenuItem
              onClick={() => handleNavigate("/settings")}
              sx={{ fontSize: "0.85rem", py: 0.8 }}
            >
              <SettingsIcon sx={{ mr: 1 }} fontSize="small" /> Settings
            </MenuItem>
            <Divider />
            <MenuItem
              onClick={handleLogout}
              sx={{ fontSize: "0.85rem", py: 0.8 }}
            >
              <LogoutIcon sx={{ mr: 1 }} fontSize="small" /> Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* ============ SIDEBAR DRAWER ============ */}
      <Drawer
        variant="permanent"
        open={open}
        sx={{
          width: open ? drawerWidth : theme.spacing(7),
          flexShrink: 0,
          whiteSpace: "nowrap",
          "& .MuiDrawer-paper": {
            width: open ? drawerWidth : theme.spacing(7),
            transition: theme.transitions.create("width", {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
            overflowX: "hidden",
            overflowY: "auto",
            borderRight: `1px solid ${theme.palette.divider}`,
            background: theme.palette.background.paper,
            display: "flex",
            flexDirection: "column",
          },
        }}
      >
        <Toolbar />

        {/* Menu Groups */}
        <List sx={{ px: 1, flex: 1, overflowY: "auto", py: 0.5 }}>
          {menuGroups.map((group) => {
            const isActive = isGroupActive(group);
            const isExpanded = expandedGroups[group.text] ?? false;

            // Single item (no children)
            if (!group.children && group.path) {
              return (
                <ListItem key={group.text} disablePadding sx={{ mb: 0.25 }}>
                  <ListItemButton
                    onClick={() => navigate(group.path!)}
                    sx={{
                      minHeight: 38,
                      justifyContent: open ? "initial" : "center",
                      px: 2,
                      borderRadius: 1.5,
                      bgcolor: isActive ? "primary.main" : "transparent",
                      color: isActive ? "white" : "inherit",
                      "&:hover": {
                        bgcolor: isActive ? "primary.dark" : "action.hover",
                      },
                      transition: "all 0.15s ease",
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: 0,
                        mr: open ? 1.5 : "auto",
                        justifyContent: "center",
                        color: isActive ? "white" : "inherit",
                      }}
                    >
                      {group.icon}
                    </ListItemIcon>
                    {open && (
                      <ListItemText
                        primary={group.text}
                        slotProps={{
                          primary: {
                            variant: "body2" as const,
                            sx: {
                              fontSize: "0.82rem",
                              fontWeight: isActive ? 600 : 400,
                            },
                          },
                        }}
                      />
                    )}
                  </ListItemButton>
                </ListItem>
              );
            }

            // Group with children
            return (
              <Box key={group.text}>
                {/* Group Header */}
                <ListItem disablePadding sx={{ mb: 0.25 }}>
                  <ListItemButton
                    onClick={() => toggleGroup(group.text)}
                    sx={{
                      minHeight: 38,
                      justifyContent: open ? "initial" : "center",
                      px: 2,
                      borderRadius: 1.5,
                      bgcolor:
                        isActive && !isExpanded
                          ? "rgba(99, 102, 241, 0.15)"
                          : "transparent",
                      color: isActive ? "primary.main" : "inherit",
                      "&:hover": { bgcolor: "action.hover" },
                      transition: "all 0.15s ease",
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: 0,
                        mr: open ? 1.5 : "auto",
                        justifyContent: "center",
                        color: isActive ? "primary.main" : "inherit",
                      }}
                    >
                      {group.icon}
                    </ListItemIcon>
                    {open && (
                      <>
                        <ListItemText
                          primary={group.text}
                          slotProps={{
                            primary: {
                              variant: "body2",
                              sx: {
                                fontSize: "0.8rem",
                                fontWeight: 600,
                              },
                            },
                          }}
                        />
                        {isExpanded ? (
                          <ExpandLess sx={{ fontSize: 16 }} />
                        ) : (
                          <ExpandMore sx={{ fontSize: 16 }} />
                        )}
                      </>
                    )}
                  </ListItemButton>
                </ListItem>

                {/* Sub-items */}
                {open && (
                  <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                    <List component="div" disablePadding>
                      {group.children?.map((child) => {
                        const childActive = isChildActive(child.path);
                        return (
                          <ListItem
                            key={child.text}
                            disablePadding
                            sx={{ mb: 0.25 }}
                          >
                            <ListItemButton
                              onClick={() => navigate(child.path)}
                              sx={{
                                minHeight: 34,
                                pl: 5,
                                pr: 2,
                                borderRadius: 1.5,
                                ml: 1,
                                bgcolor: childActive
                                  ? "primary.main"
                                  : "transparent",
                                color: childActive ? "white" : "inherit",
                                "&:hover": {
                                  bgcolor: childActive
                                    ? "primary.dark"
                                    : "action.hover",
                                },
                                transition: "all 0.15s ease",
                              }}
                            >
                              <ListItemIcon
                                sx={{
                                  minWidth: 0,
                                  mr: 1.5,
                                  color: childActive ? "white" : "inherit",
                                }}
                              >
                                {child.icon}
                              </ListItemIcon>
                              <ListItemText
                                primary={child.text}
                                slotProps={{
                                  primary: {
                                    variant: "body2",
                                    sx: {
                                      fontSize: "0.78rem",
                                      fontWeight: childActive ? 500 : 400,
                                    },
                                  },
                                }}
                              />
                            </ListItemButton>
                          </ListItem>
                        );
                      })}
                    </List>
                  </Collapse>
                )}
              </Box>
            );
          })}
        </List>

        {/* Bottom - Profile & Settings */}
        {open && (
          <Box
            sx={{ borderTop: `1px solid ${theme.palette.divider}`, py: 0.5 }}
          >
            <ListItem disablePadding>
              <ListItemButton
                onClick={() => navigate("/profile")}
                sx={{
                  minHeight: 38,
                  px: 2,
                  borderRadius: 1.5,
                  mx: 1,
                  bgcolor:
                    location.pathname === "/profile"
                      ? "primary.main"
                      : "transparent",
                  color: location.pathname === "/profile" ? "white" : "inherit",
                  "&:hover": {
                    bgcolor:
                      location.pathname === "/profile"
                        ? "primary.dark"
                        : "action.hover",
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    mr: 1.5,
                    color:
                      location.pathname === "/profile" ? "white" : "inherit",
                  }}
                >
                  <PersonIcon sx={{ fontSize: 20 }} />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" sx={{ fontSize: "0.82rem" }}>
                      Profile
                    </Typography>
                  }
                />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton
                onClick={() => navigate("/settings")}
                sx={{
                  minHeight: 38,
                  px: 2,
                  borderRadius: 1.5,
                  mx: 1,
                  bgcolor:
                    location.pathname === "/settings"
                      ? "primary.main"
                      : "transparent",
                  color:
                    location.pathname === "/settings" ? "white" : "inherit",
                  "&:hover": {
                    bgcolor:
                      location.pathname === "/settings"
                        ? "primary.dark"
                        : "action.hover",
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    mr: 1.5,
                    color:
                      location.pathname === "/settings" ? "white" : "inherit",
                  }}
                >
                  <SettingsIcon sx={{ fontSize: 20 }} />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" sx={{ fontSize: "0.82rem" }}>
                      Settings
                    </Typography>
                  }
                />
              </ListItemButton>
            </ListItem>
          </Box>
        )}

        {/* Footer */}
        {open && (
          <Box sx={{ px: 1.5, py: 1 }}>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontSize: "0.65rem" }}
            >
              © SentinelOps v1.0.0
            </Typography>
          </Box>
        )}
      </Drawer>

      {/* ============ MAIN CONTENT ============ */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          backgroundColor: theme.palette.background.default,
          minHeight: "100vh",
          width: "100%",
          overflow: "auto",
        }}
      >
        <Toolbar />
        <Outlet />
        <SessionTimeout />
      </Box>
    </Box>
  );
};
