/**
 * AgentCard Component
 * Displays real-time agent status with progress bar, metrics, and visual indicators
 */

"use client";

import { AgentStatus } from "@/lib/types";
import { Activity, CheckCircle2, AlertCircle, Loader2, Clock } from "lucide-react";

interface AgentCardProps {
  agentName: string;
  agentDisplayName: string;
  status: AgentStatus;
  currentTask: string | null;
  progress: number;
  tokensUsed: number;
  costUsd: number;
  etaSeconds: number | null;
}

export function AgentCard({
  agentName,
  agentDisplayName,
  status,
  currentTask,
  progress,
  tokensUsed,
  costUsd,
  etaSeconds,
}: AgentCardProps) {
  // Status indicator colors and icons
  const getStatusConfig = (status: AgentStatus) => {
    switch (status) {
      case "working":
        return {
          color: "bg-green-500",
          icon: <Loader2 className="w-4 h-4 animate-spin" />,
          label: "WORKING",
          bgColor: "bg-green-500/10",
          borderColor: "border-green-500/50",
        };
      case "completed":
        return {
          color: "bg-green-600",
          icon: <CheckCircle2 className="w-4 h-4" />,
          label: "COMPLETED",
          bgColor: "bg-green-500/10",
          borderColor: "border-green-500/50",
        };
      case "error":
        return {
          color: "bg-red-500",
          icon: <AlertCircle className="w-4 h-4" />,
          label: "ERROR",
          bgColor: "bg-red-500/10",
          borderColor: "border-red-500/50",
        };
      case "queued":
        return {
          color: "bg-yellow-500",
          icon: <Clock className="w-4 h-4" />,
          label: "QUEUED",
          bgColor: "bg-yellow-500/10",
          borderColor: "border-yellow-500/50",
        };
      case "reviewing":
        return {
          color: "bg-blue-500",
          icon: <Activity className="w-4 h-4" />,
          label: "REVIEWING",
          bgColor: "bg-blue-500/10",
          borderColor: "border-blue-500/50",
        };
      default:
        return {
          color: "bg-gray-500",
          icon: <Activity className="w-4 h-4" />,
          label: "IDLE",
          bgColor: "bg-gray-500/10",
          borderColor: "border-gray-500/30",
        };
    }
  };

  const statusConfig = getStatusConfig(status);

  // Format ETA
  const formatETA = (seconds: number | null) => {
    if (!seconds) return "--";
    if (seconds < 60) return `${Math.round(seconds)}s`;
    return `${Math.round(seconds / 60)}m`;
  };

  return (
    <div
      className={`relative border-2 ${statusConfig.borderColor} ${statusConfig.bgColor} rounded-lg p-4 transition-all duration-300 hover:shadow-lg`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <div className={`w-3 h-3 rounded-full ${statusConfig.color} animate-pulse`} />
            <h3 className="font-semibold text-lg text-gray-900 dark:text-white">
              {agentDisplayName}
            </h3>
          </div>
          <div className="flex items-center gap-2 text-xs">
            {statusConfig.icon}
            <span className={`font-medium ${status === "working" ? "text-green-600" : "text-gray-600"} dark:text-gray-400`}>
              {statusConfig.label}
            </span>
          </div>
        </div>
      </div>

      {/* Current Task */}
      {currentTask && (
        <div className="mb-3">
          <p className="text-sm text-gray-700 dark:text-gray-300 italic">
            {currentTask}
          </p>
        </div>
      )}

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
          <span>Progress</span>
          <span className="font-mono font-semibold">{progress.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ease-out ${
              status === "working" ? "bg-green-500" : "bg-gray-400"
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-2">
        {/* Tokens */}
        <div className="bg-white/50 dark:bg-gray-800/50 rounded px-2 py-1.5">
          <div className="text-xs text-gray-500 dark:text-gray-400">Tokens</div>
          <div className="text-sm font-mono font-semibold text-gray-900 dark:text-white">
            {tokensUsed.toLocaleString()}
          </div>
        </div>

        {/* Cost */}
        <div className="bg-white/50 dark:bg-gray-800/50 rounded px-2 py-1.5">
          <div className="text-xs text-gray-500 dark:text-gray-400">Cost</div>
          <div className="text-sm font-mono font-semibold text-gray-900 dark:text-white">
            ${costUsd.toFixed(3)}
          </div>
        </div>

        {/* ETA */}
        <div className="bg-white/50 dark:bg-gray-800/50 rounded px-2 py-1.5">
          <div className="text-xs text-gray-500 dark:text-gray-400">ETA</div>
          <div className="text-sm font-mono font-semibold text-gray-900 dark:text-white">
            {formatETA(etaSeconds)}
          </div>
        </div>
      </div>
    </div>
  );
}
