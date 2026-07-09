import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip, IconButton,
  Button, Select, MenuItem, FormControl, InputLabel, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, LinearProgress,
  Grid, Tooltip, Switch
} from '@mui/material';
import {
  Refresh, PlayArrow, Delete, Add, Shield
} from '@mui/icons-material';
import { ruleService } from '../../services/api/rules';
import { DetectionRule, RuleType, RuleStatus, AlertSeverity } from '../../types';

const severityColors: Record<AlertSeverity, 'error' | 'warning' | 'info' | 'success' | 'default'> = {
  critical: 'error',
  high: 'error',
  medium: 'warning',
  low: 'info',
  info: 'default',
};

export const RulesPage: React.FC = () => {
  const [rules, setRules] = useState<DetectionRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newRule, setNewRule] = useState({
    name: '', description: '', rule_type: 'threshold' as RuleType,
    severity: 'medium' as AlertSeverity, category: 'security',
    conditions: { event_type: 'FAILED_LOGIN', timeframe_minutes: 5, threshold: 5, group_by: ['source_ip'] },
    actions: { create_alert: true, alert_title: 'Rule Triggered', alert_severity: 'medium' },
    cooldown_minutes: 5, priority: 100,
  });

  useEffect(() => {
    loadRules();
  }, [typeFilter]);

  const loadRules = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (typeFilter) params.rule_type = typeFilter;
      const response = await ruleService.list(params);
      setRules(response.results);
    } catch (err) {
      console.error('Failed to load rules:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRule = async () => {
    try {
      await ruleService.create(newRule);
      setShowCreateDialog(false);
      setNewRule({
        name: '', description: '', rule_type: 'threshold',
        severity: 'medium', category: 'security',
        conditions: { event_type: 'FAILED_LOGIN', timeframe_minutes: 5, threshold: 5, group_by: ['source_ip'] },
        actions: { create_alert: true, alert_title: 'Rule Triggered', alert_severity: 'medium' },
        cooldown_minutes: 5, priority: 100,
      });
      loadRules();
    } catch (err) {
      console.error('Failed to create rule:', err);
    }
  };

  const handleTestRule = async (ruleId: string) => {
    try {
      const result = await ruleService.test(ruleId);
      alert(JSON.stringify(result, null, 2));
    } catch (err) {
      console.error('Failed to test rule:', err);
    }
  };

  const handleExecuteAll = async () => {
    try {
      const result = await ruleService.executeAll() as { rules_triggered: number; alerts_created: number };
      alert(`Rules triggered: ${result.rules_triggered}, Alerts created: ${result.alerts_created}`);
      loadRules();
    } catch (err) {
      console.error('Failed to execute rules:', err);
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (window.confirm('Delete this rule?')) {
      try {
        await ruleService.delete(ruleId);
        loadRules();
      } catch (err) {
        console.error('Failed to delete rule:', err);
      }
    }
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Detection Rules</Typography>
          <Typography color="text.secondary">Manage security detection rules</Typography>
        </Box>
        <Box>
          <Button startIcon={<PlayArrow />} onClick={handleExecuteAll} sx={{ mr: 1 }}>Execute All</Button>
          <Button variant="contained" startIcon={<Add />} onClick={() => setShowCreateDialog(true)}>Create Rule</Button>
        </Box>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 4 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Rule Type</InputLabel>
                <Select value={typeFilter} label="Rule Type" onChange={(e) => setTypeFilter(e.target.value)}>
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="threshold">Threshold</MenuItem>
                  <MenuItem value="correlation">Correlation</MenuItem>
                  <MenuItem value="pattern">Pattern</MenuItem>
                  <MenuItem value="frequency">Frequency</MenuItem>
                  <MenuItem value="blacklist">Blacklist</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Rules Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Times Triggered</TableCell>
              <TableCell>Alerts Generated</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rules.map((rule) => (
              <TableRow key={rule.id} hover>
                <TableCell>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>{rule.name}</Typography>
                </TableCell>
                <TableCell>{rule.rule_type}</TableCell>
                <TableCell>
                  <Chip label={rule.severity} size="small" color={severityColors[rule.severity]} />
                </TableCell>
                <TableCell>
                  <Chip label={rule.status} size="small" color={rule.status === 'active' ? 'success' : 'default'} />
                </TableCell>
                <TableCell>{rule.times_triggered}</TableCell>
                <TableCell>{rule.alerts_generated}</TableCell>
                <TableCell>
                  <Tooltip title="Test Rule">
                    <IconButton size="small" color="primary" onClick={() => handleTestRule(rule.id)}>
                      <PlayArrow />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton size="small" color="error" onClick={() => handleDeleteRule(rule.id)}>
                      <Delete />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Rule Dialog */}
      <Dialog open={showCreateDialog} onClose={() => setShowCreateDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Detection Rule</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Rule Name" fullWidth value={newRule.name} onChange={(e) => setNewRule({ ...newRule, name: e.target.value })} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Rule Type</InputLabel>
                  <Select value={newRule.rule_type} label="Rule Type" onChange={(e) => setNewRule({ ...newRule, rule_type: e.target.value as RuleType })}>
                    <MenuItem value="threshold">Threshold</MenuItem>
                    <MenuItem value="correlation">Correlation</MenuItem>
                    <MenuItem value="pattern">Pattern</MenuItem>
                    <MenuItem value="frequency">Frequency</MenuItem>
                    <MenuItem value="blacklist">Blacklist</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Severity</InputLabel>
                  <Select value={newRule.severity} label="Severity" onChange={(e) => setNewRule({ ...newRule, severity: e.target.value as AlertSeverity })}>
                    <MenuItem value="critical">Critical</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="low">Low</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Category" fullWidth value={newRule.category} onChange={(e) => setNewRule({ ...newRule, category: e.target.value })} />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField label="Description" fullWidth multiline rows={2} value={newRule.description} onChange={(e) => setNewRule({ ...newRule, description: e.target.value })} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Timeframe (minutes)" fullWidth type="number" value={newRule.conditions.timeframe_minutes} onChange={(e) => setNewRule({ ...newRule, conditions: { ...newRule.conditions, timeframe_minutes: parseInt(e.target.value) } })} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Threshold" fullWidth type="number" value={newRule.conditions.threshold} onChange={(e) => setNewRule({ ...newRule, conditions: { ...newRule.conditions, threshold: parseInt(e.target.value) } })} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Cooldown (minutes)" fullWidth type="number" value={newRule.cooldown_minutes} onChange={(e) => setNewRule({ ...newRule, cooldown_minutes: parseInt(e.target.value) })} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField label="Priority" fullWidth type="number" value={newRule.priority} onChange={(e) => setNewRule({ ...newRule, priority: parseInt(e.target.value) })} />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateRule} disabled={!newRule.name}>Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};