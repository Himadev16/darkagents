/**
 * DARKAGENTS Mission Control Dashboard
 * NASA-style real-time agent monitoring
 */

"use client";

import { use, useEffect, useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useDashboardStore } from "@/store/dashboardStore";
import { AgentCard } from "@/components/AgentCard";
import { CommunicationLog } from "@/components/CommunicationLog";
import { MetricsPanel } from "@/components/MetricsPanel";
import { apiClient } from "@/lib/api";
import { Rocket, Play, AlertCircle } from "lucide-react";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function DashboardPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const projectId = parseInt(resolvedParams.id);

  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");

  // Zustand store
  const {
    agents,
    communications,
    totalTokens,
    totalCost,
    overallProgress,
    updateAgentStatus,
    addCommunication,
    resetDashboard,
  } = useDashboardStore();

  // WebSocket connection
  const { isConnected } = useWebSocket({
    projectId,
    onAgentStatus: (data) => {
      updateAgentStatus(data.agent_name, {
        agent_name: data.agent_name,
        agent_display_name: data.agent_display_name,
        status: data.status,
        current_task: data.current_task,
        progress: data.progress,
        tokens_used: data.tokens_used,
        cost_usd: data.cost_usd,
        eta_seconds: data.eta_seconds,
      });
    },
    onAgentCommunication: (data) => {
      addCommunication(data);
    },
    onConnected: () => {
      setConnectionStatus("connected");
      console.log("✅ Connected to mission control");
    },
    onDisconnected: () => {
      setConnectionStatus("disconnected");
      console.log("❌ Disconnected from mission control");
    },
    onError: (error) => {
      console.error("WebSocket error:", error);
      setError("WebSocket connection error");
    },
  });

  // Update connection status
  useEffect(() => {
    if (isConnected) {
      setConnectionStatus("connected");
    }
  }, [isConnected]);

  // Start PM Agent
  const handleStartAgent = async () => {
    try {
      setIsExecuting(true);
      setError(null);

      await apiClient.executeAgent(projectId, "product_manager", {});

      console.log("🚀 PM Agent execution started");
    } catch (err: any) {
      console.error("Failed to start agent:", err);
      setError(err.message || "Failed to start agent");
    } finally {
      setIsExecuting(false);
    }
  };

  // Calculate active agents count
  const activeAgents = Object.values(agents).filter(
    (agent) => agent.status === "working" || agent.status === "reviewing"
  ).length;

  // Get PM agent specifically
  const pmAgent = agents["product_manager"] || {
    agent_name: "product_manager",
    agent_display_name: "Product Manager",
    status: "idle" as const,
    current_task: null,
    progress: 0,
    tokens_used: 0,
    cost_usd: 0,
    eta_seconds: null,
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Rocket className="w-10 h-10 text-blue-400" />
          <div>
            <h1 className="text-3xl font-bold text-white">
              DARKAGENTS Mission Control
            </h1>
            <p className="text-gray-400">
              Project #{projectId} · Real-time Agent Monitoring
            </p>
          </div>
        </div>

        {/* Connection Status */}
        <div className="flex items-center gap-2 mt-4">
          <div
            className={`w-3 h-3 rounded-full ${
              connectionStatus === "connected"
                ? "bg-green-500 animate-pulse"
                : connectionStatus === "connecting"
                ? "bg-yellow-500 animate-pulse"
                : "bg-red-500"
            }`}
          />
          <span className="text-sm text-gray-400">
            {connectionStatus === "connected" && "Connected to WebSocket"}
            {connectionStatus === "connecting" && "Connecting..."}
            {connectionStatus === "disconnected" && "Disconnected - Reconnecting..."}
          </span>
        </div>
      </div>

      {/* Metrics Panel */}
      <div className="mb-6">
        <MetricsPanel
          totalTokens={totalTokens}
          totalCost={totalCost}
          overallProgress={overallProgress}
          activeAgents={activeAgents}
          totalAgents={1}
        />
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 bg-red-500/10 border border-red-500/50 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <p className="text-red-200">{error}</p>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Card (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Start Button */}
          {pmAgent.status === "idle" && (
            <button
              onClick={handleStartAgent}
              disabled={isExecuting || connectionStatus !== "connected"}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-4 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
            >
              <Play className="w-5 h-5" />
              {isExecuting ? "Starting PM Agent..." : "Start Product Manager Agent"}
            </button>
          )}

          {/* PM Agent Card */}
          <AgentCard
            agentName={pmAgent.agent_name}
            agentDisplayName={pmAgent.agent_display_name}
            status={pmAgent.status}
            currentTask={pmAgent.current_task}
            progress={pmAgent.progress}
            tokensUsed={pmAgent.tokens_used}
            costUsd={pmAgent.cost_usd}
            etaSeconds={pmAgent.eta_seconds}
          />

          {/* Instructions */}
          {pmAgent.status === "idle" && (
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-6">
              <h3 className="font-semibold text-white mb-2 flex items-center gap-2">
                <Rocket className="w-5 h-5 text-blue-400" />
                How to Use
              </h3>
              <ol className="text-gray-300 space-y-2 text-sm">
                <li>1. Click "Start Product Manager Agent" above</li>
                <li>2. Watch the agent card light up in real-time</li>
                <li>3. See progress bar move from 0% → 100%</li>
                <li>4. Monitor tokens and cost as they increment</li>
                <li>5. View agent communications in the log</li>
                <li>6. When complete, download the generated PRD</li>
              </ol>
            </div>
          )}
        </div>

        {/* Communication Log (1/3 width) */}
        <div className="lg:col-span-1">
          <CommunicationLog messages={communications} maxHeight="600px" />
        </div>
      </div>

      {/* Footer */}
      <div className="mt-8 text-center text-gray-500 text-sm">
        <p>🤖 Powered by DARKAGENTS · Using OpenRouter API</p>
        <p className="mt-1">Real-time updates via WebSocket</p>
      </div>
    </div>
  );
}
