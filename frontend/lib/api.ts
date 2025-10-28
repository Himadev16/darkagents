/**
 * API Client for DARKAGENTS Backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class APIClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("darkagents_token", token);
    }
  }

  getToken(): string | null {
    if (!this.token && typeof window !== "undefined") {
      this.token = localStorage.getItem("darkagents_token");
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("darkagents_token");
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    // Add any existing headers
    if (options.headers) {
      Object.entries(options.headers).forEach(([key, value]) => {
        headers[key] = String(value);
      });
    }

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "API request failed");
    }

    return response.json();
  }

  // Auth endpoints
  async register(email: string, password: string, fullName?: string) {
    return this.request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  }

  async login(email: string, password: string) {
    const response: any = await this.request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username: email, password }),
    });
    this.setToken(response.access_token);
    return response;
  }

  async getCurrentUser() {
    return this.request("/api/auth/me");
  }

  // Project endpoints
  async createProject(data: {
    name: string;
    description?: string;
    user_idea: string;
    target_scale?: string;
  }) {
    return this.request("/api/projects", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getProjects() {
    return this.request("/api/projects");
  }

  async getProject(id: number) {
    return this.request(`/api/projects/${id}`);
  }

  async updateProject(id: number, data: any) {
    return this.request(`/api/projects/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteProject(id: number) {
    return this.request(`/api/projects/${id}`, {
      method: "DELETE",
    });
  }

  // Agent endpoints
  async executeAgent(projectId: number, agentName: string, inputData: any = {}) {
    return this.request("/api/agents/execute", {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        agent_name: agentName,
        input_data: inputData,
      }),
    });
  }

  async getAvailableAgents() {
    return this.request("/api/agents/available");
  }

  // WebSocket URL
  getWebSocketURL(projectId: number): string {
    const wsProtocol = this.baseURL.startsWith("https") ? "wss" : "ws";
    const wsBaseURL = this.baseURL.replace(/^https?:\/\//, "");
    return `${wsProtocol}://${wsBaseURL}/ws/${projectId}`;
  }
}

export const apiClient = new APIClient(API_BASE_URL);
