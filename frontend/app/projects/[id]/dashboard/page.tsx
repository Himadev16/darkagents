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
  const handleStartPMAgent = async () => {
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

  // Start Polyglot Agent
  const handleStartPolyglotAgent = async (taskType: string = "code_generation") => {
    try {
      setIsExecuting(true);
      setError(null);

      await apiClient.executeAgent(projectId, "polyglot_agent", {
        task_type: taskType,
        language: "python",
        requirements: "Create a FastAPI REST API with JWT authentication, user CRUD operations, and PostgreSQL database integration using SQLAlchemy 2.0."
      });

      console.log("🚀 Polyglot Agent execution started");
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

  // Get Polyglot agent specifically
  const polyglotAgent = agents["polyglot_agent"] || {
    agent_name: "polyglot_agent",
    agent_display_name: "Polyglot Agent",
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
          totalAgents={2}
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
        {/* Agent Cards (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Product Manager Agent Section */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Rocket className="w-6 h-6 text-blue-400" />
              Product Manager Agent
            </h2>
            {pmAgent.status === "idle" && (
              <button
                onClick={handleStartPMAgent}
                disabled={isExecuting || connectionStatus !== "connected"}
                className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
              >
                <Play className="w-5 h-5" />
                {isExecuting ? "Starting..." : "Start PM Agent"}
              </button>
            )}
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
          </div>

          {/* Polyglot Agent Section */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-2xl">💎</span>
              Polyglot Agent - Elite Multi-Language Coding AI
            </h2>
            {polyglotAgent.status === "idle" && (
              <button
                onClick={() => handleStartPolyglotAgent("code_generation")}
                disabled={isExecuting || connectionStatus !== "connected"}
                className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
              >
                <Play className="w-5 h-5" />
                {isExecuting ? "Starting..." : "Generate Python FastAPI Code"}
              </button>
            )}
            <AgentCard
              agentName={polyglotAgent.agent_name}
              agentDisplayName={polyglotAgent.agent_display_name}
              status={polyglotAgent.status}
              currentTask={polyglotAgent.current_task}
              progress={polyglotAgent.progress}
              tokensUsed={polyglotAgent.tokens_used}
              costUsd={polyglotAgent.cost_usd}
              etaSeconds={polyglotAgent.eta_seconds}
            />
          </div>

          {/* Instructions */}
          {pmAgent.status === "idle" && polyglotAgent.status === "idle" && (
            <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-lg p-6">
              <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
                <Rocket className="w-5 h-5 text-blue-400" />
                How to Use DARKAGENTS
              </h3>
              <div className="text-gray-300 space-y-3 text-sm">
                <div>
                  <p className="font-semibold text-blue-400">Product Manager Agent:</p>
                  <p>Analyzes ideas and creates comprehensive Product Requirements Documents</p>
                </div>
                <div>
                  <p className="font-semibold text-purple-400">Polyglot Agent:</p>
                  <p>Elite multi-language coder supporting 20+ languages. Generates production-ready code, reviews, debugs, refactors, tests, optimizes, and translates code between languages.</p>
                </div>
                <div className="mt-4 p-3 bg-gray-800/50 rounded">
                  <p className="font-semibold text-white mb-1">Real-time Monitoring:</p>
                  <ol className="space-y-1 ml-4 list-decimal">
                    <li>Click any "Start" button above</li>
                    <li>Watch agent cards light up in real-time</li>
                    <li>Monitor progress bars, tokens, and costs</li>
                    <li>View communications in the right panel</li>
                  </ol>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Communication Log (1/3 width) */}
        <div className="lg:col-span-1">
          <CommunicationLog messages={communications} maxHeight="800px" />
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
