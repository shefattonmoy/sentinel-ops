import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  IconButton,
  Paper,
  CircularProgress,
  Chip,
  Divider,
} from "@mui/material";
import { Send, Add, Delete, SmartToy, Person } from "@mui/icons-material";
import { apiClient } from "../../services/api/client";

interface Message {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

interface ChatSession {
  id: string;
  title: string;
  message_count: number;
  updated_at: string;
}

export const ChatPage: React.FC = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [suggestions] = useState([
    "Show me critical alerts from today",
    "What are the top attacking IPs?",
    "How many incidents are open?",
    "Show agent status summary",
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSessions();
  }, []);
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadSessions = async () => {
    try {
      const response = await apiClient.get<ChatSession[]>("/chat/sessions/");
      setSessions(Array.isArray(response) ? response : []);
    } catch (err) {
      console.error(err);
    }
  };

  const loadMessages = async (sessionId: string) => {
    try {
      const response = await apiClient.get<Message[]>(
        `/chat/messages/?session_id=${sessionId}`,
      );
      setMessages(Array.isArray(response) ? response : []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSend = async (text?: string) => {
    const messageText = text || input;
    if (!messageText.trim()) return;

    setLoading(true);
    setInput("");

    try {
      const response = await apiClient.post<{
        session_id: string;
        session_title: string;
      }>("/chat/send/", {
        message: messageText,
        session_id: currentSession,
      });

      if (!currentSession) {
        setCurrentSession(response.session_id);
        loadSessions();
      }

      loadMessages(response.session_id);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setCurrentSession(null);
    setMessages([]);
  };

  const handleSelectSession = (sessionId: string) => {
    setCurrentSession(sessionId);
    loadMessages(sessionId);
  };

  return (
    <Box sx={{ display: "flex", height: "calc(100vh - 100px)", gap: 2 }}>
      {/* Sidebar */}
      <Card sx={{ width: 280, flexShrink: 0 }}>
        <CardContent>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleNewChat}
            fullWidth
            sx={{ mb: 2 }}
          >
            New Chat
          </Button>
          <Divider sx={{ mb: 1 }} />
          {sessions.map((session) => (
            <Paper
              key={session.id}
              variant="outlined"
              sx={{
                p: 1,
                mb: 0.5,
                cursor: "pointer",
                bgcolor:
                  currentSession === session.id
                    ? "action.selected"
                    : "transparent",
                "&:hover": { bgcolor: "action.hover" },
              }}
              onClick={() => handleSelectSession(session.id)}
            >
              <Typography
                variant="body2"
                noWrap
                sx={{ fontWeight: 500, fontSize: "0.8rem" }}
              >
                {session.title}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {session.message_count} messages
              </Typography>
            </Paper>
          ))}
        </CardContent>
      </Card>

      {/* Chat Area */}
      <Card sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <CardContent sx={{ flex: 1, overflow: "auto", pb: 1 }}>
          {messages.length === 0 ? (
            <Box sx={{ textAlign: "center", pt: 8 }}>
              <SmartToy sx={{ fontSize: 60, color: "primary.main", mb: 2 }} />
              <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
                SentinelSense
              </Typography>
              <Typography color="text.secondary" sx={{ mb: 3 }}>
                Ask me anything about your security data
              </Typography>
              <Box
                sx={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 1,
                  justifyContent: "center",
                }}
              >
                {suggestions.map((s, i) => (
                  <Chip
                    key={i}
                    label={s}
                    onClick={() => handleSend(s)}
                    sx={{
                      cursor: "pointer",
                      "&:hover": { bgcolor: "primary.dark", color: "white" },
                    }}
                  />
                ))}
              </Box>
            </Box>
          ) : (
            messages.map((msg) => (
              <Box
                key={msg.id}
                sx={{
                  display: "flex",
                  gap: 1,
                  mb: 2,
                  justifyContent:
                    msg.role === "user" ? "flex-end" : "flex-start",
                }}
              >
                {msg.role === "assistant" && (
                  <SmartToy sx={{ color: "primary.main", mt: 0.5 }} />
                )}
                <Paper
                  sx={{
                    p: 1.5,
                    maxWidth: "70%",
                    borderRadius: 2,
                    bgcolor:
                      msg.role === "user" ? "primary.main" : "background.paper",
                    color: msg.role === "user" ? "white" : "text.primary",
                  }}
                >
                  <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
                    {msg.content}
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{ opacity: 0.7, display: "block", mt: 0.5 }}
                  >
                    {new Date(msg.created_at).toLocaleTimeString()}
                  </Typography>
                </Paper>
                {msg.role === "user" && (
                  <Person sx={{ color: "primary.main", mt: 0.5 }} />
                )}
              </Box>
            ))
          )}
          <div ref={messagesEndRef} />
        </CardContent>

        {/* Input */}
        <Box sx={{ p: 2, borderTop: "1px solid", borderColor: "divider" }}>
          <Box sx={{ display: "flex", gap: 1 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Ask about alerts, events, incidents..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSend()}
              disabled={loading}
            />
            <Button
              variant="contained"
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
            >
              {loading ? <CircularProgress size={20} /> : <Send />}
            </Button>
          </Box>
        </Box>
      </Card>
    </Box>
  );
};
