export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  organization: Organization | null;
  role: 'admin' | 'analyst' | 'viewer';
  is_agent: boolean;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

// Agent Types
export type AgentStatus = 'online' | 'offline' | 'degraded' | 'error';
export type AgentType = 'linux' | 'docker' | 'kubernetes' | 'custom';

export interface Agent {
  id: string;
  agent_id: string;
  name: string;
  hostname: string;
  version: string;
  agent_type: AgentType;
  status: AgentStatus;
  is_online: boolean;
  uptime: number;
  os_info: Record<string, any>;
  ip_address: string | null;
  mac_address: string | null;
  cpu_usage: number | null;
  memory_usage: number | null;
  disk_usage: number | null;
  last_heartbeat: string | null;
  missed_heartbeats: number;
  total_logs_collected: number;
  total_events_generated: number;
  total_alerts_triggered: number;
  monitored_logs: string[];
  tags: string[];
  error_count: number;
  last_error_time: string | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface AgentRegistration {
  name: string;
  hostname: string;
  version: string;
  agent_type?: string;
  os_info?: Record<string, any>;
  ip_address?: string;
  monitored_logs?: string[];
  tags?: string[];
}

export interface AgentHeartbeat {
  id: string;
  agent: string;
  timestamp: string;
  cpu_usage: number | null;
  memory_usage: number | null;
  disk_usage: number | null;
  process_count: number | null;
  network_io: Record<string, any> | null;
}

// Event Types
export type EventSeverity = 'info' | 'low' | 'medium' | 'high' | 'critical';
export type EventCategory = 'authentication' | 'authorization' | 'network' | 'system' | 'application' | 'container' | 'security' | 'compliance';

export interface Event {
  id: string;
  raw_log: string | null;
  agent: string;
  agent_name?: string;
  agent_hostname?: string;
  timestamp: string;
  event_type: string;
  category: EventCategory;
  severity: EventSeverity;
  confidence: number;
  source: string;
  service: string | null;
  source_ip: string | null;
  source_port: number | null;
  source_hostname: string | null;
  target_ip: string | null;
  target_port: number | null;
  target_hostname: string | null;
  username: string | null;
  user_id: string | null;
  message: string;
  description: string | null;
  metadata: Record<string, any>;
  tags: string[];
  correlation_id: string | null;
  is_analyzed: boolean;
  created_at: string;
}


export interface EventFilters {
  severity?: string;
  event_type?: string;
  source?: string;
  source_ip?: string;
  hostname?: string;
  username?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
}

// Alert Types
export type AlertStatus = 'open' | 'acknowledged' | 'investigating' | 'resolved' | 'closed' | 'false_positive';
export type AlertSeverity = 'info' | 'low' | 'medium' | 'high' | 'critical';

export interface Alert {
  id: string;
  title: string;
  description: string;
  severity: AlertSeverity;
  status: AlertStatus;
  source: string;
  category: string;
  organization: string;
  assigned_to: string | null;
  assigned_to_name?: string;
  related_events: string[];
  related_rule: string | null;
  metadata: Record<string, any>;
  tags: string[];
  resolution: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  closed_at: string | null;
  sla_deadline: string | null;
  is_overdue: boolean;
  events_count?: number;
  comments_count?: number;
  created_at: string;
  updated_at: string;
}

// Incident Types
export type IncidentStatus = 'new' | 'triaging' | 'investigating' | 'containment' | 'eradication' | 'recovery' | 'resolved' | 'closed' | 'false_positive';
export type IncidentType = 'brute_force' | 'malware' | 'data_breach' | 'ddos' | 'unauthorized_access' | 'privilege_escalation' | 'system_compromise' | 'policy_violation' | 'insider_threat' | 'phishing' | 'ransomware' | 'other';

export interface Incident {
  id: string;
  title: string;
  description: string;
  incident_type: IncidentType;
  severity: AlertSeverity;
  status: IncidentStatus;
  priority: 'p1' | 'p2' | 'p3' | 'p4';
  organization: string;
  assigned_to: string | null;
  assigned_to_name?: string;
  assigned_team: string | null;
  alerts: string[];
  events: string[];
  correlation_id: string | null;
  correlation_confidence: number;
  affected_systems: string[];
  affected_users: string[];
  impact_scope: string;
  source_ip: string | null;
  source_hostname: string | null;
  attack_vector: string | null;
  evidence: Record<string, any>;
  artifacts: string[];
  indicators_of_compromise: any[];
  detected_at: string | null;
  started_at: string | null;
  contained_at: string | null;
  eradicated_at: string | null;
  recovered_at: string | null;
  resolution: string;
  resolution_type: string | null;
  root_cause: string;
  lessons_learned: string;
  time_to_detect: number | null;
  time_to_contain: number | null;
  time_to_resolve: number | null;
  sla_deadline: string | null;
  is_overdue: boolean;
  is_critical: boolean;
  metadata: Record<string, any>;
  tags: string[];
  alerts_count?: number;
  events_count?: number;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  closed_at: string | null;
}

// Detection Rule Types
export type RuleType = 'threshold' | 'anomaly' | 'correlation' | 'pattern' | 'frequency' | 'sequence' | 'blacklist' | 'whitelist';
export type RuleStatus = 'active' | 'paused' | 'testing' | 'disabled';

export interface DetectionRule {
  id: string;
  name: string;
  description: string;
  rule_type: RuleType;
  conditions: Record<string, any>;
  actions: Record<string, any>;
  severity: AlertSeverity;
  category: string;
  status: RuleStatus;
  priority: number;
  cooldown_minutes: number;
  times_triggered: number;
  last_triggered: string | null;
  alerts_generated: number;
  apply_to_all_agents: boolean;
  agents: string[];
  agent_groups: string[];
  organization: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

// Dashboard Types
export interface DashboardStats {
  agents_online: number;
  agents_total: number;
  events_today: number;
  alerts_today: number;
  critical_alerts: number;
  open_incidents: number;
  security_score: number;
  avg_response_time: number;
}

export interface ChartDataPoint {
  timestamp: string;
  value: number;
}

export interface SeverityDistribution {
  severity: string;
  count: number;
}

// Notification Types
export interface Notification {
  id: string;
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  channel: string;
  trigger_type: string;
  trigger_id: string | null;
  is_read: boolean;
  created_at: string;
  action_url: string | null;
}

// Pagination Types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}