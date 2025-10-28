/**
 * Shared TypeScript types for DARKAGENTS frontend
 */

export type AgentStatus = "idle" | "queued" | "working" | "reviewing" | "completed" | "error";

export type MessageType = "info" | "warning" | "error" | "success";

export interface AgentStatusUpdate {
  agent_name: string;
  agent_display_name: string;
  status: AgentStatus;
  current_task: string | null;
  progress: number;
  tokens_used: number;
  cost_usd: number;
  eta_seconds: number | null;
}

export interface AgentCommunication {
  from_agent: string;
  to_agent: string;
  message: string;
  message_type: MessageType;
}

export interface WebSocketMessage {
  type: "connected" | "agent_status" | "agent_communication" | "checkpoint_required" | "issue_found" | "issue_resolved" | "pong";
  project_id: number;
  timestamp: string;
  data?: any;
}

export interface Project {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  status: string;
  phase: string;
  user_idea: string;
  target_scale: string | null;
  overall_progress: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface AgentExecution {
  id: number;
  project_id: number;
  agent_name: string;
  agent_display_name: string;
  status: AgentStatus;
  current_task: string | null;
  progress: number;
  output: string | null;
  error_message: string | null;
  tokens_used: number;
  cost_usd: number;
  started_at: string | null;
  completed_at: string | null;
  estimated_completion: string | null;
  created_at: string;
}
