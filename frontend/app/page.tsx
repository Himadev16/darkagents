/**
 * DARKAGENTS Home Page
 */

import Link from "next/link";
import { Rocket, Zap, Users, Shield } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-6">
      <div className="max-w-4xl mx-auto text-center">
        {/* Logo/Icon */}
        <div className="mb-8">
          <Rocket className="w-20 h-20 text-blue-400 mx-auto mb-4" />
          <h1 className="text-6xl font-bold text-white mb-4">
            DARKAGENTS
          </h1>
          <p className="text-xl text-gray-400">
            Enterprise SaaS Platform Builder
          </p>
          <p className="text-lg text-gray-500 mt-2">
            AI-Powered Development Team in Your Browser
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
            <Zap className="w-12 h-12 text-yellow-400 mx-auto mb-3" />
            <h3 className="text-white font-semibold mb-2">Real-Time Monitoring</h3>
            <p className="text-gray-400 text-sm">
              Watch AI agents work in real-time with NASA-style mission control
            </p>
          </div>

          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
            <Users className="w-12 h-12 text-green-400 mx-auto mb-3" />
            <h3 className="text-white font-semibold mb-2">11 Specialized Agents</h3>
            <p className="text-gray-400 text-sm">
              PM, Architect, Developers, QA, Security, DevOps, and more
            </p>
          </div>

          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
            <Shield className="w-12 h-12 text-purple-400 mx-auto mb-3" />
            <h3 className="text-white font-semibold mb-2">Production-Ready</h3>
            <p className="text-gray-400 text-sm">
              Complete SaaS applications with code, docs, and infrastructure
            </p>
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
          <Link
            href="/projects/1/dashboard"
            className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold py-4 px-8 rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
          >
            <Rocket className="w-5 h-5" />
            View Dashboard Demo
          </Link>
        </div>

        {/* Status */}
        <div className="text-gray-500 text-sm">
          <p>🚀 Phase 1 MVP - Product Manager Agent Functional</p>
          <p className="mt-2">Backend: FastAPI + OpenRouter API</p>
          <p>Frontend: Next.js 14 + WebSocket</p>
        </div>

        {/* Footer */}
        <div className="mt-12 text-gray-600 text-xs">
          <p>🤖 Built with Claude Code</p>
          <p className="mt-1">
            Using OpenRouter API for Claude Sonnet 4.5 access
          </p>
        </div>
      </div>
    </div>
  );
}
