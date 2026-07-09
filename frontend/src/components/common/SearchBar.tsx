import React, { useState, useEffect, useRef } from 'react';
import {
  Box, TextField, Paper, List, ListItem, ListItemButton,
  ListItemText, ListItemIcon, Typography, Chip, CircularProgress,
  Popper, ClickAwayListener, InputAdornment, IconButton, Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  Timeline, Warning, Gavel, Computer, Description,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../services/api/client';

interface SearchResult {
  type: 'event' | 'alert' | 'incident' | 'agent' | 'log';
  id: string;
  title: string;
  subtitle: string;
  severity: string;
  timestamp: string;
}

const typeIcons: Record<string, React.ReactNode> = {
  event: <Timeline fontSize="small" />,
  alert: <Warning fontSize="small" />,
  incident: <Gavel fontSize="small" />,
  agent: <Computer fontSize="small" />,
  log: <Description fontSize="small" />,
};

const severityColors: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
  info: '#10b981',
};

export const SearchBar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }

    const timer = setTimeout(() => {
      searchQuery(query);
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  const searchQuery = async (searchQuery: string) => {
    setLoading(true);
    try {
      const response = await apiClient.post<{ results: SearchResult[] }>('/search/quick/', {
        query: searchQuery,
      });
      setResults(response.results || []);
      setOpen(true);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleResultClick = (result: SearchResult) => {
    setOpen(false);
    setQuery('');
    
    const paths: Record<string, string> = {
      event: `/events?search=${result.id}`,
      alert: `/alerts?search=${result.id}`,
      incident: `/incidents?search=${result.id}`,
      agent: `/agents?search=${result.id}`,
      log: `/events?search=${result.id}`,
    };
    
    navigate(paths[result.type] || '/dashboard');
  };

  const getTypeLabel = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  return (
    <Box ref={anchorRef} sx={{ width: '100%', maxWidth: 500 }}>
      <TextField
        fullWidth
        size="small"
        placeholder="Search... (severity:critical ip:10.0.0.1)"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                {loading ? (
                  <CircularProgress size={16} />
                ) : query ? (
                  <IconButton size="small" onClick={() => { setQuery(''); setOpen(false); }}>
                    <CloseIcon fontSize="small" />
                  </IconButton>
                ) : null}
              </InputAdornment>
            ),
          },
        }}
        sx={{
          '& .MuiOutlinedInput-root': {
            borderRadius: 3,
            backgroundColor: 'background.paper',
          },
        }}
      />

      <Popper
        open={open && results.length > 0}
        anchorEl={anchorRef.current}
        placement="bottom-start"
        style={{ zIndex: 1300, width: anchorRef.current?.offsetWidth }}
      >
        <ClickAwayListener onClickAway={() => setOpen(false)}>
          <Paper sx={{ mt: 1, maxHeight: 400, overflow: 'auto', borderRadius: 2 }}>
            <Box sx={{ px: 2, py: 1, bgcolor: 'action.hover' }}>
              <Typography variant="caption" color="text.secondary">
                {results.length} results found
              </Typography>
            </Box>
            <Divider />
            <List dense>
              {results.map((result, index) => (
                <ListItem key={`${result.type}-${result.id}-${index}`} disablePadding>
                  <ListItemButton onClick={() => handleResultClick(result)}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {typeIcons[result.type]}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {result.title}
                          </Typography>
                          <Chip
                            label={getTypeLabel(result.type)}
                            size="small"
                            sx={{ height: 18, fontSize: '0.65rem' }}
                          />
                        </Box>
                      }
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="caption" color="text.secondary" noWrap>
                            {result.subtitle}
                          </Typography>
                          {result.severity && result.severity !== 'info' && (
                            <Box
                              sx={{
                                width: 6,
                                height: 6,
                                borderRadius: '50%',
                                bgcolor: severityColors[result.severity] || '#888',
                                flexShrink: 0,
                              }}
                            />
                          )}
                        </Box>
                      }
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Paper>
        </ClickAwayListener>
      </Popper>
    </Box>
  );
};