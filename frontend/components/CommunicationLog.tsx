/**
 * CommunicationLog Component
 * Displays scrolling feed of inter-agent communications
 */

"use client";

import { useEffect, useRef } from "react";
import { AgentCommunication } from "@/lib/types";
import { MessageSquare, AlertTriangle, Info, CheckCircle } from "lucide-react";

interface CommunicationLogProps {
  messages: AgentCommunication[];
  maxHeight?: string;
}

export function CommunicationLog({
  messages,
  maxHeight = "400px",
}: CommunicationLogProps) {
  const logEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const getMessageIcon = (type: string) => {
    switch (type) {
      case "error":
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case "success":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      default:
        return <Info className="w-4 h-4 text-blue-500" />;
    }
  };

  const getMessageColor = (type: string) => {
    switch (type) {
      case "error":
        return "border-l-red-500 bg-red-50 dark:bg-red-900/20";
      case "warning":
        return "border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/20";
      case "success":
        return "border-l-green-500 bg-green-50 dark:bg-green-900/20";
      default:
        return "border-l-blue-500 bg-blue-50 dark:bg-blue-900/20";
    }
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return new Date().toLocaleTimeString();
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-700">
      {/* Header */}
      <div className="border-b border-gray-700 px-4 py-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-blue-400" />
          <h3 className="font-semibold text-white">Communication Log</h3>
          <span className="ml-auto text-xs text-gray-400">
            {messages.length} messages
          </span>
        </div>
      </div>

      {/* Messages */}
      <div
        className="overflow-y-auto p-4 space-y-2 font-mono text-sm"
        style={{ maxHeight }}
      >
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No messages yet...</p>
            <p className="text-xs mt-1">
              Agent communications will appear here in real-time
            </p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`border-l-4 ${getMessageColor(msg.message_type)} rounded-r p-3 transition-all duration-200 hover:shadow-md`}
            >
              <div className="flex items-start gap-2">
                {getMessageIcon(msg.message_type)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold text-gray-600 dark:text-gray-300">
                      {msg.from_agent}
                    </span>
                    <span className="text-gray-400">→</span>
                    <span className="text-xs font-semibold text-gray-600 dark:text-gray-300">
                      {msg.to_agent}
                    </span>
                    <span className="ml-auto text-xs text-gray-400">
                      {formatTimestamp()}
                    </span>
                  </div>
                  <p className="text-gray-700 dark:text-gray-200 text-xs break-words">
                    {msg.message}
                  </p>
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}
