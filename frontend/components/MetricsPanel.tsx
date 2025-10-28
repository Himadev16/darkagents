/**
 * MetricsPanel Component
 * Displays overall project metrics (total tokens, cost, progress)
 */

"use client";

import { Coins, TrendingUp, Clock, Activity } from "lucide-react";

interface MetricsPanelProps {
  totalTokens: number;
  totalCost: number;
  overallProgress: number;
  activeAgents: number;
  totalAgents?: number;
  estimatedCompletion?: string | null;
}

export function MetricsPanel({
  totalTokens,
  totalCost,
  overallProgress,
  activeAgents,
  totalAgents = 11,
  estimatedCompletion,
}: MetricsPanelProps) {
  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(4)}`;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Tokens */}
      <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-4 text-white shadow-lg">
        <div className="flex items-center justify-between mb-2">
          <Coins className="w-8 h-8 opacity-80" />
          <span className="text-2xl font-mono font-bold">
            {formatNumber(totalTokens)}
          </span>
        </div>
        <div className="text-sm opacity-90">Total Tokens Used</div>
      </div>

      {/* Total Cost */}
      <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-4 text-white shadow-lg">
        <div className="flex items-center justify-between mb-2">
          <TrendingUp className="w-8 h-8 opacity-80" />
          <span className="text-2xl font-mono font-bold">
            {formatCost(totalCost)}
          </span>
        </div>
        <div className="text-sm opacity-90">Total Cost (USD)</div>
      </div>

      {/* Overall Progress */}
      <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-4 text-white shadow-lg">
        <div className="flex items-center justify-between mb-2">
          <Activity className="w-8 h-8 opacity-80" />
          <span className="text-2xl font-mono font-bold">
            {overallProgress.toFixed(0)}%
          </span>
        </div>
        <div className="text-sm opacity-90">Overall Progress</div>
        <div className="mt-2 w-full bg-white/30 rounded-full h-1.5">
          <div
            className="bg-white h-full rounded-full transition-all duration-500"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
      </div>

      {/* Active Agents */}
      <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg p-4 text-white shadow-lg">
        <div className="flex items-center justify-between mb-2">
          <Clock className="w-8 h-8 opacity-80" />
          <span className="text-2xl font-mono font-bold">
            {activeAgents}/{totalAgents}
          </span>
        </div>
        <div className="text-sm opacity-90">Active Agents</div>
        {estimatedCompletion && (
          <div className="mt-1 text-xs opacity-75">
            ETA: {new Date(estimatedCompletion).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}
