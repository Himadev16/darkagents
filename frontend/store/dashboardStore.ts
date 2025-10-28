/**
 * Dashboard Store (Zustand)
 * Manages real-time agent status and communications
 */

import { create } from "zustand";
import { AgentStatus, AgentCommunication } from "@/lib/types";

interface AgentState {
  agent_name: string;
  agent_display_name: string;
  status: AgentStatus;
  current_task: string | null;
  progress: number;
  tokens_used: number;
  cost_usd: number;
  eta_seconds: number | null;
}

interface DashboardState {
  // Agents
  agents: Record<string, AgentState>;

  // Communications
  communications: AgentCommunication[];

  // Overall metrics
  totalTokens: number;
  totalCost: number;
  overallProgress: number;

  // Actions
  updateAgentStatus: (agentName: string, update: Partial<AgentState>) => void;
  addCommunication: (communication: AgentCommunication) => void;
  clearCommunications: () => void;
  resetDashboard: () => void;
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  // Initial state
  agents: {},
  communications: [],
  totalTokens: 0,
  totalCost: 0,
  overallProgress: 0,

  // Update agent status
  updateAgentStatus: (agentName, update) => {
    set((state) => {
      const updatedAgent = {
        ...(state.agents[agentName] || {
          agent_name: agentName,
          agent_display_name: update.agent_display_name || agentName,
          status: "idle" as AgentStatus,
          current_task: null,
          progress: 0,
          tokens_used: 0,
          cost_usd: 0,
          eta_seconds: null,
        }),
        ...update,
      };

      const newAgents = {
        ...state.agents,
        [agentName]: updatedAgent,
      };

      // Recalculate totals
      const totalTokens = Object.values(newAgents).reduce(
        (sum, agent) => sum + agent.tokens_used,
        0
      );
      const totalCost = Object.values(newAgents).reduce(
        (sum, agent) => sum + agent.cost_usd,
        0
      );

      // Calculate overall progress (average of all agents)
      const agentCount = Object.keys(newAgents).length;
      const overallProgress = agentCount > 0
        ? Object.values(newAgents).reduce((sum, agent) => sum + agent.progress, 0) / agentCount
        : 0;

      return {
        agents: newAgents,
        totalTokens,
        totalCost,
        overallProgress,
      };
    });
  },

  // Add communication message
  addCommunication: (communication) => {
    set((state) => ({
      communications: [...state.communications, communication],
    }));
  },

  // Clear all communications
  clearCommunications: () => {
    set({ communications: [] });
  },

  // Reset entire dashboard
  resetDashboard: () => {
    set({
      agents: {},
      communications: [],
      totalTokens: 0,
      totalCost: 0,
      overallProgress: 0,
    });
  },
}));
