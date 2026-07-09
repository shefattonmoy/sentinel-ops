import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  LinearProgress,
  Avatar,
  keyframes,
} from "@mui/material";
import {
  Timer,
  Security,
  HourglassEmpty,
  Warning,
  TouchApp,
} from "@mui/icons-material";
import { useAuth } from "../../context/AuthContext";

const WARNING_BEFORE = 2 * 60 * 1000; // 2 minutes
const INITIAL_SHOWN_KEY = "sentinel_session_initial_shown";

const pulse = keyframes`
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
`;

const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
`;

const bounce = keyframes`
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
`;

const rotate = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

const shimmer = keyframes`
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
`;

export const SessionTimeout: React.FC = () => {
  const { logout, isAuthenticated, user } = useAuth();
  const [timeoutMinutes, setTimeoutMinutes] = useState(30);
  const [showWarning, setShowWarning] = useState(false);
  const [showInitialWarning, setShowInitialWarning] = useState(false);
  const [countdown, setCountdown] = useState(WARNING_BEFORE / 1000);
  const [progress, setProgress] = useState(100);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const countdownRef = useRef<NodeJS.Timeout | null>(null);
  const lastActivityRef = useRef<number>(Date.now());

  // Load timeout setting
  useEffect(() => {
    const saved = localStorage.getItem("session_timeout");
    if (saved) setTimeoutMinutes(parseInt(saved, 10));
  }, []);

  // Show initial dialog ONLY ONCE per browser session (not on every refresh)
  useEffect(() => {
    if (isAuthenticated) {
      const alreadyShown = sessionStorage.getItem(INITIAL_SHOWN_KEY);
      if (!alreadyShown) {
        const timer = setTimeout(() => {
          setShowInitialWarning(true);
          sessionStorage.setItem(INITIAL_SHOWN_KEY, "true");
        }, 1000);
        return () => clearTimeout(timer);
      }
    }
  }, [isAuthenticated]);

  const resetTimer = useCallback(() => {
    lastActivityRef.current = Date.now();
    setShowWarning(false);
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
  }, []);

  // Track user activity
  useEffect(() => {
    const events = [
      "mousedown",
      "keydown",
      "scroll",
      "touchstart",
      "click",
      "mousemove",
    ];
    const handleActivity = () => resetTimer();
    events.forEach((event) => window.addEventListener(event, handleActivity));
    return () =>
      events.forEach((event) =>
        window.removeEventListener(event, handleActivity),
      );
  }, [resetTimer]);

  // Main session check timer
  useEffect(() => {
    if (!isAuthenticated) return;

    const timeoutMs = timeoutMinutes * 60 * 1000;
    const warningTime = timeoutMs - WARNING_BEFORE;

    timerRef.current = setInterval(() => {
      const now = Date.now();
      const elapsed = now - lastActivityRef.current;

      if (elapsed >= timeoutMs) {
        handleLogout();
      } else if (elapsed >= warningTime && !showWarning) {
        setShowWarning(true);
        const remaining = Math.ceil((timeoutMs - elapsed) / 1000);
        setCountdown(remaining);
        setProgress((remaining / (WARNING_BEFORE / 1000)) * 100);

        countdownRef.current = setInterval(() => {
          setCountdown((prev) => {
            const newCount = prev - 1;
            setProgress((newCount / (WARNING_BEFORE / 1000)) * 100);
            if (newCount <= 0) {
              handleLogout();
              return 0;
            }
            return newCount;
          });
        }, 1000);
      }
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, [timeoutMinutes, showWarning, isAuthenticated]);

  const handleContinue = () => {
    resetTimer();
    setShowInitialWarning(false);
  };

  const handleLogout = () => {
    if (countdownRef.current) clearInterval(countdownRef.current);
    if (timerRef.current) clearInterval(timerRef.current);
    // Clear the initial shown flag on logout
    sessionStorage.removeItem(INITIAL_SHOWN_KEY);
    logout();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const getCountdownColor = () => {
    if (countdown <= 30) return "#ef4444";
    if (countdown <= 60) return "#f97316";
    return "#eab308";
  };

  return (
    <>
      {/* ============ INITIAL SESSION DIALOG ============ */}
      <Dialog
        open={showInitialWarning}
        onClose={handleContinue}
        maxWidth="sm"
        fullWidth
        slotProps={{
          paper: {
            sx: {
              borderRadius: 3,
              background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
              border: "1px solid rgba(99, 102, 241, 0.3)",
              overflow: "hidden",
            },
          },
        }}
      >
        <Box
          sx={{
            background:
              "linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)",
            py: 3,
            textAlign: "center",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <Box
            sx={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              opacity: 0.1,
              background:
                "radial-gradient(circle at 20% 50%, white 1px, transparent 1px), radial-gradient(circle at 80% 50%, white 1px, transparent 1px)",
              backgroundSize: "40px 40px",
            }}
          />
          <Avatar
            sx={{
              width: 70,
              height: 70,
              mx: "auto",
              mb: 1.5,
              bgcolor: "rgba(255,255,255,0.2)",
              backdropFilter: "blur(10px)",
              animation: `${pulse} 2s infinite`,
              border: "3px solid rgba(255,255,255,0.4)",
            }}
          >
            <Security sx={{ fontSize: 36, color: "white" }} />
          </Avatar>
          <Typography
            variant="h5"
            sx={{ color: "white", fontWeight: 700, position: "relative" }}
          >
            Welcome, {user?.username || "User"}! 👋
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: "rgba(255,255,255,0.8)",
              position: "relative",
              mt: 0.5,
            }}
          >
            Your secure session is now active
          </Typography>
        </Box>

        <DialogContent sx={{ px: 4, py: 3 }}>
          <Box sx={{ display: "flex", gap: 2, mb: 3 }}>
            <Box
              sx={{
                flex: 1,
                p: 2,
                borderRadius: 2,
                background: "rgba(99, 102, 241, 0.1)",
                border: "1px solid rgba(99, 102, 241, 0.2)",
                textAlign: "center",
              }}
            >
              <HourglassEmpty sx={{ color: "#6366f1", mb: 1, fontSize: 28 }} />
              <Typography
                variant="h6"
                sx={{ fontWeight: 700, color: "#6366f1" }}
              >
                {timeoutMinutes} min
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Session Duration
              </Typography>
            </Box>
            <Box
              sx={{
                flex: 1,
                p: 2,
                borderRadius: 2,
                background: "rgba(234, 179, 8, 0.1)",
                border: "1px solid rgba(234, 179, 8, 0.2)",
                textAlign: "center",
              }}
            >
              <Warning sx={{ color: "#eab308", mb: 1, fontSize: 28 }} />
              <Typography
                variant="h6"
                sx={{ fontWeight: 700, color: "#eab308" }}
              >
                2 min
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Warning Before
              </Typography>
            </Box>
            <Box
              sx={{
                flex: 1,
                p: 2,
                borderRadius: 2,
                background: "rgba(16, 185, 129, 0.1)",
                border: "1px solid rgba(16, 185, 129, 0.2)",
                textAlign: "center",
              }}
            >
              <TouchApp sx={{ color: "#10b981", mb: 1, fontSize: 28 }} />
              <Typography
                variant="h6"
                sx={{ fontWeight: 700, color: "#10b981" }}
              >
                Auto
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Activity Detection
              </Typography>
            </Box>
          </Box>
          <Typography variant="body2" color="text.secondary" align="center">
            ⚡ Your session will automatically expire after{" "}
            <strong style={{ color: "#6366f1" }}>
              {timeoutMinutes} minutes
            </strong>{" "}
            of inactivity. A warning will notify you 2 minutes before
            expiration.
          </Typography>
        </DialogContent>

        <DialogActions sx={{ justifyContent: "center", pb: 3, px: 4 }}>
          <Button
            variant="contained"
            onClick={handleContinue}
            size="large"
            autoFocus
            sx={{
              minWidth: 200,
              py: 1.2,
              borderRadius: 2,
              fontSize: "1rem",
              fontWeight: 600,
              background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
              "&:hover": {
                background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
              },
              animation: `${fadeIn} 0.5s ease-out`,
            }}
          >
            Start Session
          </Button>
        </DialogActions>
      </Dialog>

      {/* ============ SESSION EXPIRY WARNING DIALOG ============ */}
      <Dialog
        open={showWarning}
        onClose={handleContinue}
        maxWidth="sm"
        fullWidth
        slotProps={{
          paper: {
            sx: {
              borderRadius: 3,
              background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
              border:
                countdown <= 30
                  ? "1px solid rgba(239, 68, 68, 0.5)"
                  : "1px solid rgba(234, 179, 8, 0.5)",
              overflow: "hidden",
            },
          },
        }}
      >
        <Box
          sx={{
            background:
              countdown <= 30
                ? "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)"
                : countdown <= 60
                  ? "linear-gradient(135deg, #f97316 0%, #ea580c 100%)"
                  : "linear-gradient(135deg, #eab308 0%, #ca8a04 100%)",
            py: 3,
            textAlign: "center",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <Box
            sx={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              opacity: 0.15,
              background:
                "radial-gradient(circle at 30% 70%, white 2px, transparent 2px), radial-gradient(circle at 70% 30%, white 2px, transparent 2px)",
              backgroundSize: "30px 30px",
              animation: `${shimmer} 3s linear infinite`,
            }}
          />
          <Avatar
            sx={{
              width: 80,
              height: 80,
              mx: "auto",
              mb: 1.5,
              bgcolor: "rgba(255,255,255,0.2)",
              backdropFilter: "blur(10px)",
              animation: `${countdown <= 30 ? bounce : pulse} ${countdown <= 30 ? "0.5s" : "1.5s"} infinite`,
              border: "3px solid rgba(255,255,255,0.4)",
            }}
          >
            <Timer sx={{ fontSize: 42, color: "white" }} />
          </Avatar>
          <Typography
            variant="h5"
            sx={{ color: "white", fontWeight: 700, position: "relative" }}
          >
            Session Expiring!
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: "rgba(255,255,255,0.85)",
              position: "relative",
              mt: 0.5,
            }}
          >
            Your session will end soon due to inactivity
          </Typography>
        </Box>

        <DialogContent sx={{ px: 4, py: 3 }}>
          <Box sx={{ textAlign: "center", mb: 3 }}>
            <Box
              sx={{
                width: 140,
                height: 140,
                mx: "auto",
                mb: 2,
                borderRadius: "50%",
                border: `4px solid ${getCountdownColor()}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                position: "relative",
                animation: `${pulse} 1s infinite`,
                boxShadow: `0 0 30px ${getCountdownColor()}40`,
              }}
            >
              <Box
                sx={{
                  position: "absolute",
                  top: -4,
                  left: -4,
                  right: -4,
                  bottom: -4,
                  borderRadius: "50%",
                  border: "4px solid transparent",
                  borderTopColor: getCountdownColor(),
                  animation: `${rotate} ${countdown <= 30 ? "1s" : "2s"} linear infinite`,
                }}
              />
              <Box sx={{ textAlign: "center" }}>
                <Typography
                  variant="h3"
                  sx={{
                    fontWeight: 800,
                    color: getCountdownColor(),
                    lineHeight: 1,
                    fontFamily: "monospace",
                  }}
                >
                  {formatTime(countdown)}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{ color: getCountdownColor(), fontWeight: 500 }}
                >
                  remaining
                </Typography>
              </Box>
            </Box>
          </Box>

          <Box sx={{ mb: 2 }}>
            <Box
              sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}
            >
              <Typography variant="caption" color="text.secondary">
                Session Time
              </Typography>
              <Typography
                variant="caption"
                sx={{ color: getCountdownColor(), fontWeight: 600 }}
              >
                {Math.ceil(progress)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{
                height: 10,
                borderRadius: 5,
                bgcolor: "rgba(255,255,255,0.1)",
                "& .MuiLinearProgress-bar": {
                  borderRadius: 5,
                  background:
                    countdown <= 30
                      ? "linear-gradient(90deg, #ef4444, #dc2626)"
                      : countdown <= 60
                        ? "linear-gradient(90deg, #f97316, #ea580c)"
                        : "linear-gradient(90deg, #eab308, #ca8a04)",
                },
              }}
            />
          </Box>

          <Box
            sx={{
              p: 2,
              borderRadius: 2,
              textAlign: "center",
              background: "rgba(255,255,255,0.05)",
              border: "1px solid rgba(255,255,255,0.1)",
            }}
          >
            <Typography variant="body2" color="text.secondary">
              {countdown <= 30
                ? '🚨 Your session is about to end! Click "Continue Session" to stay logged in.'
                : "⏰ Your session will expire automatically. Would you like to continue?"}
            </Typography>
          </Box>
        </DialogContent>

        <DialogActions sx={{ justifyContent: "center", pb: 3, px: 4, gap: 2 }}>
          <Button
            variant="outlined"
            color="error"
            onClick={handleLogout}
            size="large"
            sx={{
              minWidth: 130,
              py: 1.2,
              borderRadius: 2,
              borderWidth: 2,
              fontWeight: 600,
              "&:hover": { borderWidth: 2 },
            }}
          >
            Logout Now
          </Button>
          <Button
            variant="contained"
            onClick={handleContinue}
            size="large"
            autoFocus
            sx={{
              minWidth: 200,
              py: 1.2,
              borderRadius: 2,
              fontSize: "1rem",
              fontWeight: 600,
              background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
              "&:hover": {
                background: "linear-gradient(135deg, #059669 0%, #047857 100%)",
              },
              animation: `${fadeIn} 0.5s ease-out`,
            }}
          >
            Continue Session
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};
