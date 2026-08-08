/** Tipos compartilhados espelhando os schemas do backend. */

export interface User {
  id: number;
  email: string;
  name: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  last_login_at?: string | null;
}

export interface ApiKey {
  id: number;
  name: string;
  key_prefix: string;
  is_active: boolean;
  created_at: string;
  last_used_at?: string | null;
  last_used_ip?: string | null;
  request_count: number;
}

export interface ApiKeyCreated extends ApiKey {
  key: string;
}

export interface OllamaModel {
  name: string;
  size?: number;
  modified_at?: string;
  details?: { family?: string; parameter_size?: string; quantization_level?: string };
}

export interface ModelsResponse {
  default_model: string;
  models: OllamaModel[];
  running: { name: string; size_vram?: number }[];
  online: boolean;
}

export interface SystemStats {
  cpu_percent: number;
  memory_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
}

export interface HealthStatus {
  api: string;
  database: string;
  ollama: string;
  version: string;
  platform_name: string;
}

export interface DashboardStats {
  total_users: number;
  total_api_keys: number;
  total_requests: number;
  requests_today: number;
  requests_month: number;
  avg_duration_ms: number;
  total_tokens: number;
  models_available: number;
  system: SystemStats;
  health: HealthStatus;
  daily_usage: { date: string; requests: number; tokens: number }[];
  top_models: { model: string; requests: number }[];
}

export interface RequestLog {
  id: number;
  user_id?: number | null;
  endpoint: string;
  model?: string | null;
  status_code: number;
  duration_ms: number;
  total_tokens: number;
  ip_address?: string | null;
  error?: string | null;
  created_at: string;
}

export interface Conversation {
  id: number;
  title: string;
  model?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: { id: number; role: string; content: string; created_at: string }[];
}
