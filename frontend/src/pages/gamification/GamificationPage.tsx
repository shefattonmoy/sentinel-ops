import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, Table,
  TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, LinearProgress, Avatar, Tabs, Tab,
} from '@mui/material';
import { apiClient } from '../../services/api/client';

interface LeaderboardEntry {
  rank: number;
  user: string;
  points: number;
  level: number;
  title: string;
  achievements: number;
}

interface LeaderboardResponse {
  period: string;
  rankings: LeaderboardEntry[];
}

export const GamificationPage: React.FC = () => {
  const [profile, setProfile] = useState<any>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [badges, setBadges] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('weekly');

  useEffect(() => { loadData(); }, [period]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [profRes, leadRes, badgeRes] = await Promise.all([
        apiClient.get<any>('/gamification/profile/'),
        apiClient.get<LeaderboardResponse>(`/gamification/leaderboard/?period=${period}`),
        apiClient.get<any[]>('/gamification/badges/'),
      ]);
      setProfile(profRes);
      setLeaderboard(leadRes?.rankings || []);
      setBadges(Array.isArray(badgeRes) ? badgeRes : []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const getRankEmoji = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>Gamification</Typography>
        <Typography color="text.secondary">SOC analyst leaderboard & achievements</Typography>
      </Box>

      {/* My Profile Card - Fixed Grid */}
      {profile && (
        <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)', color: 'white' }}>
          <CardContent>
            <Grid container spacing={3} sx={{ alignItems: 'center' }}>
              <Grid size={{ xs: 12, md: 4 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Avatar sx={{ width: 80, height: 80, mx: 'auto', mb: 1, bgcolor: 'rgba(255,255,255,0.3)', fontSize: 32 }}>
                    {profile.username?.[0]?.toUpperCase()}
                  </Avatar>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>{profile.username}</Typography>
                  <Chip label={profile.title || 'Junior Analyst'} size="small"
                    sx={{ bgcolor: 'rgba(255,255,255,0.3)', color: 'white', mt: 0.5 }} />
                </Box>
              </Grid>
              <Grid size={{ xs: 6, md: 2 }}>
                <Typography variant="h3" sx={{ fontWeight: 800 }}>{profile.total_points || 0}</Typography>
                <Typography variant="caption">Total Points</Typography>
              </Grid>
              <Grid size={{ xs: 6, md: 2 }}>
                <Typography variant="h3" sx={{ fontWeight: 800 }}>{profile.level || 1}</Typography>
                <Typography variant="caption">Level</Typography>
              </Grid>
              <Grid size={{ xs: 6, md: 2 }}>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>{profile.alerts_resolved || 0}</Typography>
                <Typography variant="caption">Alerts Resolved</Typography>
              </Grid>
              <Grid size={{ xs: 6, md: 2 }}>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>{profile.incidents_closed || 0}</Typography>
                <Typography variant="caption">Incidents Closed</Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      <Grid container spacing={3}>
        {/* Leaderboard */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>🏆 Leaderboard</Typography>
                <Tabs value={period} onChange={(_, v) => setPeriod(v)}>
                  <Tab label="Weekly" value="weekly" />
                  <Tab label="Monthly" value="monthly" />
                </Tabs>
              </Box>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Rank</TableCell>
                      <TableCell>Analyst</TableCell>
                      <TableCell>Points</TableCell>
                      <TableCell>Level</TableCell>
                      <TableCell>Title</TableCell>
                      <TableCell>Achievements</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {leaderboard.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} align="center">
                          <Typography color="text.secondary" sx={{ py: 2 }}>No data yet</Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      leaderboard.map((entry) => (
                        <TableRow key={entry.rank} hover sx={{
                          bgcolor: entry.rank <= 3 ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                        }}>
                          <TableCell>
                            <Typography variant="h6">{getRankEmoji(entry.rank)}</Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: entry.rank <= 3 ? 700 : 500 }}>
                              {entry.user}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label={`${entry.points} pts`} size="small" color="primary" />
                          </TableCell>
                          <TableCell>{entry.level}</TableCell>
                          <TableCell>{entry.title}</TableCell>
                          <TableCell>{entry.achievements}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Badges */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>🏅 Badges</Typography>
              <Grid container spacing={1}>
                {badges.map((badge, i) => (
                  <Grid size={{ xs: 6 }} key={i}>
                    <Paper
                      variant="outlined"
                      sx={{
                        p: 1.5, textAlign: 'center',
                        opacity: badge.earned ? 1 : 0.4,
                        borderColor: badge.earned ? 'primary.main' : 'divider',
                      }}
                    >
                      <Typography variant="h4">{badge.icon}</Typography>
                      <Typography variant="caption" sx={{ fontWeight: 600, display: 'block' }}>
                        {badge.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                        {badge.description}
                      </Typography>
                      {badge.earned && (
                        <Chip label="Earned" size="small" color="success" sx={{ mt: 0.5, height: 18, fontSize: '0.6rem' }} />
                      )}
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};