/**
 * useWebSocket Hook
 * Manages WebSocket connection for real-time agent updates
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { WebSocketMessage, AgentStatusUpdate, AgentCommunication } from "@/lib/types";

interface UseWebSocketOptions {
  projectId: number;
  onAgentStatus?: (data: AgentStatusUpdate) => void;
  onAgentCommunication?: (data: AgentCommunication) => void;
  onCheckpointRequired?: (data: any) => void;
  onIssueFound?: (data: any) => void;
  onIssueResolved?: (data: any) => void;
  onConnected?: () => void;
  onDisconnected?: () => void;
  onError?: (error: Event) => void;
}

export function useWebSocket(options: UseWebSocketOptions) {
  const {
    projectId,
    onAgentStatus,
    onAgentCommunication,
    onCheckpointRequired,
    onIssueFound,
    onIssueResolved,
    onConnected,
    onDisconnected,
    onError,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const getWebSocketURL = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, "") || "localhost:8000";
    return `${protocol}//${host}/ws/${projectId}`;
  }, [projectId]);

  const connect = useCallback(() => {
    try {
      const wsURL = getWebSocketURL();
      console.log("🔌 Connecting to WebSocket:", wsURL);

      const ws = new WebSocket(wsURL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("✅ WebSocket connected");
        setIsConnected(true);
        onConnected?.();

        // Start heartbeat
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send("ping");
          }
        }, 30000); // Ping every 30 seconds
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          console.log("📨 WebSocket message:", message.type, message.data);

          // Route message to appropriate handler
          switch (message.type) {
            case "connected":
              console.log("🎉 Connected to DARKAGENTS mission control");
              break;

            case "agent_status":
              onAgentStatus?.(message.data as AgentStatusUpdate);
              break;

            case "agent_communication":
              onAgentCommunication?.(message.data as AgentCommunication);
              break;

            case "checkpoint_required":
              onCheckpointRequired?.(message.data);
              break;

            case "issue_found":
              onIssueFound?.(message.data);
              break;

            case "issue_resolved":
              onIssueResolved?.(message.data);
              break;

            case "pong":
              // Heartbeat response
              break;

            default:
              console.log("Unknown message type:", message.type);
          }
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      ws.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
        onError?.(error);
      };

      ws.onclose = () => {
        console.log("🔌 WebSocket disconnected");
        setIsConnected(false);
        onDisconnected?.();

        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }

        // Attempt reconnection after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log("🔄 Attempting to reconnect...");
          connect();
        }, 5000);
      };
    } catch (error) {
      console.error("Failed to create WebSocket connection:", error);
    }
  }, [
    getWebSocketURL,
    onAgentStatus,
    onAgentCommunication,
    onCheckpointRequired,
    onIssueFound,
    onIssueResolved,
    onConnected,
    onDisconnected,
    onError,
  ]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
    } else {
      console.warn("WebSocket is not connected");
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: connect,
  };
}
