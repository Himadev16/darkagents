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

  // Start System Architect Agent
  const handleStartArchitectAgent = async () => {
    try {
      setIsExecuting(true);
      setError(null);

      // Get PRD from PM Agent if available
      const pmAgentData = agents["product_manager"];
      const prd = pmAgentData?.current_task || "Build a SaaS application for task management with user authentication, project creation, and team collaboration features.";

      await apiClient.executeAgent(projectId, "system_architect", {
        prd: prd,
        target_users: "Startups and small businesses",
        expected_scale: "1K-50K users"
      });

      console.log("🚀 System Architect execution started");
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

  // Start UI/UX Designer Agent
  const handleStartDesignerAgent = async () => {
    try {
      setIsExecuting(true);
      setError(null);

      // Get frontend code from Polyglot Agent if available
      const polyglotAgentData = agents["polyglot_agent"];
      const frontendCode = polyglotAgentData?.current_task || `
// Sample Next.js component to enhance
export default function Dashboard() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <button className="bg-blue-500 text-white px-4 py-2 rounded">
        Click Me
      </button>
    </div>
  );
}`;

      await apiClient.executeAgent(projectId, "ui_ux_designer", {
        frontend_code: frontendCode,
        design_style: "modern-minimalist",
        color_scheme: "professional",
        target_audience: "business professionals"
      });

      console.log("🚀 UI/UX Designer execution started");
    } catch (err: any) {
      console.error("Failed to start agent:", err);
      setError(err.message || "Failed to start agent");
    } finally {
      setIsExecuting(false);
    }
  };

  // Start QA Engineer Agent
  const handleStartQAAgent = async () => {
    try {
      setIsExecuting(true);
      setError(null);

      // Get codebase from Polyglot/Designer agents if available
      const polyglotAgentData = agents["polyglot_agent"];
      const designerAgentData = agents["ui_ux_designer"];
      const codebase = designerAgentData?.current_task || polyglotAgentData?.current_task || `
# Sample Python FastAPI code to test
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/users")
def get_users():
    return {"users": []}
`;

      await apiClient.executeAgent(projectId, "qa_engineer", {
        codebase: codebase,
        test_framework: "auto-detect",
        coverage_target: 80,
        test_types: ["unit", "integration", "e2e", "performance"]
      });

      console.log("🚀 QA Engineer execution started");
    } catch (err: any) {
      console.error("Failed to start agent:", err);
      setError(err.message || "Failed to start agent");
    } finally {
      setIsExecuting(false);
    }
  };

  // Start Security Specialist Agent
  const handleStartSecurityAgent = async () => {
    try {
      setIsExecuting(true);
      setError(null);

      // Get codebase from all previous agents
      const polyglotAgentData = agents["polyglot_agent"];
      const designerAgentData = agents["ui_ux_designer"];
      const qaAgentData = agents["qa_engineer"];
      const codebase = qaAgentData?.current_task || designerAgentData?.current_task || polyglotAgentData?.current_task || `
# Sample code to audit
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/users")
def get_users():
    return {"users": []}
`;

      await apiClient.executeAgent(projectId, "security_specialist", {
        codebase: codebase,
        compliance_standards: ["GDPR", "OWASP", "SOC2"],
        scan_depth: "comprehensive",
        include_penetration_tests: true
      });

      console.log("🚀 Security Specialist execution started");
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

  // Get System Architect agent specifically
  const architectAgent = agents["system_architect"] || {
    agent_name: "system_architect",
    agent_display_name: "System Architect",
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

  // Get UI/UX Designer agent specifically
  const designerAgent = agents["ui_ux_designer"] || {
    agent_name: "ui_ux_designer",
    agent_display_name: "UI/UX Designer",
    status: "idle" as const,
    current_task: null,
    progress: 0,
    tokens_used: 0,
    cost_usd: 0,
    eta_seconds: null,
  };

  // Get QA Engineer agent specifically
  const qaAgent = agents["qa_engineer"] || {
    agent_name: "qa_engineer",
    agent_display_name: "QA Engineer",
    status: "idle" as const,
    current_task: null,
    progress: 0,
    tokens_used: 0,
    cost_usd: 0,
    eta_seconds: null,
  };

  // Get Security Specialist agent specifically
  const securityAgent = agents["security_specialist"] || {
    agent_name: "security_specialist",
    agent_display_name: "Security Specialist",
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
          totalAgents={6}
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
              Agent 01: Product Manager
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

          {/* System Architect Agent Section */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-2xl">🏗️</span>
              Agent 02: System Architect
            </h2>
            {architectAgent.status === "idle" && (
              <button
                onClick={handleStartArchitectAgent}
                disabled={isExecuting || connectionStatus !== "connected"}
                className="w-full bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
              >
                <Play className="w-5 h-5" />
                {isExecuting ? "Starting..." : "Design System Architecture"}
              </button>
            )}
            <AgentCard
              agentName={architectAgent.agent_name}
              agentDisplayName={architectAgent.agent_display_name}
              status={architectAgent.status}
              currentTask={architectAgent.current_task}
              progress={architectAgent.progress}
              tokensUsed={architectAgent.tokens_used}
              costUsd={architectAgent.cost_usd}
              etaSeconds={architectAgent.eta_seconds}
            />
          </div>

          {/* Polyglot Agent Section */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-2xl">💎</span>
              Agent 03: Polyglot Developer
            </h2>
            {polyglotAgent.status === "idle" && (
              <button
                onClick={() => handleStartPolyglotAgent("code_generation")}
                disabled={isExecuting || connectionStatus !== "connected"}
                className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
              >
                <Play className="w-5 h-5" />
                {isExecuting ? "Starting..." : "Generate Full-Stack Code"}
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

          {/* UI/UX Designer Agent Section */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-2xl">🎨</span>
              Agent 04: UI/UX Designer
            </h2>
            {designerAgent.status === "idle" && (
              <button
                onClick={handleStartDesignerAgent}
                disabled={isExecuting || connectionStatus !== "connected"}
                className="w-full bg-gradient-to-r from-pink-600 to-rose-700 hover:from-pink-700 hover:to-rose-800 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
              >
                <Play className="w-5 h-5" />
                {isExecuting ? "Starting..." : "Polish UI Design"}
              </button>
            )}
            <AgentCard
              agentName={designerAgent.agent_name}
              agentDisplayName={designerAgent.agent_display_name}
              status={designerAgent.status}
              currentTask={designerAgent.current_task}
              progress={designerAgent.progress}
              tokensUsed={designerAgent.tokens_used}
              costUsd={designerAgent.cost_usd}
              etaSeconds={designerAgent.eta_seconds}
            />
          </div>

          {/* QA Engineer Agent Section */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-2xl">🧪</span>
              Agent 05: QA Engineer
            </h2>
            {qaAgent.status === "idle" && (
              <button
                onClick={handleStartQAAgent}
                disabled={isExecuting || connectionStatus !== "connected"}
                className="w-full bg-gradient-to-r from-amber-600 to-orange-700 hover:from-amber-700 hover:to-orange-800 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
              >
                <Play className="w-5 h-5" />
                {isExecuting ? "Starting..." : "Generate Tests & Find Bugs"}
              </button>
            )}
            <AgentCard
              agentName={qaAgent.agent_name}
              agentDisplayName={qaAgent.agent_display_name}
              status={qaAgent.status}
              currentTask={qaAgent.current_task}
              progress={qaAgent.progress}
              tokensUsed={qaAgent.tokens_used}
              costUsd={qaAgent.cost_usd}
              etaSeconds={qaAgent.eta_seconds}
            />
          </div>

          {/* Security Specialist Agent Section */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="text-2xl">🔒</span>
              Agent 06: Security Specialist
            </h2>
            {securityAgent.status === "idle" && (
              <button
                onClick={handleStartSecurityAgent}
                disabled={isExecuting || connectionStatus !== "connected"}
                className="w-full bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-700 hover:to-rose-800 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
              >
                <Play className="w-5 h-5" />
                {isExecuting ? "Starting..." : "Security Audit & Compliance Check"}
              </button>
            )}
            <AgentCard
              agentName={securityAgent.agent_name}
              agentDisplayName={securityAgent.agent_display_name}
              status={securityAgent.status}
              currentTask={securityAgent.current_task}
              progress={securityAgent.progress}
              tokensUsed={securityAgent.tokens_used}
              costUsd={securityAgent.cost_usd}
              etaSeconds={securityAgent.eta_seconds}
            />
          </div>

          {/* Instructions */}
          {pmAgent.status === "idle" && architectAgent.status === "idle" && polyglotAgent.status === "idle" && designerAgent.status === "idle" && qaAgent.status === "idle" && securityAgent.status === "idle" && (
            <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-lg p-6">
              <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
                <Rocket className="w-5 h-5 text-blue-400" />
                How to Use DARKAGENTS - Your AI Product Factory
              </h3>
              <div className="text-gray-300 space-y-3 text-sm">
                <div>
                  <p className="font-semibold text-blue-400">Agent 01: Product Manager</p>
                  <p>Transforms ideas into comprehensive Product Requirements Documents (PRD) with user personas, stories, success metrics, and competitive analysis</p>
                </div>
                <div>
                  <p className="font-semibold text-emerald-400">Agent 02: System Architect</p>
                  <p>Senior technical architect that designs complete system architecture including database schema, API specs, tech stack, security architecture, and cost estimates</p>
                </div>
                <div>
                  <p className="font-semibold text-purple-400">Agent 03: Polyglot Developer</p>
                  <p>Elite multi-language coder supporting 20+ languages. Generates production-ready full-stack code, reviews, debugs, refactors, tests, optimizes, and translates between languages</p>
                </div>
                <div>
                  <p className="font-semibold text-pink-400">Agent 04: UI/UX Designer</p>
                  <p>Senior product designer that polishes frontend code with professional UI design, animations, accessibility (WCAG 2.1 AA), and modern design patterns using Tailwind CSS</p>
                </div>
                <div>
                  <p className="font-semibold text-amber-400">Agent 05: QA Engineer</p>
                  <p>Senior QA engineer that generates comprehensive test suite (unit, integration, E2E, performance) and identifies bugs with severity levels and reproduction steps</p>
                </div>
                <div>
                  <p className="font-semibold text-red-400">Agent 06: Security Specialist</p>
                  <p>Senior security engineer that performs OWASP Top 10 vulnerability scan, compliance checking (GDPR, SOC2, HIPAA), and generates security audit with fix recommendations</p>
                </div>
                <div className="mt-4 p-3 bg-gray-800/50 rounded">
                  <p className="font-semibold text-white mb-1">Workflow (Sequential):</p>
                  <ol className="space-y-1 ml-4 list-decimal">
                    <li>Start PM Agent → Get PRD</li>
                    <li>Start Architect Agent → Get System Design</li>
                    <li>Start Polyglot Agent → Get Production Code</li>
                    <li>Start Designer Agent → Get Polished UI</li>
                    <li>Start QA Agent → Get Tests & Bug Reports</li>
                    <li>Start Security Agent → Get Security Audit</li>
                    <li>Watch real-time progress in agent cards</li>
                    <li>Monitor tokens, costs, and communications</li>
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
