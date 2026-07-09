import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Button, Chip, LinearProgress,
  Dialog, DialogTitle, DialogContent, DialogActions, Grid,
} from '@mui/material';
import { Refresh, TravelExplore } from '@mui/icons-material';
import { apiClient } from '../../services/api/client';

interface TopologyNode {
  id: string; name: string; type: string; hostname: string; ip: string | null;
  status: string; x: number; y: number; cpu_usage: number | null;
  memory_usage: number | null; alert_count: number; risk_score: number;
}

interface TopologyEdge {
  id: string; source: string; target: string; type: string;
  protocol: string; port: number | null; status: string;
  request_count: number; error_count: number;
}

interface TopologyData {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}

export const TopologyPage: React.FC = () => {
  const [nodes, setNodes] = useState<TopologyNode[]>([]);
  const [edges, setEdges] = useState<TopologyEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [openDialog, setOpenDialog] = useState(false);

  useEffect(() => { loadTopology(); }, []);

  const loadTopology = async () => {
    setLoading(true);
    try {
      // The API returns { nodes: [...], edges: [...] } directly
      const data = await apiClient.get<TopologyData>('/topology/map/');
      console.log('Topology data:', data); // Debug
      setNodes(Array.isArray(data?.nodes) ? data.nodes : []);
      setEdges(Array.isArray(data?.edges) ? data.edges : []);
    } catch (err) { 
      console.error('Failed to load topology:', err);
      setNodes([]);
      setEdges([]);
    } finally { 
      setLoading(false); 
    }
  };

  const handleDiscover = async () => {
    setDiscovering(true);
    try {
      await apiClient.post('/topology/discover/');
      await loadTopology();
    } catch (err) { 
      console.error('Discovery failed:', err); 
    } finally { 
      setDiscovering(false); 
    }
  };

  const handleNodeClick = async (nodeId: string) => {
    try {
      const data = await apiClient.get<any>(`/topology/node-detail/?id=${nodeId}`);
      setSelectedNode(data);
      setOpenDialog(true);
    } catch (err) { 
      console.error('Failed to load node details:', err); 
    }
  };

  const getNodeColor = (type: string, status: string): string => {
    if (status !== 'online') return '#ef4444';
    const colors: Record<string, string> = {
      server: '#3b82f6', container: '#10b981', service: '#8b5cf6',
      database: '#f59e0b', load_balancer: '#ec4899', firewall: '#ef4444', external: '#6b7280',
    };
    return colors[type] || '#6366f1';
  };

  const getEdgeColor = (status: string): string => {
    if (status === 'healthy') return '#10b981';
    if (status === 'degraded') return '#f59e0b';
    return '#ef4444';
  };

  if (loading) return <LinearProgress />;

  const onlineCount = nodes.filter(n => n.status === 'online').length;
  const offlineCount = nodes.filter(n => n.status !== 'online').length;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Network Topology</Typography>
          <Typography color="text.secondary">Auto-discovered network map</Typography>
        </Box>
        <Box>
          <Button startIcon={<Refresh />} onClick={loadTopology} sx={{ mr: 1 }}>Refresh</Button>
          <Button variant="contained" startIcon={<TravelExplore />} onClick={handleDiscover} disabled={discovering}>
            {discovering ? 'Discovering...' : 'Discover Network'}
          </Button>
        </Box>
      </Box>

      {/* Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h5" sx={{ fontWeight: 700 }}>{nodes.length}</Typography>
              <Typography variant="caption" color="text.secondary">Nodes</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h5" sx={{ fontWeight: 700 }}>{edges.length}</Typography>
              <Typography variant="caption" color="text.secondary">Connections</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h5" sx={{ fontWeight: 700, color: 'success.main' }}>{onlineCount}</Typography>
              <Typography variant="caption" color="text.secondary">Online</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h5" sx={{ fontWeight: 700, color: 'error.main' }}>{offlineCount}</Typography>
              <Typography variant="caption" color="text.secondary">Offline</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Topology Canvas */}
      <Card>
        <CardContent sx={{ p: 1 }}>
          {nodes.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <TravelExplore sx={{ fontSize: 60, color: 'text.disabled', mb: 2 }} />
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                No network topology data available
              </Typography>
              <Button variant="contained" startIcon={<TravelExplore />} onClick={handleDiscover} disabled={discovering}>
                {discovering ? 'Discovering...' : 'Discover Network'}
              </Button>
            </Box>
          ) : (
            <Box sx={{ 
              position: 'relative', height: 600, bgcolor: 'background.default', 
              borderRadius: 2, overflow: 'hidden', border: '1px solid', borderColor: 'divider' 
            }}>
              <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0 }}>
                {/* Edges */}
                {edges.map(edge => {
                  const source = nodes.find(n => n.id === edge.source);
                  const target = nodes.find(n => n.id === edge.target);
                  if (!source || !target) return null;
                  return (
                    <line key={edge.id}
                      x1={source.x} y1={source.y} x2={target.x} y2={target.y}
                      stroke={getEdgeColor(edge.status)} 
                      strokeWidth={Math.max(1, Math.min((edge.request_count || 0) / 100, 4))}
                      opacity={0.6} 
                      strokeDasharray={edge.status === 'down' ? '5,5' : 'none'}
                    />
                  );
                })}
                {/* Nodes */}
                {nodes.map(node => (
                  <g key={node.id} cursor="pointer" onClick={() => handleNodeClick(node.id)}>
                    <circle 
                      cx={node.x} cy={node.y} 
                      r={Math.max(20, Math.min((node.alert_count || 0) * 2 + 15, 40))}
                      fill={getNodeColor(node.type, node.status)} 
                      opacity={0.8}
                      stroke={node.status !== 'online' ? '#ef4444' : '#fff'} 
                      strokeWidth={2} 
                    />
                    <text x={node.x} y={node.y + 4} textAnchor="middle" fill="white" fontSize={10} fontWeight={600}>
                      {node.name?.substring(0, 12) || 'N/A'}
                    </text>
                  </g>
                ))}
              </svg>
              {/* Legend */}
              <Box sx={{ 
                position: 'absolute', bottom: 10, left: 10, bgcolor: 'background.paper', 
                p: 1, borderRadius: 1, border: '1px solid', borderColor: 'divider' 
              }}>
                <Typography variant="caption" sx={{ fontWeight: 600 }}>Legend</Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 0.5 }}>
                  {['server', 'container', 'database', 'load_balancer', 'firewall'].map(type => (
                    <Chip key={type} label={type.replace('_', ' ')} size="small"
                      sx={{ bgcolor: getNodeColor(type, 'online'), color: 'white', fontSize: '0.65rem', height: 18 }} />
                  ))}
                </Box>
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Node Detail Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{selectedNode?.node?.name || 'Node Details'}</DialogTitle>
        <DialogContent>
          {selectedNode?.node ? (
            <Box>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Chip label={selectedNode.node.type || 'unknown'} size="small" />
                <Chip 
                  label={selectedNode.node.status || 'unknown'} 
                  size="small" 
                  color={selectedNode.node.status === 'online' ? 'success' : 'error'} 
                />
              </Box>
              <Grid container spacing={1}>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="text.secondary">Hostname</Typography>
                  <Typography>{selectedNode.node.hostname || 'N/A'}</Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="text.secondary">IP</Typography>
                  <Typography>{selectedNode.node.ip || 'N/A'}</Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="text.secondary">CPU</Typography>
                  <Typography>
                    {selectedNode.node.cpu_usage != null ? `${selectedNode.node.cpu_usage}%` : 'N/A'}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="body2" color="text.secondary">Risk Score</Typography>
                  <Typography color={(selectedNode.node.risk_score || 0) > 70 ? 'error.main' : 'success.main'}>
                    {selectedNode.node.risk_score || 0}
                  </Typography>
                </Grid>
              </Grid>
              {selectedNode.connections && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 0.5 }}>Outgoing Connections</Typography>
                  {(selectedNode.connections.outgoing || []).slice(0, 5).map((c: any, i: number) => (
                    <Typography key={i} variant="caption" sx={{ display: 'block' }}>
                      → {c.target} ({c.type}) - {c.status}
                    </Typography>
                  ))}
                  {selectedNode.connections.incoming && selectedNode.connections.incoming.length > 0 && (
                    <>
                      <Typography variant="subtitle2" sx={{ mt: 1, mb: 0.5 }}>Incoming Connections</Typography>
                      {(selectedNode.connections.incoming || []).slice(0, 5).map((c: any, i: number) => (
                        <Typography key={i} variant="caption" sx={{ display: 'block' }}>
                          ← {c.source} ({c.type}) - {c.status}
                        </Typography>
                      ))}
                    </>
                  )}
                </Box>
              )}
            </Box>
          ) : (
            <Typography color="text.secondary">No node data available</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};